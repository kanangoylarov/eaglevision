# EagleVision — AI-Powered Urban Traffic & Transit Intelligence Platform

> Real-time multimodal navigation system for Baku that combines computer vision, deep learning forecasting, and intelligent routing to optimize urban mobility across roads and metro.

**Live Demo:** [http://167.172.145.17](http://167.172.145.17)

---

## The Problem

Baku faces growing urban mobility challenges: commuters have no way to know real-time road congestion or metro crowd levels, and no tool exists that can recommend whether to drive or take the metro based on current and predicted conditions. Traditional navigation apps treat roads and public transit as separate systems.

## Our Solution

EagleVision is a **full-stack AI platform** that unifies road traffic analysis and metro crowd detection into a single intelligent navigation system. It uses **5 ML models working in a pipeline** to detect current conditions, predict future congestion, and recommend optimal multimodal routes (drive vs. metro+walk) in real-time.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  Camera Feeds (roads) ──→ YOLO v8   (vehicle detection)        │
│  Camera Feeds (metro) ──→ CSRNet    (crowd density)            │
│  Historical Grid Data ──→ ConvLSTM  (3h congestion forecast)   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      DATA FUSION LAYER                          │
│  Combines YOLO counts + grid density + temporal features        │
│  Builds 33-feature vectors per intersection (lag features,      │
│  calendar, weather, neighbor data, cross features)              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    DECISION ENGINE                               │
│  LightGBM ──→ 1-hour congestion forecast per node (road+metro) │
│  Anomaly detection + trend analysis (increasing/decreasing)     │
│  Status classification: FREE_FLOW → NORMAL → HEAVY → CONGESTED │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                 MULTIMODAL ROUTING ENGINE                        │
│  Time-dependent A* algorithm with dynamic edge costs            │
│  Options: Drive Now | Metro Now | Wait+Metro | Wait+Drive       │
│  Considers: road congestion, metro crowds, trend forecasts      │
│  Outputs: optimal route + risk score + reliability + reasoning  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      FRONTEND (Vue 3)                           │
│  Dashboard: real-time stats, road status, metro stations        │
│  Navigation: Leaflet map + route comparison + AI forecast       │
│  Roads: per-intersection breakdown with trend indicators        │
│  Metro: station & train crowd density tables                    │
│  Analyze: upload video/image for on-demand AI analysis          │
└─────────────────────────────────────────────────────────────────┘
```

---

## ML Models — The 5-Model Pipeline

### 1. CSRNet (Crowd Scene Recognition Network)
- **Purpose:** Estimate number of people in metro stations/trains from camera images
- **Architecture:** VGG16 frontend + dilated convolution backend → density map
- **Input:** Single image or video (multi-frame sampling)
- **Output:** `{ humanCount: 44, density: "high" }`
- **Training notebook:** [`csrnet.ipynb`](csrnet.ipynb)

### 2. YOLOv8-nano (Vehicle Detection)
- **Purpose:** Count vehicles and estimate road coverage from traffic camera feeds
- **Architecture:** Ultralytics YOLOv8n, detecting cars, motorcycles, buses, trucks
- **Input:** Road camera image or video
- **Output:** `{ vehicleCount: 87, coverage: 38.2%, status: "HEAVY" }`
- **Training notebook:** [`yuklemeler/car_counter_orderedpipeline.ipynb`](yuklemeler/car_counter_orderedpipeline.ipynb)

### 3. ConvLSTM v2 (Spatiotemporal Congestion Forecasting)
- **Purpose:** Predict traffic congestion 1-3 hours into the future on a 32×32 city grid
- **Architecture:** 2-layer ConvLSTM encoder + autoregressive ConvLSTM decoder
- **Input:** Last 6 hours of grid data (2 channels: density + vehicle count)
- **Output:** 3 future hourly congestion grids (32×32 each)
- **Key improvement:** Autoregressive decoder — each prediction step feeds back into the next, producing genuinely different forecasts per hour
- **Training data:** 4,320 hours (180 days) of synthetic Baku traffic patterns with rush hours, weekends, seasonal variation, and random incidents
- **Training notebook:** [`yuklemeler/traffik_jam (1).ipynb`](yuklemeler/traffik_jam%20(1).ipynb)

### 4. LightGBM (Decision Engine)
- **Purpose:** Per-intersection 1-hour congestion forecast using 33 engineered features
- **Architecture:** Gradient boosted decision trees (500 rounds, MAE: 5.85%, R² = 0.95)
- **33 Features include:**
  - Real-time: current vehicle count, coverage ratio
  - Temporal lags: 5min, 15min, 30min, 1h ago counts + rolling stats
  - Calendar: hour, day of week, weekend, holiday, month
  - Node properties: type (road/metro), capacity, lane count
  - Cross features: rain × peak hour, holiday × hour
  - Neighbor features: average/max count, trend of adjacent intersections
  - Historical patterns: weekday/weekend averages, all-time max
- **Output:** `{ forecast_1h: 64.7%, status: "CONGESTED", trend: "increasing" }`
- **Training notebook:** [`yuklemeler/car_counter_orderedpipeline.ipynb`](yuklemeler/car_counter_orderedpipeline.ipynb) (Cell 8-10)

### 5. A* Multimodal Routing Engine
- **Purpose:** Find optimal route considering real-time congestion on both roads and metro
- **Algorithm:** Time-dependent A* with dynamic edge costs
- **Graph:** 11 road intersections + 5 metro stations + walk connections
- **Edge cost factors:**
  - Road: base time × congestion multiplier (1.0x–2.5x based on LightGBM forecast)
  - Metro: base time × crowd multiplier (1.0x–1.6x based on metro density)
  - Walk: fixed time (unaffected by traffic)
  - Trend adjustment: +0.2 if increasing, -0.15 if decreasing
- **Route options generated:**
  - **Drive Now** — road-only route with current traffic
  - **Metro Now** — walk + metro + walk with current crowd levels
  - **Wait 15min + Metro** — if metro is crowded but trend is decreasing
  - **Wait 20min + Drive** — if roads are congested but easing
- **Output:** Ranked routes with time, distance, risk (0-10), reliability %, and human-readable reasoning

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vue 3, Vite, PrimeVue, Pinia, Leaflet.js (OpenStreetMap), PWA |
| **Backend** | Node.js, Express.js, Prisma ORM |
| **Database** | PostgreSQL (Supabase) |
| **ML Runtime** | Python 3.12, PyTorch, LightGBM, OpenCV, Ultralytics |
| **ML Integration** | Child process (stdin/stdout JSON) — no separate ML server |
| **Auth** | JWT + bcrypt, cookie-based sessions |
| **Deployment** | DigitalOcean VPS, Nginx, PM2 |

---

## Repository Structure

```
eaglevision/
├── client/                      # Vue 3 frontend (Vite + PrimeVue)
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue    # Real-time stats dashboard
│   │   │   ├── Navigation.vue   # Leaflet map + route planner + AI forecast
│   │   │   ├── Roads.vue        # Per-road traffic breakdown
│   │   │   ├── Metro.vue        # Station & train crowd tables
│   │   │   ├── Analyze.vue      # Upload video/image for AI analysis
│   │   │   ├── Signin.vue       # Authentication
│   │   │   └── Signup.vue       # Registration
│   │   ├── stores/auth.js       # Pinia auth store
│   │   ├── api/index.js         # Axios API client
│   │   └── router/index.js      # Vue Router with auth guards
│   └── public/
│       └── logo.jpeg            # EagleVision logo
│
├── server/                      # Node.js backend (Express)
│   ├── ml/                      # ML models and prediction scripts
│   │   ├── predict.py           # CSRNet crowd density (function-based)
│   │   ├── predict_traffic.py   # YOLO vehicle detection (function-based)
│   │   ├── predict_congestion.py # ConvLSTM 3h forecast + grid status
│   │   ├── navigation_engine.py # Full pipeline: DataFusion + LightGBM + A* Router
│   │   ├── model.py             # CSRNet architecture definition
│   │   ├── model.pth            # CSRNet trained weights
│   │   ├── convlstm_model_v2.pth # ConvLSTM v2 trained weights
│   │   ├── yolov8n.pt           # YOLOv8-nano weights
│   │   ├── lightgbm_congestion.txt # LightGBM model
│   │   ├── lgb_features.pkl     # LightGBM feature list
│   │   ├── baku_grid_data_v2.npy # 4320h traffic grid (2ch, 32×32)
│   │   └── road_mask.npy        # Baku road network mask
│   ├── src/
│   │   ├── controllers/         # Request handlers
│   │   ├── routes/              # API route definitions
│   │   ├── services/            # Business logic + ML integration
│   │   └── middleware/          # Auth + error handling
│   ├── prisma/
│   │   ├── schema.prisma        # Database schema (User, Station, Train, Road)
│   │   └── seed.js              # Seed data (18 Baku metro stations, 5 trains)
│   └── server.js                # Entry point
│
├── yuklemeler/                  # Training notebooks and data
│   ├── car_counter_orderedpipeline.ipynb  # YOLO + LightGBM + DataFusion + Routing
│   ├── traffik_jam (1).ipynb              # ConvLSTM v2 training
│   ├── traffic_convlstm_v2/              # ConvLSTM v2 model + data
│   └── traffic_project/                   # Grid data + road mask + visualizations
│
├── csrnet.ipynb                 # CSRNet training notebook
├── nixpacks.toml                # Railway deployment config
├── railway.json                 # Railway deployment spec
├── render.yaml                  # Render deployment spec
└── requirements.txt             # Python dependencies
```

---

## API Endpoints

### Navigation (Full AI Pipeline)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/nav/status` | All intersection statuses (LightGBM forecast) |
| `GET` | `/api/nav/forecast` | Per-node 1h congestion forecast with trends |
| `GET` | `/api/nav/route?start=X&end=Y` | Multimodal route comparison (drive vs metro) |

### Congestion (ConvLSTM Grid)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/congestion/status` | Current grid congestion status |
| `GET` | `/api/congestion/forecast` | 3-hour prediction from ConvLSTM v2 |

### Metro & Roads
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stations` | All metro stations with crowd data |
| `GET` | `/api/trains` | All trains with current station |
| `GET` | `/api/roads` | All roads with traffic data |
| `POST` | `/api/stations/analyze` | Upload image/video for metro crowd analysis (CSRNet) |
| `POST` | `/api/trains/analyze` | Upload image/video for train analysis |
| `POST` | `/api/roads/analyze` | Upload image/video for traffic analysis (YOLO) |

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Create account |
| `POST` | `/api/auth/signin` | Sign in (returns JWT cookie) |
| `POST` | `/api/auth/signout` | Sign out |

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL (or Supabase account)

### Installation

```bash
git clone https://github.com/kanangoylarov/eaglevision.git
cd eaglevision

# Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install torch torchvision lightgbm scikit-learn scipy numpy opencv-python-headless pillow flask joblib pandas ultralytics

# Server dependencies
cd server
npm install
cp .env.example .env   # Edit with your DB credentials
npx prisma generate
npx prisma db push
node prisma/seed.js     # Seed 18 metro stations + 5 trains
cd ..

# Client dependencies
cd client
npm install
cd ..
```

### Environment Variables

Create `server/.env`:
```env
DATABASE_URL="postgresql://user:password@host:5432/dbname"
DIRECT_URL="postgresql://user:password@host:5432/dbname"
JWT_SECRET="your-secret-key"
PORT=3000
PYTHON_PATH="/path/to/venv/bin/python"
```

### Run (Development)

```bash
# Terminal 1 — Backend
cd server && npm run dev

# Terminal 2 — Frontend
cd client && npm run dev
```

Open **http://localhost:5173**

### Run (Production)

```bash
cd client && npm run build
cd ../server && node server.js
```

The Express server serves both the API and the built Vue frontend.

---

## Deployment

The project is deployed on a DigitalOcean VPS with:
- **Nginx** as reverse proxy (port 80 → localhost:3000)
- **PM2** for process management with auto-restart
- **Python venv** for ML dependencies on the server

Alternative deployment configs are included for:
- **Railway** (`nixpacks.toml`, `railway.json`)
- **Render** (`render.yaml`)

---

## Training the Models

All training notebooks are designed for **Google Colab** with GPU:

| Notebook | Model | Dataset | Epochs |
|----------|-------|---------|--------|
| `csrnet.ipynb` | CSRNet | ShanghaiTech Part A | Custom |
| `yuklemeler/traffik_jam (1).ipynb` | ConvLSTM v2 | 4,320h synthetic grid | 80 |
| `yuklemeler/car_counter_orderedpipeline.ipynb` | LightGBM + YOLO | 50K synthetic samples | 500 rounds |

The synthetic data in `baku_grid_data_v2.npy` models realistic Baku traffic:
- Rush hours (07-09, 17-19): high congestion
- Night (22-05): minimal traffic
- Weekends: 50-70% of weekday levels
- Random incidents: 5% chance of localized spikes
- Seasonal variation: summer -15%, autumn +10%

---

## Key Design Decisions

1. **No separate ML server** — All ML models run as Python functions via `child_process`, eliminating the need for Flask/FastAPI and simplifying deployment.

2. **Multimodal routing** — The A* router considers both road congestion AND metro crowd levels simultaneously, recommending "wait and take metro later" when data supports it.

3. **Autoregressive ConvLSTM** — v2 model uses a decoder cell that feeds predictions back as input, producing genuinely different forecasts for each future hour (unlike v1 which repeated the same output).

4. **33-feature LightGBM** — Goes beyond simple density readings by incorporating temporal lags, neighbor effects, calendar patterns, and cross-features for robust per-intersection forecasting.

5. **30-second auto-refresh** — All pages poll for updated data every 30 seconds, reflecting changing conditions throughout the day.

---

## Team

| Name | Role |
|------|------|
| Kanan Goylarov | Full-Stack Developer & ML Engineer |

---

## Hackathon Context

- **Event:** Data-Driven Solutions Hackathon 2026
- **Track:** Urban Mobility / Smart City
- **Focus:** End-to-end ML pipeline from detection to intelligent multimodal routing
