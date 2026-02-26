# Functional interfaces and analysis (from Functional Block Diagram)

Derived from the nine functional blocks (Acquire Match Input → … → Present Results). Abstract data and logic only; no implementation details.

---

## 1. Interface identification

Every interaction between functional blocks is one interface. Producer = block that outputs; Consumer = block that receives.

| Interface | Producer | Consumer | Data (abstract) | Direction |
|-----------|----------|----------|-----------------|-----------|
| IF-1 | Configure Court | Validate Court for Match | Court model | Configure Court → Validate Court for Match |
| IF-2 | Acquire Match Input | Track Players | Video frames | Acquire Match Input → Track Players |
| IF-3 | Acquire Match Input | Produce Highlights | Video frames | Acquire Match Input → Produce Highlights |
| IF-4 | Acquire Match Input | Build Report | Match metadata | Acquire Match Input → Build Report |
| IF-5 | Validate Court for Match | Track Players | Validated court model | Validate Court for Match → Track Players |
| IF-6 | Track Players | Map Trajectories to Court | Player trajectories (image coordinates) | Track Players → Map Trajectories to Court |
| IF-7 | Map Trajectories to Court | Compute Movement and Spatial Metrics | Player trajectories (court coordinates) | Map Trajectories to Court → Compute Movement and Spatial Metrics |
| IF-8 | Compute Movement and Spatial Metrics | Build Report | Movement metrics, spatial density | Compute Movement and Spatial Metrics → Build Report |
| IF-9 | Build Report | Produce Highlights | Structured report | Build Report → Produce Highlights |
| IF-10 | Build Report | Present Results | Structured report | Build Report → Present Results |
| IF-11 | Produce Highlights | Present Results | Highlight reel | Produce Highlights → Present Results |

**Note:** Configure Court has no producer in this flow (external input: court reference and reference imagery). Present Results has no consumer (output is user-facing).

---

## 2. Interface contracts (per interface)

For each interface: abstract data, logical update rate, timing/ordering, validity, and accuracy/precision in abstract terms. No protocols or implementation.

---

**IF-1 (Configure Court → Validate Court for Match)**  
- **Data:** Court model (image-to-court mapping, play boundary).  
- **Update rate:** When court configuration is created or changed (per court).  
- **Timing:** Court model must exist before any match is validated for that court.  
- **Validity duration:** Until court is reconfigured.  
- **Accuracy / precision:** Court model must be consistent with the reference imagery and usable for mapping.

---

**IF-2 (Acquire Match Input → Track Players)**  
- **Data:** Video frames (raw capture for the match).  
- **Update rate:** Once per match (full stream or sampled sequence).  
- **Timing:** Frames available before tracking starts; consumer reads in order.  
- **Validity duration:** For the duration of the match processing run.  
- **Accuracy / precision:** Frames must be temporally ordered and associated with the same match.

---

**IF-3 (Acquire Match Input → Produce Highlights)**  
- **Data:** Video frames (same as IF-2).  
- **Update rate:** Once per match.  
- **Timing:** Frames available when highlight production runs (after report is built).  
- **Validity duration:** Same as IF-2.  
- **Accuracy / precision:** Same as IF-2.

---

**IF-4 (Acquire Match Input → Build Report)**  
- **Data:** Match metadata (e.g. duration, identifiers).  
- **Update rate:** Once per match.  
- **Timing:** Available before or when Build Report runs.  
- **Validity duration:** Match run.  
- **Accuracy / precision:** Metadata must uniquely identify the match and describe its temporal extent.

---

**IF-5 (Validate Court for Match → Track Players)**  
- **Data:** Validated court model (court model deemed valid for this match).  
- **Update rate:** Once per match.  
- **Timing:** Available before Track Players runs.  
- **Validity duration:** Match run.  
- **Accuracy / precision:** Same as court model; validation attests fitness for this match.

---

**IF-6 (Track Players → Map Trajectories to Court)**  
- **Data:** Player trajectories (positions over time in image coordinates).  
- **Update rate:** Once per match (batch after tracking completes).  
- **Timing:** Consumer runs after Track Players completes.  
- **Validity duration:** For downstream processing.  
- **Accuracy / precision:** One trajectory per player; positions in image space; time-ordered.

---

**IF-7 (Map Trajectories to Court → Compute Movement and Spatial Metrics)**  
- **Data:** Player trajectories (court coordinates).  
- **Update rate:** Once per match.  
- **Timing:** Consumer runs after Map Trajectories to Court completes.  
- **Validity duration:** For downstream processing.  
- **Accuracy / precision:** Same structure as IF-6 output; coordinates in court space (e.g. consistent units).

