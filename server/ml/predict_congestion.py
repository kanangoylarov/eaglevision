"""
ConvLSTM Traffic Congestion Predictor + Smart Routing

Modes:
  forecast  — predict next 3 hours from current grid state
  route     — find optimal route between two intersections
  status    — return current grid congestion status + hotspots

Input via stdin (JSON):
  forecast: {"grid": [...] or null}  (null = use last 6h from baku_grid_data)
  route:    {"start": "Neftchilar/Nizami", "end": "Bunyadov/Heydar", "grid": [...] or null}
  status:   {"grid": [...] or null}
"""

import heapq
import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn

ML_DIR = os.path.dirname(__file__)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ─── ConvLSTM Model ───

class ConvLSTMCell(nn.Module):
    def __init__(self, in_ch, hid_ch, kernel=3):
        super().__init__()
        self.hid_ch = hid_ch
        self.conv = nn.Conv2d(in_ch + hid_ch, 4 * hid_ch, kernel, padding=kernel // 2)

    def forward(self, x, h, c):
        gates = self.conv(torch.cat([x, h], dim=1))
        i, f, o, g = gates.chunk(4, dim=1)
        i, f, o = torch.sigmoid(i), torch.sigmoid(f), torch.sigmoid(o)
        c = f * c + i * torch.tanh(g)
        h = o * torch.tanh(c)
        return h, c


class TrafficPredictor(nn.Module):
    def __init__(self, in_ch=2, hid1=64, hid2=32, out_steps=3):
        super().__init__()
        self.hid1, self.hid2 = hid1, hid2
        self.out_steps = out_steps
        self.cell1 = ConvLSTMCell(in_ch, hid1)
        self.cell2 = ConvLSTMCell(hid1, hid2)
        self.output = nn.Conv2d(hid2, 1, kernel_size=1)
        self.decode_cell = ConvLSTMCell(1, hid2)

    def forward(self, x):
        B, T, C, H, W = x.shape
        h1 = torch.zeros(B, self.hid1, H, W, device=x.device)
        c1 = torch.zeros_like(h1)
        h2 = torch.zeros(B, self.hid2, H, W, device=x.device)
        c2 = torch.zeros_like(h2)

        for t in range(T):
            h1, c1 = self.cell1(x[:, t], h1, c1)
            h2, c2 = self.cell2(h1, h2, c2)

        hd, cd = h2, c2
        preds = []
        prev_pred = self.output(h2)

        for _ in range(self.out_steps):
            hd, cd = self.decode_cell(prev_pred, hd, cd)
            prev_pred = self.output(hd)
            preds.append(prev_pred.squeeze(1))

        return torch.stack(preds, dim=1)


# Load v2 model (2-channel, autoregressive decoder)
model = TrafficPredictor(in_ch=2).to(DEVICE)
model.load_state_dict(torch.load(
    os.path.join(ML_DIR, "convlstm_model_v2.pth"),
    map_location=DEVICE, weights_only=True
))
model.eval()

# Load v2 grid data (4320 hours, 2 channels)
grid_data = np.load(os.path.join(ML_DIR, "baku_grid_data_v2.npy"))  # (4320, 2, 32, 32)
road_mask = np.load(os.path.join(ML_DIR, "road_mask.npy"))          # (32, 32)
hotspots_arr = np.load(os.path.join(ML_DIR, "hotspots.npy"))        # (11, 2)

# ─── Graph (intersections + edges) ───

INTERSECTIONS = {
    "Neftchilar/Nizami": (8, 10),
    "Neftchilar/H.Aliyev": (8, 18),
    "Neftchilar/Heydar": (8, 24),
    "Babek/Nizami": (14, 10),
    "Babek/H.Aliyev": (14, 18),
    "Babek/Heydar": (14, 24),
    "Tbilisi/Nizami": (20, 10),
    "Tbilisi/H.Aliyev": (20, 18),
    "Bunyadov/Nizami": (25, 10),
    "Bunyadov/H.Aliyev": (25, 18),
    "Bunyadov/Heydar": (25, 24),
}

EDGES = [
    ("Neftchilar/Nizami", "Neftchilar/H.Aliyev", "Neftchilar Ave"),
    ("Neftchilar/H.Aliyev", "Neftchilar/Heydar", "Neftchilar Ave"),
    ("Babek/Nizami", "Babek/H.Aliyev", "Babek Ave"),
    ("Babek/H.Aliyev", "Babek/Heydar", "Babek Ave"),
    ("Tbilisi/Nizami", "Tbilisi/H.Aliyev", "Tbilisi Ave"),
    ("Bunyadov/Nizami", "Bunyadov/H.Aliyev", "Z.Bunyadov Ave"),
    ("Bunyadov/H.Aliyev", "Bunyadov/Heydar", "Z.Bunyadov Ave"),
    ("Neftchilar/Nizami", "Babek/Nizami", "Nizami St"),
    ("Babek/Nizami", "Tbilisi/Nizami", "Nizami St"),
    ("Tbilisi/Nizami", "Bunyadov/Nizami", "Nizami St"),
    ("Neftchilar/H.Aliyev", "Babek/H.Aliyev", "H.Aliyev St"),
    ("Babek/H.Aliyev", "Tbilisi/H.Aliyev", "H.Aliyev St"),
    ("Tbilisi/H.Aliyev", "Bunyadov/H.Aliyev", "H.Aliyev St"),
    ("Neftchilar/Heydar", "Babek/Heydar", "Heydar Aliyev Ave"),
    ("Babek/Heydar", "Bunyadov/Heydar", "Heydar Aliyev Ave"),
]

ROAD_NAMES = {
    (8, 10): "Neftchilar Ave / Nizami St",
    (8, 18): "Neftchilar Ave / H.Aliyev St",
    (8, 24): "Neftchilar Ave / Heydar Aliyev Ave",
    (14, 10): "Babek Ave / Nizami St",
    (14, 18): "Babek Ave / H.Aliyev St",
    (14, 24): "Babek Ave / Heydar Aliyev Ave",
    (20, 10): "Tbilisi Ave / Nizami St",
    (20, 18): "Tbilisi Ave / H.Aliyev St",
    (25, 10): "Z.Bunyadov Ave / Nizami St",
    (25, 18): "Z.Bunyadov Ave / H.Aliyev St",
    (25, 24): "Z.Bunyadov Ave / Heydar Aliyev Ave",
}


def get_edge_cost(n1, n2, cong_grid, use_congestion=True):
    r1, c1 = INTERSECTIONS[n1]
    r2, c2 = INTERSECTIONS[n2]
    base_dist = abs(r1 - r2) + abs(c1 - c2)
    if not use_congestion:
        return base_dist
    steps = max(abs(r2 - r1), abs(c2 - c1))
    total = 0.0
    for s in range(steps + 1):
        r = int(r1 + (r2 - r1) * s / max(steps, 1))
        c = int(c1 + (c2 - c1) * s / max(steps, 1))
        total += float(cong_grid[r, c])
    avg = total / (steps + 1)
    return base_dist * (1 + avg * 5)


def find_route(start, end, cong_grid, use_congestion=True):
    graph = {}
    for a, b, road in EDGES:
        cost = get_edge_cost(a, b, cong_grid, use_congestion)
        graph.setdefault(a, []).append((b, cost, road))
        graph.setdefault(b, []).append((a, cost, road))

    dist = {n: float("inf") for n in INTERSECTIONS}
    dist[start] = 0
    prev = {}
    pq = [(0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == end:
            break
        for v, w, road in graph.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = (u, road)
                heapq.heappush(pq, (nd, v))

    path, roads = [], []
    node = end
    while node in prev:
        path.append(node)
        parent, road = prev[node]
        roads.append(road)
        node = parent
    path.append(start)
    path.reverse()
    roads.reverse()

    return path, roads, dist[end]


def get_congestion_grid(input_data=None, hour_offset=None):
    """Get a congestion grid — from input or from stored data using current hour."""
    if input_data is not None:
        return np.array(input_data, dtype=np.float32)
    if hour_offset is not None:
        idx = min(max(int(hour_offset), 0), len(grid_data) - 1)
    else:
        # Use current hour of day to pick a representative slice from the data
        from datetime import datetime
        now = datetime.now()
        current_hour = now.hour
        # Find a matching hour in the dataset (skip first day, use day 2+)
        idx = 24 + current_hour  # day 2, same hour
    return grid_data[idx, 0]


def do_forecast(input_seq=None, hour_offset=None):
    """Predict next 3 hours using ConvLSTM v2 (autoregressive decoder)."""
    from datetime import datetime

    current_hour = datetime.now().hour
    if hour_offset is not None:
        base_idx = max(int(hour_offset), 6)
    else:
        base_idx = 24 + current_hour
    base_idx = max(6, min(base_idx, len(grid_data) - 1))

    # Input: last 6 hours, shape (6, 2, 32, 32)
    seq = grid_data[base_idx - 6:base_idx]
    x = torch.tensor(seq).unsqueeze(0).to(DEVICE)  # (1, 6, 2, 32, 32)
    with torch.no_grad():
        pred = model(x).cpu().numpy()[0]  # (3, 32, 32) — 3 autoregressive steps

    results = []
    for t in range(3):
        grid = pred[t]
        zones = extract_zones(grid)
        avg_congestion = float(grid[road_mask > 0.3].mean()) if (road_mask > 0.3).any() else 0

        intersection_statuses = []
        for name, (r, c) in INTERSECTIONS.items():
            r1, r2 = max(0, r - 2), min(31, r + 3)
            c1, c2 = max(0, c - 2), min(31, c + 3)
            val = float(grid[r1:r2, c1:c2].mean())
            if val > 0.55: st = "CONGESTED"
            elif val > 0.35: st = "HEAVY"
            elif val > 0.12: st = "NORMAL"
            else: st = "FREE_FLOW"
            intersection_statuses.append({
                "intersection": name,
                "congestion": round(val, 3),
                "status": st,
            })

        future_hour = (current_hour + t + 1) % 24
        results.append({
            "hour": f"+{t + 1}h ({future_hour:02d}:00)",
            "avgCongestion": round(avg_congestion, 3),
            "zones": zones,
            "intersections": intersection_statuses,
        })

    return results


def extract_zones(grid, threshold=0.2):
    """Extract congestion zones from a grid."""
    from scipy import ndimage
    binary = (grid > threshold).astype(int)
    labeled, num = ndimage.label(binary)
    zones = []
    for zid in range(1, num + 1):
        rows, cols = np.where(labeled == zid)
        cr, cc = float(rows.mean()), float(cols.mean())
        intensity = float(grid[labeled == zid].mean())
        size = int((labeled == zid).sum())

        nearest = "Unknown"
        min_dist = 999
        for (rr, rc), name in ROAD_NAMES.items():
            d = ((cr - rr) ** 2 + (cc - rc) ** 2) ** 0.5
            if d < min_dist:
                min_dist, nearest = d, name

        severity = "high" if intensity > 0.3 else ("medium" if intensity > 0.2 else "low")
        zones.append({
            "center": [round(cr, 1), round(cc, 1)],
            "size": size,
            "intensity": round(intensity, 3),
            "severity": severity,
            "nearestRoad": nearest,
            "estimatedDelay": int(size * 0.15),
        })
    return zones


def do_route(start, end, cong_grid=None, hour_offset=None):
    """Find smart and default routes."""
    grid = get_congestion_grid(cong_grid, hour_offset)

    path_smart, roads_smart, cost_smart = find_route(start, end, grid, use_congestion=True)
    path_default, roads_default, _ = find_route(start, end, grid, use_congestion=False)
    cost_default = sum(
        get_edge_cost(path_default[i], path_default[i + 1], grid, True)
        for i in range(len(path_default) - 1)
    )

    return {
        "smart": {
            "path": path_smart,
            "roads": list(dict.fromkeys(roads_smart)),
            "cost": round(cost_smart, 2),
            "estimatedMinutes": int(cost_smart * 0.5),
        },
        "default": {
            "path": path_default,
            "roads": list(dict.fromkeys(roads_default)),
            "cost": round(cost_default, 2),
            "estimatedMinutes": int(cost_default * 0.5),
        },
        "savedMinutes": max(0, int(cost_default * 0.5) - int(cost_smart * 0.5)),
    }


def do_status(cong_grid=None, hour_offset=None):
    """Return current intersection statuses."""
    grid = get_congestion_grid(cong_grid, hour_offset)
    statuses = []
    for name, (r, c) in INTERSECTIONS.items():
        r1, r2 = max(0, r - 2), min(31, r + 3)
        c1, c2 = max(0, c - 2), min(31, c + 3)
        val = float(grid[r1:r2, c1:c2].mean())
        if val > 0.55:
            status = "CONGESTED"
        elif val > 0.35:
            status = "HEAVY"
        elif val > 0.12:
            status = "NORMAL"
        else:
            status = "FREE_FLOW"
        statuses.append({
            "intersection": name,
            "gridPos": [r, c],
            "congestion": round(val, 3),
            "status": status,
        })
    return {
        "intersections": statuses,
        "roadMask": road_mask.tolist(),
        "grid": grid.tolist(),
    }


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    raw = sys.stdin.read().strip()
    params = json.loads(raw) if raw else {}

    if mode == "forecast":
        result = do_forecast(params.get("grid"), params.get("hourOffset"))
    elif mode == "route":
        result = do_route(
            params.get("start", "Neftchilar/Nizami"),
            params.get("end", "Bunyadov/Heydar"),
            params.get("grid"),
            params.get("hourOffset"),
        )
    elif mode == "status":
        result = do_status(params.get("grid"), params.get("hourOffset"))
    else:
        result = {"error": f"Unknown mode: {mode}"}

    json.dump(result, sys.stdout)
