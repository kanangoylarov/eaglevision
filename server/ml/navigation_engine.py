"""
Full Navigation Pipeline:
  DataFusion → LightGBM Forecast → DecisionEngine → A* Multimodal Routing

Modes:
  route       — find best route (road + metro options)
  status      — full pipeline status for all nodes
  forecast    — LightGBM 1h congestion forecast per node
"""

import heapq
import json
import os
import sys
from datetime import datetime

import joblib
import lightgbm as lgb
import numpy as np

ML_DIR = os.path.dirname(__file__)

# Load v2 grid data (4320 hours, 2 channels: density + vehicle_count)
grid_data = np.load(os.path.join(ML_DIR, "baku_grid_data_v2.npy"))  # (4320, 2, 32, 32)
road_mask = np.load(os.path.join(ML_DIR, "road_mask.npy"))

# Load LightGBM model
lgb_model = lgb.Booster(model_file=os.path.join(ML_DIR, "lightgbm_congestion.txt"))
lgb_features = joblib.load(os.path.join(ML_DIR, "lgb_features.pkl"))

# ─── Network Definition (Road + Metro) ───

NODES = {
    # Road intersections — (lat, lon, mode, grid_r, grid_c, capacity)
    "neft_nizami":   (40.3862, 49.8486, "road",  8, 10, 200),
    "neft_aliyev":   (40.3835, 49.8590, "road",  8, 18, 250),
    "neft_heydar":   (40.3808, 49.8700, "road",  8, 24, 300),
    "babek_nizami":  (40.3955, 49.8465, "road", 14, 10, 200),
    "babek_aliyev":  (40.3935, 49.8575, "road", 14, 18, 250),
    "babek_heydar":  (40.3915, 49.8690, "road", 14, 24, 300),
    "tbilisi_nizami":(40.4060, 49.8450, "road", 20, 10, 200),
    "tbilisi_aliyev":(40.4040, 49.8560, "road", 20, 18, 250),
    "bunyadov_nizami":(40.4170, 49.8440, "road", 25, 10, 200),
    "bunyadov_aliyev":(40.4150, 49.8550, "road", 25, 18, 250),
    "bunyadov_heydar":(40.4130, 49.8680, "road", 25, 24, 300),
    # Metro stations
    "m_sahil":       (40.3870, 49.8490, "metro",  8, 10, 500),
    "m_28may":       (40.3940, 49.8535, "metro", 14, 18, 500),
    "m_ganjlik":     (40.4020, 49.8550, "metro", 20, 18, 500),
    "m_narimanov":   (40.4050, 49.8560, "metro", 20, 18, 500),
    "m_koroglu":     (40.4160, 49.8550, "metro", 25, 18, 500),
}

DISPLAY_NAMES = {
    "neft_nizami": "Sahil area", "neft_aliyev": "Bayil road", "neft_heydar": "Boulevard",
    "babek_nizami": "Memar Ajami", "babek_aliyev": "Old City area", "babek_heydar": "Hazi Aslanov rd.",
    "tbilisi_nizami": "20 January area", "tbilisi_aliyev": "Narimanov area",
    "bunyadov_nizami": "Koroglu area", "bunyadov_aliyev": "Gara Garayev area", "bunyadov_heydar": "Hazi Aslanov m.",
    "m_sahil": "Sahil metro", "m_28may": "28 May metro",
    "m_ganjlik": "Ganjlik metro", "m_narimanov": "Narimanov metro", "m_koroglu": "Koroglu metro",
}

# Map old intersection keys to new node ids
OLD_KEY_MAP = {
    "Neftchilar/Nizami": "neft_nizami", "Neftchilar/H.Aliyev": "neft_aliyev", "Neftchilar/Heydar": "neft_heydar",
    "Babek/Nizami": "babek_nizami", "Babek/H.Aliyev": "babek_aliyev", "Babek/Heydar": "babek_heydar",
    "Tbilisi/Nizami": "tbilisi_nizami", "Tbilisi/H.Aliyev": "tbilisi_aliyev",
    "Bunyadov/Nizami": "bunyadov_nizami", "Bunyadov/H.Aliyev": "bunyadov_aliyev", "Bunyadov/Heydar": "bunyadov_heydar",
}

