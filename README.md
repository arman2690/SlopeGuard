# SlopeGuard — NER Landslide Risk Intelligence (Prototype)

AI-based landslide risk prediction and early-warning system for the North
Eastern Region of India. Built for Smart India Hackathon as a working
prototype: a real trained XGBoost model, a FastAPI backend, a Postgres/
Supabase schema, and a frontend that calls all of it live — with a demo-mode
fallback so it still runs with zero external services configured.

```
slopeguard/
├── frontend/index.html      # Single-file interactive dashboard (map, predictions, alerts, analytics)
├── backend/
│   ├── app/                 # FastAPI service
│   │   ├── main.py
│   │   ├── api/routes.py
│   │   ├── schemas/schemas.py
│   │   ├── services/        # config, demo data, Supabase client
│   │   └── data_sources/    # ISRO / Bhuvan / Bhusanket / GEE / weather adapters
│   ├── ml/                  # Training + inference pipeline
│   │   ├── features.py
│   │   ├── training/train.py
│   │   ├── prediction/predict.py
│   │   └── model/           # landslide_xgb_v1.json + model_meta.json (generated)
│   └── requirements.txt
├── database/schema.sql
├── .env.example
└── README.md
```

## What's real vs. what's demo

- **Real**: the XGBoost model is genuinely trained (on synthetic data — see
  below) and genuinely served; `/api/predict` runs actual inference with
  exact SHAP-style feature contributions from the booster. The FastAPI
  routes, Pydantic schemas, and database schema are fully implemented, not
  mocked.
- **Demo/synthetic**: there is no licensed landslide dataset bundled with
  this prototype, so the model is trained on a synthetic dataset generated
  from a documented rule (`backend/ml/training/train.py`). Model evaluation
  metrics are real numbers computed on a synthetic hold-out split — they are
  **not** a claim about real-world predictive accuracy. Weather, ISRO,
  Bhuvan, Bhusanket and Earth Engine data are demo/fallback unless you
  configure the corresponding API key, in which case the adapter interface
  is ready for a real implementation to be dropped in.

---

## 1. Run it locally

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate      # optional but recommended
pip install -r requirements.txt

# Train the model (writes backend/ml/model/landslide_xgb_v1.json)
python -m ml.training.train

# Start the API
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger docs, or
`http://localhost:8000/api/health` to confirm it's running.

### Frontend

The frontend is a single static HTML file — no build step.

```bash
cd frontend
python3 -m http.server 5500
```

Open `http://localhost:5500`. It auto-detects `localhost` and points at
`http://localhost:8000` for the API. If the backend is reachable, the header
pill switches from "OFFLINE DEMO MODE" to "API CONNECTED" and the map,
predictions, and alerts all switch to live data from your FastAPI service.
If the backend isn't running, everything still works using built-in
client-side demo data — the app degrades gracefully rather than breaking.

---

## 2. Deploy it for real (free tier friendly)

### Step 1 — Database (Supabase)

1. Create a project at [supabase.com](https://supabase.com).
2. Open the SQL editor and run `database/schema.sql`.
3. Copy your **Project URL** and **service_role key** (Settings → API) —
   you'll need these for `SUPABASE_URL` / `SUPABASE_KEY`.

### Step 2 — Backend (Render, Railway, or Fly.io — any Python host works)

Example using **Render**:

1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo, root directory `backend`.
3. Build command: `pip install -r requirements.txt && python -m ml.training.train`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example` (`DEMO_MODE`, `SUPABASE_URL`,
   `SUPABASE_KEY`, `CORS_ORIGINS` set to your frontend's deployed URL, etc).
6. Deploy. Note the resulting URL, e.g. `https://slopeguard-api.onrender.com`.

The `python -m ml.training.train` build step trains and saves the model as
part of deployment, so the service is self-contained — no external model
file to upload.

### Step 3 — Frontend (Vercel, or any static host)

The frontend is one HTML file, so any static host works (Vercel, Netlify,
GitHub Pages, Cloudflare Pages).

1. On Vercel: New Project → import the repo → set root directory to
   `frontend` → framework preset "Other" (static).
2. Before deploying, set `window.API_BASE` in `frontend/index.html` to your
   backend's deployed URL from Step 2 (search for `window.API_BASE =` near
   the top of the `<script>` block), **or** serve it dynamically by
   templating that line from `NEXT_PUBLIC_API_BASE` if you migrate this to
   a Next.js app per the original spec.
3. Deploy. Your dashboard is now live and calling your live API.

### Step 4 — Verify the full loop

Open the deployed frontend → the header pill should read **API CONNECTED**.
Go to Predictions, run a prediction — the "Prediction result" panel footer
should say **LIVE · XGBoost v1.0.0-prototype**, confirming the request went
frontend → FastAPI → XGBoost → response → UI, exactly as specified.

---

## 3. Connecting real data sources later

Each adapter in `backend/app/data_sources/` (`isro.py`, `bhuvan.py`,
`bhusanket.py`, `earth_engine.py`, `weather.py`) already defines the
function signature the rest of the app calls. To go live:

1. Get access/API keys from the provider.
2. Set the corresponding environment variable (see `.env.example`).
3. Implement the real HTTP/SDK call inside that adapter's function body,
   returning data in the same shape the demo fallback returns.
4. Nothing else in the app needs to change — routes and the frontend
   already consume the adapter's return shape.

## 4. Retraining on real data

Replace `generate_synthetic_dataset()` in `backend/ml/training/train.py`
with a loader that reads your real, labelled landslide dataset (ISRO/Bhuvan/
GEE-derived features + verified historical landslide events), keeping the
same column names as `ml/features.py::FEATURES`. Re-run
`python -m ml.training.train` — it will overwrite the model and
`model_meta.json` with metrics computed on your real hold-out set.

## 5. Risk thresholds

Configured once, centrally, in `backend/ml/features.py::RISK_THRESHOLDS`
(backend) — mirror any change in the frontend's `THRESHOLDS` constant in
`frontend/index.html` if you're not yet pulling zones live from the API.

## Limitations of this prototype (be upfront about these at demo time)

- The model is trained on synthetic data — treat its scores as illustrative.
- The in-memory alert store resets on backend restart when no database is
  connected.
- GIS adapters are interface stubs, not live integrations, until you supply
  credentials and implement the request.
- Map "state boundaries" shown are approximate circles for visual context,
  not authoritative administrative boundaries — swap in real GeoJSON
  boundaries for production use.
