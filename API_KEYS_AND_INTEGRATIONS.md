# API Keys and External Integrations

Clipify uses these only when you enable real social posting. Until then, posting uses stubs (fake success URLs).

---

## Systems That Need API Keys (when you enable them)

### 1. **TikTok – Content Posting API**
- **What you need:** TikTok for Developers app, OAuth 2.0 access token (user auth).
- **Env var:** `TIKTOK_ACCESS_TOKEN`
- **Where to get:** [TikTok for Developers](https://developers.tiktok.com/) → create an app → Request Content Posting API → implement OAuth and store the access token. Token expires; you need refresh flow.
- **Used in:** `backend/services/publishing.py` – when token is set, replace the stub with a call to TikTok’s upload API (e.g. direct upload or init + upload endpoints per their docs).

### 2. **Instagram – Graph API (Reels)**
- **What you need:** Meta (Facebook) Developer app, Instagram Business/Creator account linked, Page connected, and a long‑lived User Access Token with `instagram_content_publish` (and often `pages_show_list`, `pages_read_engagement`).
- **Env var:** `INSTAGRAM_ACCESS_TOKEN` (or per‑page token).
- **Where to get:** [Meta for Developers](https://developers.facebook.com/) → create app → add Instagram Graph API → configure Instagram Basic Display or Content Publishing → get token via Graph API Explorer or your own OAuth flow. For Reels you use the Content Publishing API (container creation then publish).
- **Used in:** `backend/services/publishing.py` – when token is set, replace the stub with Graph API calls to create a Reel container and publish it.

### 3. **YouTube – Data API v3 (Shorts)**
- **What you need:** Google Cloud project, YouTube Data API v3 enabled, OAuth 2.0 credentials (desktop or web app). Shorts are uploaded as normal videos with short form; the client can use the same Upload API.
- **Env var:** `YOUTUBE_CLIENT_SECRETS_PATH` (path to `client_secrets.json`) **or** store refresh token and use a server-side OAuth flow; often you’ll have something like `YOUTUBE_REFRESH_TOKEN` + client id/secret.
- **Where to get:** [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → enable YouTube Data API v3 → Create OAuth 2.0 credentials → download JSON. Run a one‑time OAuth flow to get a refresh token and store it securely.
- **Used in:** `backend/services/publishing.py` – when credentials are set, replace the stub with the YouTube Resumable Upload API (e.g. via `google-api-python-client` or `httpx`).

### 4. **Optional – Upload‑Post or similar “post to many” services**
- Some third‑party APIs (e.g. “Upload-Post” style) offer one key and one endpoint to post to TikTok, Instagram, YouTube. If you use one, you’ll get a single API key and base URL.
- **Env var:** e.g. `UPLOAD_POST_API_KEY`, `UPLOAD_POST_BASE_URL`.
- **Used in:** You can add a branch in `publishing.py` that, when this key is set, calls their API instead of the per‑platform stubs.

---

## Summary table

| System              | Env var (example)        | Purpose                    |
|---------------------|--------------------------|----------------------------|
| TikTok              | `TIKTOK_ACCESS_TOKEN`    | Real TikTok uploads        |
| Instagram (Reels)   | `INSTAGRAM_ACCESS_TOKEN` | Real Reels uploads         |
| YouTube (Shorts)    | `YOUTUBE_CLIENT_SECRETS_PATH` or refresh token + client id/secret | Real Shorts uploads |
| Optional aggregator | e.g. `UPLOAD_POST_API_KEY` | Single API for multiple platforms |

---

## Enabling auth later (internal access)

- **Backend:** Set `API_KEY` in `.env`; the code in `api/auth.py` will enforce `X-API-Key` when `API_KEY` is non‑empty (auth is currently not applied to routes; you can re‑add `Depends(require_api_key)` in `main.py` when needed).
- **Frontend:** Set `VITE_API_KEY` to the same value so the app sends the header.

No other systems in Clipify require API keys for basic operation (ingest, transcribe, clip, render, burn, validate, and stub posting work without any keys).