---

**IF-8 (Compute Movement and Spatial Metrics → Build Report)**  
- **Data:** Movement metrics (distance, duration, speed per player and aggregate), spatial density (e.g. heatmap).  
- **Update rate:** Once per match.  
- **Timing:** Consumer runs after Compute completes.  
- **Validity duration:** For report assembly.  
- **Accuracy / precision:** Metrics and density consistent with input trajectories and court units.

---

**IF-9 (Build Report → Produce Highlights)**  
- **Data:** Structured report (summary, per-player stats, spatial reference, match metadata).  
- **Update rate:** Once per match.  
- **Timing:** Available when Produce Highlights runs.  
- **Validity duration:** Match run.  
- **Accuracy / precision:** Report is complete and internally consistent.

---

**IF-10 (Build Report → Present Results)**  
- **Data:** Structured report.  
- **Update rate:** Once per match.  
- **Timing:** Available when results are presented.  
- **Validity duration:** Until superseded or session ends.  
- **Accuracy / precision:** Same as IF-9.

---

**IF-11 (Produce Highlights → Present Results)**  
- **Data:** Highlight reel (ordered segments or single sequence).  
- **Update rate:** Once per match.  
- **Timing:** Available when results are presented.  
- **Validity duration:** Same as IF-10.  
- **Accuracy / precision:** Reel references valid segments of the match video.

---

## 3. Ownership mapping

For each abstract data item: owner (block that is responsible / single writer where applicable), who updates, who reads, who can modify. Logic only.

| Data | Owner | Who updates | Who reads | Who can modify |
|------|--------|-------------|-----------|----------------|
| Court model | Configure Court | Configure Court | Validate Court for Match | Configure Court only |
| Video frames | Acquire Match Input | Acquire Match Input | Track Players, Produce Highlights | Acquire Match Input only |
| Match metadata | Acquire Match Input | Acquire Match Input | Build Report | Acquire Match Input only |
| Validated court model | Validate Court for Match | Validate Court for Match | Track Players | Validate Court for Match only |
| Player trajectories (image) | Track Players | Track Players | Map Trajectories to Court | Track Players only |
| Player trajectories (court) | Map Trajectories to Court | Map Trajectories to Court | Compute Movement and Spatial Metrics | Map Trajectories to Court only |
| Movement metrics, spatial density | Compute Movement and Spatial Metrics | Compute Movement and Spatial Metrics | Build Report | Compute Movement and Spatial Metrics only |
| Structured report | Build Report | Build Report | Produce Highlights, Present Results | Build Report only |
| Highlight reel | Produce Highlights | Produce Highlights | Present Results | Produce Highlights only |
| User-facing results | Present Results | Present Results | User | Present Results only (assembles from report + reel) |

**Rule:** Each data item has a single logical owner (writer). Downstream blocks only read. No shared write; avoids undefined ownership and silent conflicts.

---

## 4. Blocking and deadlock analysis

### 4a. Blocking (logical “waits for”)

For each interface, the consumer logically waits for the producer to produce the data. No protocol or implementation.

| Interface | Blocking? | What consumer waits for | Both sides wait? | Deadlock risk? |
|-----------|------------|--------------------------|-----------------|----------------|
| IF-1 | Yes | Court model from Configure Court | No | No |
| IF-2 | Yes | Video frames from Acquire Match Input | No | No |
| IF-3 | Yes | Video frames from Acquire Match Input | No | No |
| IF-4 | Yes | Match metadata from Acquire Match Input | No | No |
| IF-5 | Yes | Validated court model from Validate Court for Match | No | No |
| IF-6 | Yes | Player trajectories (image) from Track Players | No | No |
| IF-7 | Yes | Player trajectories (court) from Map Trajectories to Court | No | No |
| IF-8 | Yes | Movement metrics and spatial density from Compute | No | No |
| IF-9 | Yes | Structured report from Build Report | No | No |
| IF-10 | Yes | Structured report from Build Report | No | No |
| IF-11 | Yes | Highlight reel from Produce Highlights | No | No |

**Summary:** All interfaces are one-way, producer → consumer. Consumer waits for producer; producer does not wait for consumer. No mutual waiting.

### 4b. Dependency graph (“waits for”)

Nodes = functional blocks. Arrow **A → B** = “A waits for B” (A cannot complete until B has produced the data A needs).

