# Deploy in ~5 Minutes (Free or Under $5) – Non‑Developer Friendly

Use **two free tiers**: frontend on **Vercel**, backend + worker + Redis on **Render**. Total cost: **$0** (within free limits). If you outgrow free, Render is about **$7/mo** for a small paid instance; still under $10.

---

## What You’ll Do

1. Push this repo to **GitHub** (if it isn’t already).
2. Deploy the **frontend** to Vercel (connect repo, 3 clicks).
3. Deploy the **backend** to Render (connect repo, add Redis, 1 click).
4. Set the frontend’s **backend URL** and redeploy once.

No terminal or code required after the repo is on GitHub.

---

## Step 1: Frontend on Vercel (Free)

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New…** → **Project**.
3. **Import** the GitHub repo that contains Clipify.
4. Set:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add **Environment Variable** (you’ll fill the value after Step 3):
   - Name: `VITE_API_BASE_URL`  
   - Value: leave empty for now (e.g. `https://your-backend.onrender.com` after you have the backend URL).
6. Click **Deploy**. Wait 1–2 minutes. Note your frontend URL (e.g. `https://clipify-xxx.vercel.app`).

---

## Step 2: Backend + Worker + Redis on Render (Free Tier)

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. **Create a Redis instance** (free, 90 days):
   - **Dashboard** → **New +** → **Redis**.
   - Name it (e.g. `clipify-redis`), region nearest to you → **Create**. Copy the **Internal Redis URL** (starts with `redis://`).
3. **Create a Web Service** (runs both API and worker in one):
   - **New +** → **Web Service**.
   - Connect the **same GitHub repo**.
   - Set:
     - **Name:** e.g. `clipify-api`
     - **Region:** same as Redis.
     - **Root Directory:** leave empty (repo root).
     - **Runtime:** **Docker**.
   - **Dockerfile path:** `Dockerfile.render` (so one service runs both API and worker).
   - **Environment:**
     - `REDIS_URL` = the Internal Redis URL from step 2 (or the **external** URL if you need to call from outside Render).
     - `CELERY_BROKER_URL` = same as `REDIS_URL`.
     - `CELERY_RESULT_BACKEND` = same as `REDIS_URL`.
   - **Create Web Service**. Render will build and run the Docker image. Copy the service URL (e.g. `https://clipify-api.onrender.com`).

---

## Step 3: Point Frontend at Backend

1. In **Vercel** → your Clipify project → **Settings** → **Environment Variables**.
2. Set **`VITE_API_BASE_URL`** = your Render backend URL (e.g. `https://clipify-api.onrender.com`) **with no trailing slash**.
3. **Redeploy** the frontend (Deployments → ⋮ → Redeploy).

Open your Vercel URL: you should see the app and it will call the backend on Render.

**If you see "Request failed with status code 404" when you click Generate clip:**  
The frontend is calling Vercel instead of your backend. You must set **`VITE_API_BASE_URL`** in Vercel to your **Render backend URL** (e.g. `https://clipify-api-xxxx.onrender.com` — no trailing slash), then **redeploy** the frontend (Deployments → ⋮ → Redeploy). Vite bakes env vars into the build, so a new deploy is required after changing them.

**YouTube: "Sign in to confirm you're not a bot" / HTTP 400:**  
Use one of these on Render (Environment tab):

- **Easiest:** **`YT_DLP_COOKIES_CONTENT`** — Paste the **entire contents** of your `youtubecookies.txt` into this env var (Render allows multiline). No upload needed.
- **Or a URL:** **`YT_DLP_COOKIES_URL`** — Host the cookies file somewhere that returns it as plain text, then set this to that URL. Options:
  - **GitHub Gist (secret):** Create a new Gist at [gist.github.com](https://gist.github.com), set "Secret", upload or paste your `youtubecookies.txt`, then click "Raw" and copy the URL. Use that as `YT_DLP_COOKIES_URL`. (Anyone with the link can see the file, so prefer secret gist and don’t share the link.)
  - **Other:** Any HTTPS URL that returns the cookies file (e.g. a private S3/R2 link, or a small paste service that supports raw output).

Alternatively use **Upload file** with a video you already have.

**Upload file: "No module named 'requests'":**  
The backend image was built without the `requests` dependency. Redeploy the backend (e.g. push a commit or trigger a redeploy on Render) so it rebuilds with the updated `requirements.txt` that includes `requests`.

---

## Free Tier Limits (So You Stay Free or Under $5)

- **Vercel:** Free tier is enough for this frontend (bandwidth/hits limits are generous).
- **Render free Web Service:** Spins down after ~15 min of no traffic; first request after that can take 30–60 seconds to wake. Free Redis is 90 days (then you’d recreate or switch to a paid Redis).
- To stay under **$5/month**: use only Render free Web Service + free Redis; if you need always-on, upgrade only the Web Service to the cheapest paid plan (~$7/mo); total still in the “under $10” range.

---

## Summary

| Part        | Where   | Cost   | Time      |
|------------|---------|--------|-----------|
| Frontend   | Vercel  | Free   | ~2 min    |
| Backend+Worker | Render (Docker) | Free* | ~3–5 min |
| Redis      | Render  | Free** | ~1 min    |

\* Free tier spins down when idle.  
\** Free Redis 90 days.

Total: **about 5 minutes**, **$0** to start, and **under $5** (or just free) if you stay on free tiers.
