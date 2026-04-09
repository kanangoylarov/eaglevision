<div align="center">

# EagleVision

### Real-Time Metro & Traffic Intelligence Platform

**Computer Vision + Deep Learning + Multimodal Routing for Baku's Transit Network**

[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Express](https://img.shields.io/badge/Express-4.21-000000?logo=express&logoColor=white)](https://expressjs.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Prisma](https://img.shields.io/badge/Prisma-5.22-2D3748?logo=prisma&logoColor=white)](https://www.prisma.io/)
[![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8?logo=pwa&logoColor=white)]()

*Built for the **Data-Driven Solutions Hackathon 2026** &mdash; Urban Mobility / Smart City Track*

</div>

---

## The Problem

Baku's metro serves hundreds of thousands of passengers daily, yet riders have **zero visibility** into real-time congestion. There is no way to know if a station platform is packed, which train car has space, or whether a road alternative would be faster. Existing navigation tools optimize for distance &mdash; they ignore crowd density entirely.

## What EagleVision Does

EagleVision fuses **computer vision inference**, **spatiotemporal deep learning**, and **graph-based routing** into a single platform that answers one question: *"What is the fastest, least crowded way to get from A to B right now?"*

| Layer | Model | Input | Output |
|-------|-------|-------|--------|
| Crowd Detection | **CSRNet** (VGG16 + dilated convolutions) | Station/train camera frames | Density map &rarr; person count + congestion label |
| Vehicle Detection | **YOLOv8-nano** | Road camera frames | Vehicle counts by class, road coverage %, traffic status |
| Traffic Forecasting | **ConvLSTM v2** (autoregressive decoder) | 6h historical grid (2ch &times; 32&times;32) | 3h-ahead congestion heatmaps |
| Congestion Prediction | **LightGBM** | Tabular features (time, weather, events, history) | Node-level congestion scores |
| Route Planning | **A\* with congestion cost** | Origin/destination + live predictions | Multimodal routes (road + metro + walk) |

---

## Architecture

```
                                    ┌─────────────────────────┐
                                    │      Vue 3 Frontend     │
                                    │  PrimeVue + Leaflet PWA │
                                    └────────────┬────────────┘
                                                 │ REST API
                                    ┌────────────▼────────────┐
                                    │    Express.js Backend    │
                                    │  Controllers → Services  │
                                    │    JWT Auth + Multer     │
                                    ├──────────┬──────────────┤
                                    │  Prisma  │  ML Service  │
                                    │   ORM    │  (subprocess)│
                                    └────┬─────┴──────┬───────┘
                                         │            │
                                ┌────────▼──┐  ┌──────▼────────┐
                                │ PostgreSQL │  │ Python ML     │
                                │ (Supabase) │  │ CSRNet│YOLOv8 │
                                └────────────┘  │ ConvLSTM│LGBM │
                                                │ A* Router     │
                                                └───────────────┘
```

**Data flow for a route query:**
1. Frontend sends origin/destination + routing criteria
2. Express controller invokes `navigation_engine.py` via `child_process.execFile`
3. LightGBM predicts node-level congestion using time + weather + event features
4. A\* pathfinder computes optimal multimodal path with congestion-weighted edges
5. Response includes route geometry, estimated travel time, and congestion breakdown

---

## ML Pipeline Deep Dive

### CSRNet &mdash; Crowd Density Estimation

Custom implementation of [Li et al., 2018](https://arxiv.org/abs/1802.10062). VGG-16 frontend extracts spatial features; dilated convolutional backend (rates 2/4/8/16) produces a density map without pooling-induced resolution loss. A 1&times;1 conv layer outputs per-pixel crowd density. Summing the density map yields the total count.

```
Input (H&times;W&times;3) &rarr; VGG-16 frontend &rarr; Dilated backend &rarr; Density map &rarr; &Sigma; = person count
                                                                    Thresholds: <15 low | 15-40 med | 40+ high
```

Processes both single images and video (frame-by-frame with configurable skip). Checkpoint: `model.pth`.

### YOLOv8-nano &mdash; Vehicle Detection

Ultralytics YOLOv8-nano tracks four vehicle classes: `car`, `motorcycle`, `bus`, `truck`. Per-frame outputs include bounding boxes, class counts, and a road coverage percentage calculated from aggregate bbox area.

```
Coverage thresholds:
  >45% CONGESTED | >25% HEAVY | >10% NORMAL | &le;10% FREE_FLOW
```

Optimized for edge inference &mdash; nano variant runs at 30+ FPS on commodity GPUs.

### ConvLSTM v2 &mdash; Spatiotemporal Traffic Forecasting

Two-layer ConvLSTM encoder ingests 6 hours of historical traffic grids (2 channels: density + vehicle count, 32&times;32 spatial resolution). An **autoregressive decoder** generates 3 future timesteps by feeding each prediction back as input &mdash; capturing temporal dependencies that single-shot decoders miss.

```
Training data: 4,320 hours of synthetic Baku traffic (baku_grid_data_v2.npy)
Spatial mask:  road_mask.npy (32&times;32 binary road network)
Hotspots:      11 pre-identified congestion points
```

### LightGBM &mdash; Node-Level Congestion

Gradient-boosted decision trees predict congestion scores per intersection node. Feature vector includes:

- `hour`, `day_of_week`, `is_weekend`, `is_rush_hour`
- `temperature`, `precipitation`, `wind_speed`
- `event_nearby` (binary), `event_magnitude`
- `historical_avg_congestion` (rolling window)

Model artifact: `lightgbm_congestion.txt` (1.4 MB). Feature metadata: `lgb_features.pkl`.

### A\* Multimodal Router

Graph with three edge types:

| Type | Nodes | Edges | Cost Function |
|------|-------|-------|---------------|
| **Road** | 11 intersections | 15 segments | `distance &times; (1 + congestion_penalty)` |
| **Metro** | 5 stations (Sahil, 28 May, Ganjlik, Narimanov, Koroglu) | 4 links | `base_time + platform_wait` |
| **Walk** | Road &harr; Metro connectors | 5 links | `distance &times; walk_speed` |

Two routing modes:
- **Smart route** &mdash; minimizes congestion exposure using live LightGBM/ConvLSTM predictions
- **Default route** &mdash; minimizes raw distance

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vue 3 (Composition API), Vite 5, PrimeVue 4, Leaflet, Pinia, Axios |
| **Backend** | Node.js, Express 4, Prisma 5 ORM, JWT, Multer |
| **ML/CV** | PyTorch 2.6, Ultralytics YOLOv8, LightGBM, OpenCV 4.10, NumPy, SciPy |
| **Database** | PostgreSQL 16 (Supabase) |
| **Infra** | PWA (vite-plugin-pwa), Docker Compose |

---

## Project Structure

```
eaglevision/
├── client/                              # Vue 3 SPA
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue            # Real-time KPIs + congestion heatmap
│   │   │   ├── Metro.vue                # Station & train congestion analysis
│   │   │   ├── Roads.vue                # Traffic status by intersection
│   │   │   ├── Navigation.vue           # Multi-criteria route planner
│   │   │   ├── Analyze.vue              # Admin: upload media for ML inference
│   │   │   ├── Signin.vue               # Auth
│   │   │   └── Signup.vue
│   │   ├── router/index.js              # Route definitions + auth guards
│   │   ├── stores/auth.js               # Pinia auth store (JWT + role)
│   │   ├── api/index.js                 # Axios instance
│   │   └── main.js                      # App bootstrap (PrimeVue, PWA)
│   ├── vite.config.js                   # Dev proxy + PWA config
│   └── package.json
│
├── server/                              # Express API
│   ├── src/
│   │   ├── app.js                       # Express setup (CORS, routes, error handler)
│   │   ├── routes/                      # RESTful route definitions
│   │   │   ├── authRoutes.js
│   │   │   ├── stationRoutes.js
│   │   │   ├── trainRoutes.js
│   │   │   ├── roadRoutes.js
│   │   │   ├── navigationRoutes.js
│   │   │   └── congestionRoutes.js
│   │   ├── controllers/                 # Request handling
│   │   ├── services/                    # Business logic
│   │   │   └── mlService.js             # Python subprocess orchestration
│   │   ├── middleware/
│   │   │   ├── authMiddleware.js         # JWT verification
│   │   │   └── errorHandler.js
│   │   └── config/prisma.js             # Prisma client singleton
│   │
│   ├── prisma/
│   │   ├── schema.prisma                # DB schema (User, Station, Train, Road)
│   │   └── seed.js                      # Database seeding
│   │
│   ├── ml/                              # Python ML modules
│   │   ├── model.py                     # CSRNet architecture (VGG16 + dilated backend)
│   │   ├── predict.py                   # CSRNet inference (image/video)
│   │   ├── predict_traffic.py           # YOLOv8-nano vehicle detection
│   │   ├── predict_congestion.py        # ConvLSTM forecasting + grid routing
│   │   ├── navigation_engine.py         # LightGBM + A* multimodal router
│   │   ├── requirements.txt             # Python dependencies
│   │   ├── model.pth                    # CSRNet checkpoint
│   │   ├── yolov8n.pt                   # YOLOv8-nano weights
│   │   ├── lightgbm_congestion.txt      # LightGBM booster
│   │   ├── baku_grid_data_v2.npy        # 4,320h traffic grid (2ch x 32x32)
│   │   └── road_mask.npy               # Road network binary mask
│   │
│   ├── server.js                        # Entry point
│   └── package.json
│
└── csrnet.ipynb                         # Model training/experimentation notebook
```

---

## Database Schema

```sql
User     { id, firstName, lastName, email (unique), password (bcrypt), isAdmin, createdAt }
Station  { id, name (unique), humanCount, aiResult, updatedAt } → has many Train
Train    { id, trainCode (unique), humanCount, aiResult, currentStationId (FK), updatedAt }
Road     { id, name (unique), fromPoint, toPoint, distanceKm, vehicleCount, coverage, status, aiResult, updatedAt }
```

`aiResult` caches the latest ML inference output as a JSON string. `status` on Road uses the enum: `FREE_FLOW | NORMAL | HEAVY | CONGESTED`.

---

## Getting Started

### Prerequisites

- **Node.js** 18+
- **Python** 3.10+ with pip
- **PostgreSQL** (or a Supabase account)

### 1. Clone & install

```bash
git clone https://github.com/your-team/eaglevision.git
cd eaglevision

# Backend
cd server
npm install
npx prisma generate

# Frontend
cd ../client
npm install

# ML dependencies
cd ../server/ml
pip install -r requirements.txt
```

### 2. Configure environment

Create `server/.env`:

```env
DATABASE_URL="postgresql://user:pass@host:5432/dbname?pgbouncer=true"
DIRECT_URL="postgresql://user:pass@host:5432/dbname"
JWT_SECRET="your-secret-key"
PORT=3000
PYTHON_PATH="python3"
CLIENT_ORIGIN="http://localhost:5173"
```

### 3. Initialize database

```bash
cd server
npx prisma db push
node prisma/seed.js
```

### 4. Run

```bash
# Terminal 1 — Backend
cd server
npm run dev          # Express on :3000

# Terminal 2 — Frontend
cd client
npm run dev          # Vite on :5173 (proxies /api → :3000)
```

Open **http://localhost:5173** &mdash; the Vite dev server proxies all API calls to the Express backend.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/signup` | &mdash; | Register new user |
| `POST` | `/api/auth/signin` | &mdash; | Authenticate, receive JWT |
| `GET` | `/api/stations` | JWT | List all stations with congestion data |
| `GET` | `/api/stations/:id/trains` | JWT | Trains at a specific station |
| `GET` | `/api/trains` | JWT | All trains with current positions |
| `GET` | `/api/roads` | JWT | All road segments with traffic status |
| `POST` | `/api/analyze/predict` | Admin | Upload image/video &rarr; ML inference |
| `POST` | `/api/navigation/route` | JWT | Compute multimodal route |
| `GET` | `/api/navigation/status` | JWT | Network-wide congestion summary |
| `GET` | `/api/navigation/forecast` | JWT | 3h-ahead congestion forecast |

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/dashboard` | Real-time KPIs: total passengers across stations, active trains, road network status, congestion heatmap |
| **Metro** | `/metro` | Per-station and per-train congestion breakdown with Leaflet map visualization |
| **Roads** | `/roads` | Traffic status for each monitored intersection, coverage metrics |
| **Navigation** | `/navigation` | Multi-criteria route planner &mdash; select origin/destination and routing preference |
| **Analyze** | `/analyze` | Admin-only: upload image/video for CSRNet or YOLOv8 inference, results update DB |
| **Auth** | `/signin`, `/signup` | JWT-based authentication with role support |

All data-driven pages auto-refresh on 30-second polling intervals. The app is a **Progressive Web App** &mdash; installable and functional offline via service workers.

---

## Routing Criteria

The navigation engine supports four routing modes, each optimizing a different objective:

| Mode | Optimizes | Use Case |
|------|-----------|----------|
| **Fastest** | Minimum travel time | Daily commute, time-sensitive trips |
| **Least Crowded** | Minimum congestion exposure | Comfort-first, accessibility needs |
| **Fewest Transfers** | Minimum mode switches | Traveling with luggage, elderly passengers |
| **Most Walking** | Maximum walking segments | Fitness preference, short-distance flexibility |

Each query returns **two routes**: a congestion-aware *smart route* and a distance-optimized *default route* for comparison.

---

## Model Performance

| Model | Task | Key Metric |
|-------|------|------------|
| CSRNet | Person counting | MAE on density maps, tested on station camera frames |
| YOLOv8-nano | Vehicle detection | mAP@0.5, real-time inference (30+ FPS on GPU) |
| ConvLSTM v2 | 3h traffic forecast | MSE on held-out temporal splits |
| LightGBM | Congestion prediction | RMSE on tabular test set |

All models are trained on **synthetic data** modeled on real Baku Metro ridership patterns and Baku road traffic distributions. Production deployment would integrate live camera feeds and real-time weather/event APIs.

---

## Design Decisions

**ML as subprocess, not microservice.** Python scripts are invoked via `child_process.execFile` with JSON I/O. This eliminates inter-service networking complexity and keeps the stack deployable on a single machine &mdash; the right tradeoff for a hackathon demo that needs to "just work" on a judge's laptop.

**Autoregressive ConvLSTM decoder.** The v2 model feeds each predicted frame back as input to the next timestep, rather than generating all 3 future frames in a single forward pass. This captures cascading congestion dynamics (e.g., an upstream jam propagating downstream) at the cost of slightly slower inference.

**Congestion-weighted A\* over Dijkstra.** While the grid-based routing in `predict_congestion.py` uses Dijkstra, the multimodal router in `navigation_engine.py` uses A\* with haversine heuristic. The admissible heuristic guarantees optimality while pruning the search space significantly on the sparse Baku transit graph.

**PWA-first frontend.** Transit apps must work in metro stations with spotty connectivity. The service worker caches the app shell and last-known network state, so the route planner remains functional underground.

---

## Hackathon Context

| | |
|---|---|
| **Event** | Data-Driven Solutions Hackathon 2026 |
| **Track** | Urban Mobility / Smart City |
| **Duration** | ~48 hours |
| **Judging** | Data use, technical depth, real-world applicability, demo quality |

The platform runs on synthetic data modeled on real Baku ridership and traffic patterns. A production deployment would require integration with BMA's camera infrastructure, real-time weather APIs, and event calendars.

---

<div align="center">

**EagleVision** &mdash; seeing the city's pulse so you don't have to guess.

</div>