- **Validate Court for Match** ← Configure Court  
- **Track Players** ← Acquire Match Input, Validate Court for Match  
- **Map Trajectories to Court** ← Track Players  
- **Compute Movement and Spatial Metrics** ← Map Trajectories to Court  
- **Build Report** ← Compute Movement and Spatial Metrics, Acquire Match Input (match metadata)  
- **Produce Highlights** ← Build Report, Acquire Match Input (video frames)  
- **Present Results** ← Build Report, Produce Highlights  

**Cycle check:** No cycle. Flow is a DAG: Configure Court → Validate → Track → Map → Compute → Build Report; Acquire feeds Track, Produce Highlights, and Build Report; Build Report and Produce Highlights feed Present Results. No “A waits for B and B waits for A.”

### 4c. Deadlock, livelock, starvation

| Question | Answer | Justification |
|----------|--------|----------------|
| **Possible deadlock?** | **No** | No cycle of mutual waiting. Every dependency is one-way (consumer waits for producer). No block holds a resource another block needs while waiting for that block. |
| **Possible livelock?** | **No** | No retry or negotiation loop between blocks. Flow is deterministic and sequential; no abstract “retry until” between blocks that could repeat forever. |
| **Possible starvation?** | **No** | No shared resource with multiple contenders. Each block has at most one producer per input; no block is denied progress by another in the functional model. |

---

## 5. Data models (per interface / data item)

For every data item that flows across interfaces: abstract description, logical unit/range/update, owner, consumers, and classification. No implementation details.

| Data item | Description (abstract) | Unit / range / update (logical) | Owner | Consumers | Classification |
|-----------|-------------------------|----------------------------------|--------|-----------|-----------------|
| Court model | Mapping from image coordinates to court coordinates; play boundary (region of interest). | One per court; update when court is reconfigured. | Configure Court | Validate Court for Match | Configuration |
| Video frames | Ordered sequence of image frames for one match. | One sequence per match; temporally ordered; update once per match. | Acquire Match Input | Track Players, Produce Highlights | Measurement |
| Match metadata | Identifiers and temporal extent of the match (e.g. duration, match and court identifiers). | One per match; update when match is acquired. | Acquire Match Input | Build Report | State |
| Validated court model | Court model deemed valid for this match. | One per match run; update when validation runs. | Validate Court for Match | Track Players | State |
| Player trajectories (image) | Set of trajectories; each trajectory = sequence of (time, position in image coordinates), one per player. | One set per match; update when tracking completes. | Track Players | Map Trajectories to Court | Measurement |
| Player trajectories (court) | Same structure as image trajectories; positions in court coordinates (e.g. consistent units). | One set per match; update when mapping completes. | Map Trajectories to Court | Compute Movement and Spatial Metrics | Measurement |
| Movement metrics | Aggregate (total distance, total duration, number of players, etc.) and per-player (distance, duration, average speed, point count). | One set per match; update when computation completes. | Compute Movement and Spatial Metrics | Build Report | Measurement |
| Spatial density | 2D density of positions over the court (e.g. heatmap). | One per match; update when computation completes. | Compute Movement and Spatial Metrics | Build Report | Measurement |
| Structured report | Summary, per-player statistics, reference to spatial view, match metadata, list of highlight segments. | One per match; update when report is built. | Build Report | Produce Highlights, Present Results | State |
| Highlight reel | Ordered set of segments (each segment = start time, end time, optional reason) or single continuous sequence. | One per match; update when highlight production completes. | Produce Highlights | Present Results | State |
| User-facing results | Assembled report and highlight reel presented to the user. | One per match/session; update when results are presented. | Present Results | User | State |

**Classification legend:**  
- **Measurement:** Observed or derived data (frames, trajectories, metrics, density).  
- **State:** Current state of the system or match (metadata, validated model, report, reel, results).  
- **Configuration:** Setup that changes infrequently (court model).  
- **Command / Event / Log:** Not used in this flow at the functional level.

---

## 6. Data structures (abstract, in-depth)

Logical structure of each data type: composition, cardinality, constraints, and relationships. No implementation or format details.

---

### 6.1 Court model

**Composition**
- **Image-to-court mapping:** A function (or equivalent structure) that maps any point in image coordinates to a point in court coordinates. Defined over the full image frame. Required.
- **Play boundary:** A region in image coordinates (e.g. polygon or mask) that defines the court play area. Used to filter which image positions are “on court.” Optional in principle; if absent, the whole image may be treated as playable.

**Cardinality and scope**
- One court model per court. The mapping and boundary refer to a fixed image size (implicit frame dimensions).

