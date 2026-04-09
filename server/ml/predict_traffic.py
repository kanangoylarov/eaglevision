import json
import os
import sys
import tempfile

import cv2
import numpy as np
from ultralytics import YOLO

MODEL_PATH = os.path.join(os.path.dirname(__file__), "yolov8n.pt")
model = YOLO(MODEL_PATH)
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def congestion_label(coverage):
    if coverage > 0.45:
        return "CONGESTED"
    if coverage > 0.25:
        return "HEAVY"
    if coverage > 0.10:
        return "NORMAL"
    return "FREE_FLOW"


def analyze_frame(frame):
    results = model(frame, verbose=False)[0]
    frame_area = frame.shape[0] * frame.shape[1]
    total_box_area = 0
    counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        if cls_id in VEHICLE_CLASSES and conf > 0.3:
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            total_box_area += (x2 - x1) * (y2 - y1)
            counts[VEHICLE_CLASSES[cls_id]] += 1

    coverage = total_box_area / frame_area if frame_area > 0 else 0
    return sum(counts.values()), counts, coverage


def predict_image(data):
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"error": "invalid image"}

    total, counts, coverage = analyze_frame(frame)
    status = congestion_label(coverage)
    return {
        "vehicleCount": total,
        "counts": counts,
        "coverage": round(coverage * 100, 1),
        "status": status,
        "aiResult": f"{total} vehicles ({status.lower().replace('_', ' ')})",
    }


def predict_video(data, samples=8):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {"error": "could not open video"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        if total_frames <= 0:
            return {"error": "empty video"}

        n = max(1, min(samples, total_frames))
        indices = np.linspace(0, total_frames - 1, n, dtype=int)

        snapshots = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok:
                continue
            vehicle_count, counts, coverage = analyze_frame(frame)
            status = congestion_label(coverage)
            snapshots.append({
                "second": round(int(idx) / fps, 1),
                "vehicleCount": vehicle_count,
                "counts": counts,
                "coverage": round(coverage * 100, 1),
                "status": status,
            })

        cap.release()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if not snapshots:
        return {"error": "no frames decoded"}

    avg_vehicles = float(np.mean([s["vehicleCount"] for s in snapshots]))
    avg_coverage = float(np.mean([s["coverage"] for s in snapshots]))
    peak_vehicles = max(s["vehicleCount"] for s in snapshots)
    overall_status = congestion_label(avg_coverage / 100)

    return {
        "vehicleCount": int(round(avg_vehicles)),
        "peakVehicles": peak_vehicles,
        "avgCoverage": round(avg_coverage, 1),
        "framesAnalyzed": len(snapshots),
        "status": overall_status,
        "snapshots": snapshots,
        "aiResult": f"{int(round(avg_vehicles))} vehicles avg ({overall_status.lower().replace('_', ' ')})",
    }


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "image"
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    data = sys.stdin.buffer.read()

    if mode == "video":
        result = predict_video(data, samples)
    else:
        result = predict_image(data)

    json.dump(result, sys.stdout)