EDGES = [
    # Road edges: (from, to, base_time_min, distance_km, mode, road_name)
    ("neft_nizami", "neft_aliyev", 5, 1.2, "road", "Neftchilar Ave"),
    ("neft_aliyev", "neft_heydar", 5, 1.3, "road", "Neftchilar Ave"),
    ("babek_nizami", "babek_aliyev", 5, 1.3, "road", "Babek Ave"),
    ("babek_aliyev", "babek_heydar", 5, 1.3, "road", "Babek Ave"),
    ("tbilisi_nizami", "tbilisi_aliyev", 5, 1.2, "road", "Tbilisi Ave"),
    ("bunyadov_nizami", "bunyadov_aliyev", 5, 1.3, "road", "Z.Bunyadov Ave"),
    ("bunyadov_aliyev", "bunyadov_heydar", 6, 1.5, "road", "Z.Bunyadov Ave"),
    ("neft_nizami", "babek_nizami", 7, 1.8, "road", "M.Mushfig St"),
    ("babek_nizami", "tbilisi_nizami", 7, 1.8, "road", "M.Mushfig St"),
    ("tbilisi_nizami", "bunyadov_nizami", 7, 1.8, "road", "M.Mushfig St"),
    ("neft_aliyev", "babek_aliyev", 7, 1.8, "road", "A.Aliyev St"),
    ("babek_aliyev", "tbilisi_aliyev", 7, 1.8, "road", "A.Aliyev St"),
    ("tbilisi_aliyev", "bunyadov_aliyev", 7, 1.8, "road", "A.Aliyev St"),
    ("neft_heydar", "babek_heydar", 8, 2.0, "road", "H.Aliyev Ave"),
    ("babek_heydar", "bunyadov_heydar", 10, 2.5, "road", "H.Aliyev Ave"),
    # Walk to metro
    ("neft_nizami", "m_sahil", 3, 0.2, "walk", "walk"),
    ("babek_aliyev", "m_28may", 4, 0.3, "walk", "walk"),
    ("tbilisi_aliyev", "m_ganjlik", 3, 0.2, "walk", "walk"),
    ("tbilisi_aliyev", "m_narimanov", 4, 0.3, "walk", "walk"),
    ("bunyadov_aliyev", "m_koroglu", 3, 0.2, "walk", "walk"),
    # Metro edges
    ("m_sahil", "m_28may", 3, 2.5, "metro", "Metro Green Line"),
    ("m_28may", "m_ganjlik", 2, 1.5, "metro", "Metro Green Line"),
    ("m_ganjlik", "m_narimanov", 2, 1.0, "metro", "Metro Red Line"),
    ("m_narimanov", "m_koroglu", 3, 2.0, "metro", "Metro Red Line"),
]


# ─── DataFusion ───

class DataFusion:
    def __init__(self):
        self.node_history = {}

    def get_grid_reading(self, node_id, hour_idx):
        """Read congestion from grid data for a node."""
        info = NODES.get(node_id)
        if not info:
            return 0, 0
        _, _, _, r, c, cap = info
        idx = max(0, min(hour_idx, len(grid_data) - 1))
        density = float(grid_data[idx, 0, r, c])
        count = int(density * cap)
        return count, density

    def build_features(self, node_id, hour_idx=None):
        """Build 33-feature vector for LightGBM."""
        if hour_idx is None:
            hour_idx = 24 + datetime.now().hour

        info = NODES.get(node_id)
        if not info:
            return None
        _, _, mode, r, c, capacity = info

        current_count, coverage = self.get_grid_reading(node_id, hour_idx)

        # Lag features from grid
        counts_hist = []
        for offset in [1, 3, 6, 12]:
            idx = max(0, hour_idx - offset)
            cnt, _ = self.get_grid_reading(node_id, idx)
            counts_hist.append(cnt)

        recent_counts = [self.get_grid_reading(node_id, max(0, hour_idx - i))[0] for i in range(6)]
        avg_recent = float(np.mean(recent_counts)) if recent_counts else 0
        std_recent = float(np.std(recent_counts)) if recent_counts else 0
        trend = current_count - counts_hist[2] if len(counts_hist) > 2 else 0

        # Neighbor features
        neighbor_counts = []
        for nid, ninfo in NODES.items():
            if nid != node_id and ninfo[2] == mode:
                nc, _ = self.get_grid_reading(nid, hour_idx)
                neighbor_counts.append(nc)

        now = datetime.now()
        hour = now.hour
        dow = now.weekday()
        is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0

        features = {
            'current_count': current_count,
            'coverage_ratio': coverage,
            'count_5min_ago': counts_hist[0],
            'count_15min_ago': counts_hist[1],
            'count_30min_ago': counts_hist[2],
            'count_1h_ago': counts_hist[3],
            'avg_last_30min': avg_recent,
            'std_last_30min': std_recent,
            'trend_30min': trend,
            'temperature': 22.0,
            'rain_mm': 0.0,
            'wind_speed': 10.0,
            'visibility': 8.0,
            'hour': hour,
            'minute': now.minute,
            'day_of_week': dow,
            'is_weekend': 1 if dow >= 5 else 0,
            'is_holiday': 0,
            'month': now.month,
            'node_type': 0 if mode == 'road' else 1,
            'node_capacity': capacity,
            'lane_count': 3 if mode == 'road' else 0,
            'rain_x_peak': 0.0,
            'holiday_x_hour': 0,
            'event_nearby': 0,
            'event_distance_km': 5.0,
            'neighbor_avg_count': float(np.mean(neighbor_counts)) if neighbor_counts else 0,
            'neighbor_max_count': int(np.max(neighbor_counts)) if neighbor_counts else 0,
            'neighbor_trend': 0,
            'avg_this_hour_weekday': avg_recent,
            'avg_this_hour_weekend': avg_recent * 0.6,
            'max_this_hour_ever': int(capacity * 0.8),
        }
        return features


