# Deploy guide – step by step

This guide walks you through deploying the API so **anyone can open the user dashboard link** (e.g. `/view?match_id=xxx`). You can change the product name later; the steps stay the same.

---

## What you need before you start

1. **GitHub repo** – This project pushed to a GitHub repository (e.g. `CourtFlow-1` or whatever you’ll rename it to).
2. **At least one match uploaded to R2** – From your machine you’ve run the pipeline and uploaded to Cloudflare R2 (see [Upload to R2](#step-0-upload-a-match-to-r2) below).
3. **R2 credentials** – You have these four values (from Cloudflare R2):
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_BUCKET` (your bucket name, e.g. `courtflow`)
   - `R2_ACCOUNT_ID`
4. **An account** on [Render](https://render.com) or [Railway](https://railway.app) (both have free tiers).

---

## Step 0: Upload a match to R2

Do this on your **local machine** (where you already run the pipeline).

1. Open a terminal in the project root.
2. Make sure `.env` has your R2 variables set (see main README “Cloud upload (R2)”).
3. Run:

```bash
python3 -m src.app.cli upload-match --match_id match_2026_02_25_022906
```

(Use your real match ID if different.)

4. You should see: `Uploaded keys: ['matches/.../highlights.mp4', 'matches/.../report.json']`.
5. Optional: In Cloudflare Dashboard → R2 → your bucket, confirm that `matches/match_2026_02_25_022906/` contains `report.json` and `highlights.mp4`.

Without this, the deployed API will have nothing to show when someone opens a link.

---

## Deploying on Render (detailed)

### Step 1: Sign in and connect GitHub

1. Go to **https://render.com** and sign in (or create an account).
2. Click **Dashboard** (or **New +**).
3. Click **Connect account** under “GitHub” (or **New → Web Service** and you’ll be asked to connect GitHub).
4. Authorize Render to access your GitHub. Choose “All repositories” or select only the repo that contains this project (e.g. `CourtFlow-1`).

### Step 2: Create a new Web Service

1. On the Render dashboard, click **New +** → **Web Service**.
2. If you see a list of repos, click **Connect** (or **Configure**) next to your repo (e.g. `your-username/CourtFlow-1`).
3. You’ll see a form with:
   - **Name** – e.g. `courtflow-api` (you can change this later; it only affects the default URL subdomain).
   - **Region** – Pick one close to your users (e.g. Oregon, Frankfurt).
   - **Branch** – Usually `main` (or `master`).
   - **Root Directory** – Leave blank if the project is at the repo root.
   - **Runtime** – **Python 3**.

### Step 3: Build and start commands

1. **Build Command**  
   Set it exactly to:
   ```bash
   pip install -r requirements.txt
   ```
   (Render runs this in the repo root. If you ever move the app into a subfolder, set **Root Directory** to that folder and keep this command, or use `pip install -r path/to/requirements.txt`.)

2. **Start Command**  
   Set it exactly to:
   ```bash
   uvicorn src.app.api:app --host 0.0.0.0 --port $PORT
   ```
   - `0.0.0.0` lets Render reach your app.
   - `$PORT` is set by Render (e.g. 10000); do not replace it with a number.

3. **Instance type**  
   For free tier, leave the default (e.g. **Free**). For production later, you can switch to a paid instance.

### Step 4: Environment variables

1. In the same form, find the **Environment** or **Environment Variables** section.
2. Click **Add Environment Variable** and add these **four** variables (one by one). Use the same values you have in your local `.env` for R2:

   | Key | Value (example – use your real values) |
   |-----|----------------------------------------|
   | `R2_ACCESS_KEY_ID` | Your R2 access key ID |
   | `R2_SECRET_ACCESS_KEY` | Your R2 secret access key |
   | `R2_BUCKET` | Your bucket name (e.g. `courtflow`) |
   | `R2_ACCOUNT_ID` | Your Cloudflare account ID |

   Do **not** add `PORT` – Render sets it automatically.

3. Optional (only if you need them later):
   - `COURTFLOW_DATA_DIR` – Only if you run the pipeline on this same service and need a data directory (not needed for “link only” deploy).
   - `COURTFLOW_LOG_LEVEL` – e.g. `INFO` or `DEBUG`.

### Step 5: Deploy

1. Click **Create Web Service** (or **Deploy**).
2. Render will clone the repo, run the build command, then the start command. The first deploy can take 2–5 minutes.
3. Watch the **Logs** tab. You should see something like:
   ```text
   INFO:     Uvicorn running on http://0.0.0.0:10000
   ```
4. When the status is **Live**, copy the service URL at the top (e.g. `https://courtflow-api-xxxx.onrender.com`).

### Step 6: Test the link

1. Open in a browser (use your real match ID and your real Render URL):
   ```text
   https://courtflow-api-xxxx.onrender.com/view?match_id=match_2026_02_25_022906
   ```
2. You should see the Phase 1 user dashboard (match, report, highlights link).
3. Optional: open the API docs:
   ```text
   https://courtflow-api-xxxx.onrender.com/docs
   ```

### Step 7: Share the link

Send users the **view** URL only (no login):

```text
https://your-service-name.onrender.com/view?match_id=THEIR_MATCH_ID
```

They need the correct `match_id` (you get that from your pipeline / ops dashboard after you upload that match to R2).

---

## Deploying on Railway (alternative)

1. Go to **https://railway.app** and sign in; connect your GitHub account and select the repo.
2. **New Project** → **Deploy from GitHub repo** → choose this repo and branch (e.g. `main`).
3. Railway may detect a **Dockerfile**. You can:
   - **Use Docker**: leave it; Railway will build the image and run it. Ensure the Dockerfile’s `CMD` uses `$PORT` (ours does).
   - **Or use Python**: in **Settings**, set **Build Command** to `pip install -r requirements.txt` and **Start Command** to `uvicorn src.app.api:app --host 0.0.0.0 --port $PORT`.
4. **Variables**: add the same four R2 variables as in the Render section. Railway usually sets `PORT` for you.
5. **Deploy**. When it’s up, open **Settings** → **Networking** → **Generate Domain** to get a URL like `https://xxx.up.railway.app`.
6. Test: `https://xxx.up.railway.app/view?match_id=match_2026_02_25_022906`.

---

## Will this work when we scale?

**Short answer:** Yes for “more users opening the same link.” For “many matches, many courts, and high traffic,” you’ll add a proper DB and possibly a CDN; the current design allows that.

- **What works as you grow**
  - **More people opening `/view?match_id=xxx`** – R2 and presigned URLs handle it; no change needed.
  - **More matches** – Upload more to R2; the API lists and serves them from R2 when there’s no local DB.
  - **Renaming the product** – Change service name, repo name, and env vars (see below); no code change required for “CourtFlow” vs another name.

- **What to add when you scale**
  - **Persistent DB for matches** – Today the deployed API can run with **no** SQLite (R2-only). When you run the pipeline on a server or need richer metadata, you’ll attach a real DB (e.g. Postgres on Render/Railway or Supabase) and point the app at it; the R2 fallback still works for report/URLs.
  - **Multiple API instances** – Stateless API + R2 works with multiple instances behind a load balancer; no sticky sessions needed.
  - **Heavy traffic / global users** – Put a CDN in front of the API; optionally serve `/view` or static assets from the CDN. R2 presigned URLs are per-request and already work from anywhere.
  - **Custom domain** – Render and Railway let you add your own domain (e.g. `app.yourproduct.com`) in the dashboard; no code change.

So: **what you’re doing now will work when you scale**, as long as you add a proper DB when you need it and optionally a CDN/custom domain for branding and performance.

---

## Changing the name later

You can rename the product without changing how deploy works.

| What to change | Where |
|----------------|--------|
| **Service name** | Render/Railway dashboard → service **Name**. Only affects the default URL (e.g. `new-name-xxx.onrender.com`). |
| **Repo name** | GitHub → repo **Settings** → rename. Update the connection in Render/Railway if you use “repo name” anywhere. |
| **R2 bucket** | You can create a new bucket (e.g. `newproduct`) and set `R2_BUCKET` to it; move or re-upload objects if needed. |
| **Env vars** | `COURTFLOW_*` and app name are only for your config and logs; renaming them is optional and doesn’t break deploy. |
| **Code / “CourtFlow” in UI** | Replace “CourtFlow” in `dashboard/view.html` and README when you’re ready; deploy steps stay the same. |

No special “migration” is required for deploy when you change the name; just update the service name, env vars if you change bucket name, and any branding in the repo.

---

## Using your own domain (e.g. courtflow.com)

To have the app at **courtflow.com** (or **www.courtflow.com**) instead of `courtflow-mqns.onrender.com`:

### 1. Add the domain in Render

1. In the **Render dashboard**, open your **CourtFlow** web service.
2. Go to **Settings** → **Custom Domains** (or **Environment** → **Custom Domains**).
3. Click **Add Custom Domain**.
4. Enter **courtflow.com** (and optionally **www.courtflow.com**).
5. Render will show you the **DNS records** to add (usually a **CNAME** for `www` and an **A** or **CNAME** for the root `courtflow.com`). Copy the **host/target** value (e.g. something like `courtflow-mqns.onrender.com`).

### 2. Point your domain at Render (where you bought the domain)

Go to the place you registered **courtflow.com** (e.g. Namecheap, GoDaddy, Cloudflare, Google Domains).

- **For www.courtflow.com**  
  Add a **CNAME** record:  
  - Name/host: `www`  
  - Target/value: the Render host Render gave you (e.g. `courtflow-mqns.onrender.com`).

- **For courtflow.com (root domain)**  
  - Render often gives you an **A** record (an IP) or tells you to use a CNAME “flattening” or ALIAS.  
  - Add whatever Render shows (e.g. **A** record with the IP they give, or the CNAME target if your registrar supports CNAME on root).

Save the DNS changes. They can take from a few minutes up to 24–48 hours to propagate.

### 3. HTTPS

Render will issue an SSL certificate for your custom domain once DNS is correct. After that, **https://courtflow.com** and **https://www.courtflow.com** will work.

No code changes are needed; the app is the same, only the URL changes.

---

## How to update the deploy

When you change code and want the live site to use the new version:

### Option 1: Push to GitHub (auto deploy)

1. Commit your changes locally:
   ```bash
   git add .
   git commit -m "Your message"
   git push origin main
   ```
2. If **Auto-Deploy** is on (Render: **Settings** → **Build & Deploy** → **Auto-Deploy**), Render will build and deploy the new commit within a few minutes.
3. Check the **Logs** or **Events** tab to see the new deploy.

### Option 2: Deploy from the Render dashboard

1. Open your service on **Render**.
2. Click **Manual Deploy** → **Deploy latest commit** (or pick a branch/commit if you use that).
3. Wait for the build and deploy to finish.

After either option, your custom domain (e.g. **courtflow.com**) will serve the updated app; no need to change the domain or DNS again.

---

## Quick reference – Render

| Step | What to set |
|------|-------------|
| Build | `pip install -r requirements.txt` |
| Start | `uvicorn src.app.api:app --host 0.0.0.0 --port $PORT` |
| Env | `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ACCOUNT_ID` |
| Link | `https://YOUR-SERVICE.onrender.com/view?match_id=MATCH_ID` |

---

## Troubleshooting

- **Blank page or “Match not found”**  
  - Confirm that match is uploaded to R2 (Step 0).  
  - Check that the four R2 env vars are set correctly on Render/Railway (no typos, no extra spaces).

- **502 / Service Unavailable**  
  - Check **Logs** in the dashboard. Often the app crashed on startup (e.g. missing env var or wrong start command).  
  - Ensure start command is exactly: `uvicorn src.app.api:app --host 0.0.0.0 --port $PORT`.

- **Free tier spins down**  
  - On Render free tier, the service may sleep after inactivity; the first request can take 30–60 seconds. Consider a paid instance or a small cron that hits `/health` if you need always-fast response.
