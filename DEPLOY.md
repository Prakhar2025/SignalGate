# Deployment (live demo)

Two free-tier services, five minutes. All configuration is environment-only
(ground rule 08); no credentials live in either repository.

## 1. Backend on Render

1. Push this repository to GitHub (done: Prakhar2025/SignalGate).
2. Render dashboard: New, Web Service, connect the repo.
3. Settings:
   - Runtime: Python 3
   - Build command: `pip install -r requirements-lock.txt && pip install -e . --no-deps && python -m generator.build --out data`
   - Start command: `uvicorn signalgate.api.app:app --host 0.0.0.0 --port $PORT`
4. Environment variables: none required. Optional LIVE capability:
   - `SIGNALGATE_MODE=live`, `SIGNALGATE_MODEL`, `SIGNALGATE_API_BASE`,
     `SIGNALGATE_API_KEY` (only if you want the server itself to hold a key).
5. Deploy. Note the URL, for example `https://signalgate-api.onrender.com`.

Free tier note: the service sleeps after about 15 idle minutes and the first
request afterwards takes up to a minute (cold start). The dataset is rebuilt
during deploy, so the demo needs no database and no uploads.

## 2. Frontend on Vercel

1. Vercel dashboard: Add New, Project, import the same repository.
2. Root directory: `frontend`. Framework: Next.js (detected). Everything
   else defaults.
3. Environment variable: `SIGNALGATE_API` =
   the Render URL from step 1 (for example
   `https://signalgate-api.onrender.com`). The Next.js rewrites proxy all
   API paths there, so the browser never cross-origin calls the backend.
4. Deploy. Share the Vercel URL as the live demo.

## 3. Optional: BYO-model in the product

The gate page has a "Bring your own model" panel: anyone can paste their own
OpenAI-compatible endpoint, model id, and key. The key stays in that
visitor's browser (localStorage), travels only with their own request, is
used for that single investigation, and is never logged, persisted, or
bundled server-side. With no key, everything runs on LOCAL_MOCK and every
published number stays reproducible.

## 4. Verification after deploy

- `https://<render-url>/healthz` returns `{"status": "ok", ...}`
- `https://<vercel-url>/api/metrics` returns the published numbers
- Submit the flagship example on the gate and expect `REJECT_SPURIOUS` with
  `LOOKAHEAD_COLLAPSE`