# ─── DecisionEngine ───

class DecisionEngine:
    def __init__(self, fusion):
        self.fusion = fusion
        self.node_states = {}

    def update_all(self, hour_idx=None):
        """Run LightGBM forecast for all nodes, store states."""
        import pandas as pd
        self.node_states = {}

        for node_id in NODES:
            feat = self.fusion.build_features(node_id, hour_idx)
            if feat is None:
                continue

            # LightGBM prediction
            feat_df = pd.DataFrame([feat])[lgb_features]
            forecast_1h = float(lgb_model.predict(feat_df)[0])
            forecast_1h = max(0, min(100, forecast_1h))

            # Determine trend
            trend_val = feat['trend_30min']
            if trend_val > 10:
                trend = "increasing"
            elif trend_val < -10:
                trend = "decreasing"
            else:
                trend = "stable"

            # Status
            if forecast_1h > 70:
                status = "CONGESTED"
            elif forecast_1h > 50:
                status = "HEAVY"
            elif forecast_1h > 25:
                status = "NORMAL"
            else:
                status = "FREE_FLOW"

            self.node_states[node_id] = {
                "node_id": node_id,
                "name": DISPLAY_NAMES.get(node_id, node_id),
                "mode": NODES[node_id][2],
                "current_count": feat['current_count'],
                "coverage": feat['coverage_ratio'],
                "forecast_1h": round(forecast_1h, 1),
                "trend": trend,
                "status": status,
            }


# ─── RoutingEngine (A* with time-dependent costs) ───