**Constraints**
- Mapping must be defined for at least all points inside the play boundary (if present).
- Court coordinates use a consistent, linear scale (e.g. same units across the court; origin and axes fixed).

**Relationships**
- Produced by Configure Court; consumed by Validate Court for Match and (after validation) by Track Players and Map Trajectories to Court. The same logical structure is reused as validated court model.

---

### 6.2 Video frames

**Composition**
- **Sequence of frames:** Ordered list. Each element is one frame.
- **Per frame:** A single image (logical) plus an associated time or index. The time/index is monotonic along the sequence.

**Cardinality and scope**
- One sequence per match. Length = number of frames (variable; depends on match duration and capture rate).
- Frames are totally ordered (temporal or by index).

**Constraints**
- Order must be strict (no duplicate times/indices for ordering purposes).
- All frames belong to the same match; no mixing of matches in one sequence.

**Relationships**
- Produced by Acquire Match Input. Consumed by Track Players (full or sampled sequence) and by Produce Highlights (for cutting segments). The timeline used in trajectories and in the highlight reel must be consistent with this sequence’s time/index.

---

### 6.3 Match metadata

**Composition**
- **Match identifier:** Uniquely identifies the match. Required.
- **Court identifier:** Identifies the court this match belongs to. Required.
- **Temporal extent:** Duration of the match and/or start and end time (or start and end frame index). Required for report and highlights.
- **Optional descriptors:** E.g. capture rate (frames per time unit), resolution, or other attributes. Optional.

**Cardinality and scope**
- One set of match metadata per match. All attributes refer to the same match.

**Constraints**
- Duration (if present) must be non-negative. Start/end (if present) must be consistent (e.g. end ≥ start).
- Match and court identifiers must be stable and unique within their namespaces.

**Relationships**
- Produced by Acquire Match Input. Consumed by Build Report. The temporal extent in metadata must be consistent with the video frames sequence and with any times used in trajectories and highlight segments.

---

### 6.4 Validated court model

**Composition**
- Same as court model (image-to-court mapping + play boundary). No extra fields at the logical level.

**Semantics**
- Carries an implicit attestation: this court model has been checked and is valid for the current match (e.g. same court, dimensions consistent with the video, or other validation rules).

**Cardinality and scope**
- One validated court model per match run. It is a view on or copy of a court model, bound to that match.

**Relationships**
- Produced by Validate Court for Match (input: court model + match/court identifiers). Consumed only by Track Players. Not consumed by Map Trajectories to Court (which uses the same underlying court model for mapping).

---

### 6.5 Player trajectories (image or court)

**Composition**
- **Set of trajectories:** One trajectory per player. Players are distinguished by a stable player identifier (same identifier for the same person across the whole sequence).
- **Per trajectory:** An ordered sequence of points. Each point has:
  - **Time (or frame index):** Position in the match timeline. Required.
  - **Position:** Two coordinates (e.g. x, y) in either image space or court space. Required.
  - **Optional:** Bounding box or other geometric info in image space (only relevant for image trajectories); not required for court trajectories.

**Cardinality and scope**
- Number of trajectories = number of distinct players observed (variable; can be zero).
- Per trajectory: variable number of points (one per sampled frame or per detection). Points are ordered by time/frame; no duplicate times for the same trajectory.

**Constraints**
- Time/frame values must be non-negative and within the match timeline. Order within each trajectory must be strictly monotonic in time.
- Positions in image space must lie within the image (and optionally inside the play boundary). Positions in court space must use the same coordinate system as the court model.
- The same player identifier must not appear in more than one trajectory. All trajectories share the same time base (match timeline).

**Relationships**
- **Image:** Produced by Track Players; consumed by Map Trajectories to Court. Time base must match video frames.
- **Court:** Produced by Map Trajectories to Court; consumed by Compute Movement and Spatial Metrics. Player identifiers must be consistent with the image trajectories and with the per-player data in the report.

---

### 6.6 Movement metrics

**Composition**
- **Aggregate level:** Single set of values for the whole match.
  - Total distance (non-negative).
  - Total duration (non-negative; time or duration units).
  - Number of players (or trajectory count; non-negative integer).
  - Total point count (non-negative integer).
  - Optionally: average speed or other derived aggregates.
- **Per-player level:** One set of values per player identifier.
  - Distance, duration, average speed, point count (and optional derived values). All non-negative where applicable.

**Cardinality and scope**
- One aggregate set per match. Per-player entries: one per player identifier that appears in the input trajectories. The set of player identifiers in movement metrics must match the set in the trajectories (and later in the report).

