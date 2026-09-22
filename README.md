# SlopeGuard - AI Landslide Early Warning System

SlopeGuard is an AI-powered landslide prediction and automated early warning system designed for the North Eastern Region of India. Built as a prototype for the Smart India Hackathon, it combines real-time environmental telemetry, an XGBoost predictive model, and a fully automated notification engine to trigger emergency alerts before disasters strike.

## 🚀 Key Features

*   **Interactive 3D Terrain Dashboard:** A glassmorphism-styled dashboard featuring a Mapbox/MapLibre GL JS engine. Includes Satellite and 3D Terrain toggles for deep topographical analysis of vulnerable zones.
*   **AI Risk Simulator:** An interactive tool to test the AI model. Adjust environmental parameters (Rainfall, Soil Moisture, Slope Gradient, NDVI, and Historical Data) and instantly see the XGBoost surrogate model calculate risk scores and factor contributions.
*   **Fully Automated Emergency Blasts:** The system doesn't just passively monitor. If the AI detects a **HIGH** or **CRITICAL** risk score, the backend automatically triggers an EmailJS payload, instantly blasting emergency evacuation emails to all subscribed users—with zero human intervention.
*   **Public Early Warning Registry:** A mobile-responsive subscription widget allowing citizens and local authorities to register their email addresses for instant critical alerts.
*   **Mobile-First Responsive Design:** The UI is completely responsive, featuring slide-up navigation and padding optimized specifically to prevent overlap with Android and iOS mobile browser navigation bars.
*   **FastAPI Backend & Vercel Frontend:** A decoupled architecture with a blazing fast static frontend hosted on Vercel and a Python FastAPI backend deployed on Render.

---

## 🛠️ Tech Stack

*   **Frontend:** HTML5, Tailwind CSS, JavaScript (ES6+), MapLibre GL JS, Chart.js, Lucide Icons. (Hosted on Vercel)
*   **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic. (Hosted on Render)
*   **Machine Learning:** XGBoost, SHAP (Surrogate simulated for demo).
*   **Communications API:** EmailJS REST API (Bypassing Render SMTP firewalls).
*   **Storage:** In-memory state and browser `localStorage` for demo persistence.

---

## ⚙️ How the Automated Alert System Works

1.  **Subscription:** Users enter their email in the "Public Early Warning Registry". The frontend saves this to `localStorage` (for persistence) and registers it with the backend.
2.  **Telemetry Ingestion:** The AI model ingests environmental telemetry (or mock parameters via the Risk Simulator).
3.  **Risk Calculation:** The engine calculates a risk score (0-100) and assigns a label (LOW, MODERATE, HIGH, CRITICAL).
4.  **Autonomous Trigger:** If the label is **HIGH** or **CRITICAL**, the frontend/backend bridge automatically packages an emergency payload.
5.  **Bypassing Firewalls:** The backend acts as a Google Chrome browser (via spoofed User-Agent) to bypass Cloudflare security, hitting the EmailJS REST API.
6.  **Instant Delivery:** EmailJS dispatches the emergency emails to all registered authorities and citizens instantly.

---

## 💻 Local Development

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start the API
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive API documentation.

### Frontend

The frontend is a single static HTML file with no build step required.

```bash
cd frontend
python3 -m http.server 5500
```
Open `http://localhost:5500`. It will automatically detect `localhost` and point to the local backend.

---

## 🌍 Live Deployment

*   **Frontend:** `https://slope-guard-rust.vercel.app/`
*   **Backend:** `https://slopeguard-36tz.onrender.com/`

*(Note: Render free tier servers spin down after 15 minutes of inactivity. The first API request after a period of inactivity may take 60-90 seconds to respond as the server wakes up).*