class RoutingEngine:
    def __init__(self, decision):
        self.decision = decision
        self.graph = {}
        for a, b, base_time, dist, mode, road in EDGES:
            self.graph.setdefault(a, []).append({"to": b, "base_time": base_time, "distance": dist, "mode": mode, "road": road})
            self.graph.setdefault(b, []).append({"to": a, "base_time": base_time, "distance": dist, "mode": mode, "road": road})

    def get_dynamic_cost(self, node_id, edge):
        base = edge["base_time"]
        mode = edge["mode"]
        state = self.decision.node_states.get(node_id)

        if state is None or mode == "walk":
            return base

        forecast = state["forecast_1h"]
        trend = state["trend"]

        if forecast > 85:
            mult = 3.0
        elif forecast > 70:
            mult = 2.0
        elif forecast > 50:
            mult = 1.5
        else:
            mult = 1.0

        if trend == "increasing":
            mult += 0.3
        elif trend == "decreasing":
            mult -= 0.2

        if mode == "metro":
            mult = 1.0 + (mult - 1.0) * 0.2

        return base * max(mult, 1.0)

    def heuristic(self, a, b):
        if a not in NODES or b not in NODES:
            return 0
        lat1, lon1 = NODES[a][0], NODES[a][1]
        lat2, lon2 = NODES[b][0], NODES[b][1]
        dist = ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5 * 111
        return dist / 30 * 60

    def find_route(self, start, end):
        queue = [(0, 0, start, [start], [])]
        visited = {}

        while queue:
            f_cost, cost, node, path, edges = heapq.heappop(queue)
            if node == end:
                total_dist = sum(e["distance"] for e in edges)
                return {
                    "path": path,
                    "edges": edges,
                    "totalTime": round(cost, 1),
                    "totalDistance": round(total_dist, 1),
                }
            if node in visited and visited[node] <= cost:
                continue
            visited[node] = cost

            for edge in self.graph.get(node, []):
                nxt = edge["to"]
                dc = self.get_dynamic_cost(nxt, edge)
                new_cost = cost + dc
                h = self.heuristic(nxt, end)
                heapq.heappush(queue, (
                    new_cost + h, new_cost, nxt, path + [nxt],
                    edges + [{"from": node, "to": nxt, "mode": edge["mode"], "road": edge["road"], "time": round(dc, 1), "distance": edge["distance"]}]
                ))
        return None

    def calculate_risk(self, route):
        risk = 0
        for edge in route.get("edges", []):
            state = self.decision.node_states.get(edge["to"], {})
            f = state.get("forecast_1h", 0)
            if f > 80: risk += 3
            elif f > 60: risk += 2
            elif f > 40: risk += 1
        return min(risk, 10)

    def find_multimodal(self, start, end):
        routes = []

        # Road-only route
        road_route = self.find_route(start, end)
        if road_route:
            road_route["type"] = "road"
            road_route["label"] = "Drive"
            road_route["risk"] = self.calculate_risk(road_route)
            road_route["reliability"] = max(100 - road_route["risk"] * 10, 20)
            road_route["roads"] = list(dict.fromkeys(e["road"] for e in road_route["edges"] if e["road"] != "walk"))
            routes.append(road_route)

        # Metro-assisted route
        metro_nodes = [n for n, info in NODES.items() if info[2] == "metro"]
        best_metro = None
        best_time = float("inf")

        for ms in metro_nodes:
            for me in metro_nodes:
                if ms == me:
                    continue
                leg1 = self.find_route(start, ms)
                leg2 = self.find_route(ms, me)
                leg3 = self.find_route(me, end)
                if leg1 and leg2 and leg3:
                    total = leg1["totalTime"] + leg2["totalTime"] + leg3["totalTime"]
                    if total < best_time:
                        best_time = total
                        best_metro = {
                            "path": leg1["path"] + leg2["path"][1:] + leg3["path"][1:],
                            "edges": leg1["edges"] + leg2["edges"] + leg3["edges"],
                            "totalTime": round(total, 1),
                            "totalDistance": round(leg1["totalDistance"] + leg2["totalDistance"] + leg3["totalDistance"], 1),
                            "type": "multimodal",
                            "label": "Metro + Walk",
                            "legs": [
                                {"mode": "walk", "time": round(leg1["totalTime"], 1), "to": DISPLAY_NAMES.get(ms, ms)},
                                {"mode": "metro", "time": round(leg2["totalTime"], 1), "from": DISPLAY_NAMES.get(ms, ms), "to": DISPLAY_NAMES.get(me, me)},
                                {"mode": "walk", "time": round(leg3["totalTime"], 1), "from": DISPLAY_NAMES.get(me, me)},
                            ],
                            "roads": [],
                        }

        if best_metro:
            best_metro["risk"] = self.calculate_risk(best_metro)
            best_metro["reliability"] = max(100 - best_metro["risk"] * 10, 20)
            routes.append(best_metro)

        routes.sort(key=lambda r: r["totalTime"])
        for i, r in enumerate(routes):
            r["rank"] = i + 1

        return routes


# ─── Initialize Pipeline ───

fusion = DataFusion()
decision = DecisionEngine(fusion)
router = RoutingEngine(decision)


def do_route(start, end):
    decision.update_all()
    # Map old keys to new node ids
    start = OLD_KEY_MAP.get(start, start)
    end = OLD_KEY_MAP.get(end, end)
    routes = router.find_multimodal(start, end)
    return {"routes": routes, "nodeStates": {k: v for k, v in decision.node_states.items()}}


def do_status():
    decision.update_all()
    nodes = []
    for nid, state in decision.node_states.items():
        info = NODES[nid]
        nodes.append({
            **state,
            "lat": info[0],
            "lon": info[1],
        })
    return {"nodes": nodes}


def do_forecast():
    decision.update_all()
    forecasts = []
    for nid, state in decision.node_states.items():
        forecasts.append({
            "node_id": nid,
            "name": state["name"],
            "mode": state["mode"],
            "forecast_1h": state["forecast_1h"],
            "trend": state["trend"],
            "status": state["status"],
            "current_count": state["current_count"],
        })
    return {"forecasts": forecasts}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    raw = sys.stdin.read().strip()
    params = json.loads(raw) if raw else {}

    if mode == "route":
        result = do_route(params.get("start", "neft_nizami"), params.get("end", "bunyadov_heydar"))
    elif mode == "forecast":
        result = do_forecast()
    elif mode == "status":
        result = do_status()
    else:
        result = {"error": f"Unknown mode: {mode}"}

    json.dump(result, sys.stdout)