**Constraints**
- Aggregate totals must be consistent with per-player sums (e.g. total distance = sum of per-player distances; total point count = sum of per-player point counts). Durations may be overlapping (multiple players at same time) so total duration is not necessarily the sum of per-player durations.
- No negative values for distance, duration, speed, or counts.

**Relationships**
- Produced by Compute Movement and Spatial Metrics from player trajectories (court). Consumed by Build Report. Player identifiers must align with the report’s per-player section and with trajectories.

---

### 6.7 Spatial density

**Composition**
- **2D distribution:** A function or discrete grid over the court plane. For each region (or cell), a single non-negative value.
- **Semantics:** Value = how often (count) or how much (e.g. time or weighted presence) players were in that region. Used to form a heatmap or similar visualization.

**Cardinality and scope**
- One spatial density per match. The court domain (extent and resolution) is defined by the court model’s coordinate system. Number of regions/cells is fixed for a given resolution; values are variable.

**Constraints**
- All values non-negative. The domain (court extent) must be consistent with the court model used for the trajectories that produced this density.
- Optionally normalized (e.g. sum to one or to total time) for display; normalization is a presentation choice.

**Relationships**
- Produced by Compute Movement and Spatial Metrics from player trajectories (court). Consumed by Build Report as a “reference to spatial density” (e.g. heatmap). The report does not embed the raw grid; it refers to it so that Present Results can retrieve or render it.

---

### 6.8 Structured report

**Composition**
- **Summary:** Match duration; report generated time; aggregate movement metrics (total distance, total duration, number of players, total point count; optional averages). All required where they exist in the pipeline.
- **Per-player statistics:** Keyed by player identifier. Each entry: distance, duration, average speed, point count (and optional derived values). Same set of player identifiers as in movement metrics and trajectories.
- **Reference to spatial density:** A reference (logical) to the spatial density produced for this match (e.g. heatmap). Optional if no trajectories; required if movement metrics exist.
- **Match metadata:** Match and court identifiers; temporal extent; optional descriptors. Must be consistent with the match metadata used earlier in the pipeline.
- **List of highlight segments:** Ordered list. Each segment: start time, end time (within match timeline); optional reason or label. May be empty (no highlights selected).

**Cardinality and scope**
- One structured report per match. Summary is single; per-player is one entry per player; highlight list length is variable (zero or more segments).

**Constraints**
- Start/end times of segments must lie within match duration. Segments may overlap or be adjacent; order in the list defines presentation order.
- Per-player identifiers must match movement metrics and trajectories. Aggregate values in summary must match the aggregate part of movement metrics.

**Relationships**
- Produced by Build Report (inputs: movement metrics, spatial density reference, match metadata). Consumed by Produce Highlights (for segment selection and ordering) and by Present Results (for display). The report is the single authoritative description of the match for downstream blocks.

---

### 6.9 Highlight reel

**Composition**
- **Option A – Segment list:** Ordered list of segments. Each segment: start time, end time (within match timeline); optional reason or label. The order of the list is the playback order.
- **Option B – Single continuous sequence:** One concatenated sequence (e.g. one “video” or one stream) built from the match video according to selected segments. Logically still defined by start/end times over the match timeline.

**Cardinality and scope**
- One highlight reel per match. Number of segments (Option A) or number of “parts” (Option B) is variable; can be zero (empty reel).

**Constraints**
- All segment times must be within the match timeline. End time ≥ start time per segment. Segments may overlap or be adjacent; ordering is explicit in the list (Option A) or in the construction (Option B).

**Relationships**
- Produced by Produce Highlights (inputs: structured report, video frames). Consumed by Present Results. The reel references the same match timeline as the video frames and the report’s highlight segment list; segment boundaries must be consistent with that timeline.

---

### 6.10 User-facing results

**Composition**
- **Report component:** The structured report (or a view of it) in a form the user can see (e.g. summary, per-player table, link or embedding for spatial density).
- **Highlight component:** The highlight reel (or a reference to it) in a form the user can play or navigate.
- Together they form the complete result of the pipeline from the user’s perspective.

**Cardinality and scope**
- One result set per match (or per session). Report and highlight are for the same match.

**Constraints**
- No additional logical constraints; consistency is inherited from the structured report and highlight reel.

**Relationships**
- Produced by Present Results (inputs: structured report, highlight reel). Consumed by the user. No further downstream block in the functional diagram.

---

*This document is the basis for interface identification, contracts, ownership mapping, blocking/deadlock analysis, data models, and data structures at the functional level. Implementation-specific details (e.g. file formats, storage, protocols) belong in separate design documents.*
