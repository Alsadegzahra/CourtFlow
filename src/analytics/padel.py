"""
Padel-specific analytics layer.
Metrics: rally length, wall usage, shot speeds, per-player stats (shots, speed, movement).
Works with player tracks only for now; ball_shot_frames and bounce_events can be plugged in later
to fill rally/shot/wall metrics.
Uses: movement metrics, court dimensions (constants), pandas/numpy for time-series stats.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.config.constants import COURT_HEIGHT_M, COURT_WIDTH_M


def _court_point(t: dict) -> Optional[Tuple[float, float]]:
    x, y = t.get("x_court"), t.get("y_court")
    if x is None or y is None:
        return None
    return (float(x), float(y))


def _distance_m(p1: Tuple[float, float], p2: Tuple[float, float], court_width_m: float = COURT_WIDTH_M, court_height_m: float = COURT_HEIGHT_M) -> float:
    """Euclidean distance in court space scaled to meters (court 0–1 → court_width_m x court_height_m)."""
    dx = (p2[0] - p1[0]) * court_width_m
    dy = (p2[1] - p1[1]) * court_height_m
    return (dx * dx + dy * dy) ** 0.5


class PadelAnalytics:
    """
    Padel-specific performance metrics.
    Today: works with player tracks only (movement, speed). Rally/shot/wall metrics
    are stubbed until ball_shot_frames and bounce_events are available.
    """

    def __init__(
        self,
        court_width_m: float = COURT_WIDTH_M,
        court_height_m: float = COURT_HEIGHT_M,
    ):
        self.court_width_m = court_width_m
        self.court_height_m = court_height_m

    def compute_rally_metrics(
        self,
        ball_shot_frames: Optional[List[int]] = None,
        ball_mini_court_detections: Optional[List[dict]] = None,
    ) -> List[dict]:
        """
        Rally length (shots per rally) and duration.
        Without ball data returns [].
        With ball_shot_frames: one rally per consecutive pair of shot frames.
        """
        if not ball_shot_frames or len(ball_shot_frames) < 2:
            return []
        rallies = []
        for i in range(len(ball_shot_frames) - 1):
            start, end = ball_shot_frames[i], ball_shot_frames[i + 1]
            duration_frames = end - start
            rallies.append({"shots": 1, "duration_frames": duration_frames})
        return rallies

    def compute_shot_speeds(
        self,
        ball_shot_frames: Optional[List[int]] = None,
        ball_mini_court_detections: Optional[List[dict]] = None,
        fps: float = 24,
    ) -> List[dict]:
        """
        Ball speed (km/h) between shot frames.
        Without ball data returns [].
        ball_mini_court_detections[frame] should be dict like {1: (x, y)} for ball position in court coords.
        """
        if not ball_shot_frames or not ball_mini_court_detections or len(ball_shot_frames) < 2:
            return []
        speeds = []
        for i in range(len(ball_shot_frames) - 1):
            start_frame = ball_shot_frames[i]
            end_frame = ball_shot_frames[i + 1]
            if start_frame >= len(ball_mini_court_detections) or end_frame >= len(ball_mini_court_detections):
                continue
            start_det = ball_mini_court_detections[start_frame]
            end_det = ball_mini_court_detections[end_frame]
            start_pos = start_det.get(1, (0.0, 0.0)) if isinstance(start_det, dict) else (0.0, 0.0)
            end_pos = end_det.get(1, (0.0, 0.0)) if isinstance(end_det, dict) else (0.0, 0.0)
            if isinstance(start_pos, (list, tuple)) and len(start_pos) >= 2:
                start_pos = (float(start_pos[0]), float(start_pos[1]))
            if isinstance(end_pos, (list, tuple)) and len(end_pos) >= 2:
                end_pos = (float(end_pos[0]), float(end_pos[1]))
            dist_m = _distance_m(start_pos, end_pos, self.court_width_m, self.court_height_m)
            time_s = (end_frame - start_frame) / fps
            speed_kmh = (dist_m / time_s * 3.6) if time_s > 0 else 0
            speeds.append({"frame": start_frame, "speed_kmh": speed_kmh})
        return speeds

    def compute_player_stats_from_tracks(
        self,
        tracks: List[dict],
        fps: float = 30,
        player_ids: Optional[List[int]] = None,
        interval_frames: int = 30,
    ) -> List[dict]:
        """
        Per-player stats from tracks only (no ball): cumulative distance and speed over time.
        Emits one row every interval_frames (e.g. 30 = ~1s) with keys player_{id}_total_distance,
        player_{id}_total_player_speed, etc. player_ids: e.g. [1,2,3,4]; if None, use unique IDs from tracks.
        """
        if not tracks:
            return []
        by_player: Dict[int, List[dict]] = {}
        for t in tracks:
            pid = t.get("player_id")
            if pid is None:
                continue
            pt = _court_point(t)
            if pt is None:
                continue
            by_player.setdefault(int(pid), []).append(t)
        if not by_player:
            return []
        ids = sorted(by_player.keys()) if player_ids is None else player_ids
        all_frames = sorted(set(t["frame"] for t in tracks))
        if not all_frames:
            return []
        max_frame = max(all_frames)

        # Per-player cumulative distance and total speed (sum of segment speeds)
        totals: Dict[int, Dict[str, float]] = {pid: {"distance": 0.0, "speed_sum": 0.0, "n": 0} for pid in ids}
        # Sample frames at interval_frames
        sample_frames = list(range(0, max_frame + 1, interval_frames))
        if sample_frames[-1] != max_frame:
            sample_frames.append(max_frame)
        player_stats_data = []

        for frame_num in sample_frames:
            # Update totals from all track points up to this frame
            for pid in ids:
                list_t = sorted([t for t in by_player[pid] if t["frame"] <= frame_num], key=lambda x: x["frame"])
                if len(list_t) < 2:
                    continue
                dist = 0.0
                speed_sum = 0.0
                for i in range(1, len(list_t)):
                    seg_m = 0.0
                    p0 = _court_point(list_t[i - 1])
                    p1 = _court_point(list_t[i])
                    if p0 and p1:
                        seg_m = _distance_m(p0, p1, self.court_width_m, self.court_height_m)
                        dist += seg_m
                    ts_prev = list_t[i - 1].get("timestamp") or 0
                    ts_cur = list_t[i].get("timestamp") or 0
                    dt = ts_cur - ts_prev
                    if dt > 0 and seg_m > 0:
                        speed_sum += (seg_m * 3.6) / dt
                totals[pid]["distance"] = dist
                totals[pid]["speed_sum"] = speed_sum
                totals[pid]["n"] = len(list_t)
            row: Dict[str, Any] = {"frame_num": frame_num}
            for pid in ids:
                row[f"player_{pid}_number_of_shots"] = 0
                row[f"player_{pid}_total_shot_speed"] = 0.0
                row[f"player_{pid}_last_shot_speed"] = 0.0
                row[f"player_{pid}_total_distance"] = totals[pid]["distance"]
                row[f"player_{pid}_total_player_speed"] = totals[pid]["speed_sum"]
                row[f"player_{pid}_last_player_speed"] = 0.0
            player_stats_data.append(row)
        return player_stats_data

    def compute_player_stats(
        self,
        ball_shot_frames: Optional[List[int]] = None,
        player_mini_court_detections: Optional[List[dict]] = None,
        ball_mini_court_detections: Optional[List[dict]] = None,
        player_tracker: Optional[Any] = None,
        fps: float = 24,
        tracks: Optional[List[dict]] = None,
    ) -> List[dict]:
        """
        Per-player stats: with ball data use shot attribution; otherwise fall back to tracks-only.
        """
        if ball_shot_frames and player_mini_court_detections and ball_mini_court_detections and player_tracker is not None:
            return self._compute_player_stats_from_ball(
                ball_shot_frames, player_mini_court_detections,
                ball_mini_court_detections, player_tracker, fps,
            )
        if tracks:
            return self.compute_player_stats_from_tracks(tracks, fps=fps)
        return []

    def _compute_player_stats_from_ball(
        self,
        ball_shot_frames: List[int],
        player_mini_court_detections: List[dict],
        ball_mini_court_detections: List[dict],
        player_tracker: Any,
        fps: float,
    ) -> List[dict]:
        """Full implementation when ball + player positions and tracker are available."""
        player_ids = [1, 2, 3, 4]
        init_stats: Dict[str, Any] = {f"player_{i}_number_of_shots": 0 for i in player_ids}
        init_stats.update({f"player_{i}_total_shot_speed": 0.0 for i in player_ids})
        init_stats.update({f"player_{i}_last_shot_speed": 0.0 for i in player_ids})
        init_stats.update({f"player_{i}_total_player_speed": 0.0 for i in player_ids})
        init_stats.update({f"player_{i}_last_player_speed": 0.0 for i in player_ids})
        init_stats["frame_num"] = 0
        player_stats_data = [deepcopy(init_stats)]
        # Stub: would need measure_distance, convert_pixel_distance_to_meters, player_tracker.get_opponents
        # Leave as placeholder so caller can plug in when ball pipeline exists
        return player_stats_data

    def compute_wall_usage(
        self,
        bounce_events: Optional[List[dict]] = None,
    ) -> dict:
        """
        Wall bounce count and frequency.
        Without bounce_events returns stub (zeros).
        bounce_events: list of { type: "wall" | "ground", ... }.
        """
        if not bounce_events:
            return {
                "wall_bounce_count": 0,
                "ground_bounce_count": 0,
                "wall_usage_ratio": 0.0,
            }
        wall = sum(1 for b in bounce_events if b.get("type") == "wall")
        ground = sum(1 for b in bounce_events if b.get("type") == "ground")
        total = len(bounce_events)
        return {
            "wall_bounce_count": wall,
            "ground_bounce_count": ground,
            "wall_usage_ratio": wall / total if total > 0 else 0.0,
        }

    def build_stats_dataframe(
        self,
        player_stats_data: List[dict],
        num_frames: int,
        player_ids: Optional[List[int]] = None,
    ) -> "pd.DataFrame":
        """Build DataFrame with forward-fill for display. Requires pandas."""
        import pandas as pd
        if not player_stats_data:
            return pd.DataFrame()
        df = pd.DataFrame(player_stats_data)
        frames_df = pd.DataFrame({"frame_num": list(range(num_frames))})
        df = pd.merge(frames_df, df, on="frame_num", how="left")
        df = df.ffill()
        ids = player_ids or [1, 2, 3, 4]
        for pid in ids:
            shots_col = f"player_{pid}_number_of_shots"
            if shots_col in df.columns:
                total_shot = f"player_{pid}_total_shot_speed"
                if total_shot in df.columns:
                    df[f"player_{pid}_average_shot_speed"] = np.where(
                        df[shots_col] > 0,
                        df[total_shot] / df[shots_col],
                        0.0,
                    )
            total_player = f"player_{pid}_total_player_speed"
            if total_player in df.columns:
                opp1 = 3 if pid in (1, 2) else 1
                opp2 = 4 if pid in (1, 2) else 2
                c1 = f"player_{opp1}_number_of_shots"
                c2 = f"player_{opp2}_number_of_shots"
                if c1 in df.columns and c2 in df.columns:
                    total_opp = df[c1].fillna(0) + df[c2].fillna(0)
                    safe = total_opp.replace(0, np.nan)
                    df[f"player_{pid}_average_player_speed"] = (
                        df[total_player].fillna(0) / safe
                    ).fillna(0)
                else:
                    df[f"player_{pid}_average_player_speed"] = 0.0
        return df

    def run_from_tracks(
        self,
        tracks: List[dict],
        num_frames: int,
        fps: float = 30,
    ) -> dict:
        """
        One-shot: run all track-based analytics and return a dict for the report.
        Rally/shot/wall remain stubbed until ball and bounce data exist.
        """
        player_stats_data = self.compute_player_stats_from_tracks(tracks, fps=fps)
        stats_df_records: List[dict] = []
        try:
            import pandas as pd
            df = self.build_stats_dataframe(player_stats_data, num_frames)
            if not df.empty:
                stats_df_records = df.to_dict(orient="records")
        except ImportError:
            pass
        except Exception:
            pass
        return {
            "rally_metrics": self.compute_rally_metrics(),
            "shot_speeds": self.compute_shot_speeds(),
            "wall_usage": self.compute_wall_usage(),
            "player_stats_data": player_stats_data,
            "stats_dataframe_records": stats_df_records,
        }
