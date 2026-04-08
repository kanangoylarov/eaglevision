import io
import os
import tempfile

import cv2
import numpy as np
import torch
from flask import Flask, jsonify, request
from PIL import Image
from torchvision import transforms

from model import CSRNet

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "model.pth")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = Flask(__name__)

transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)

model = CSRNet(load_weights=True)
checkpoint = torch.load(CHECKPOINT_PATH, map_location=DEVICE, weights_only=False)
state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
model.load_state_dict(state_dict)
model.to(DEVICE).eval()


def density_label(count: float) -> str:
    if count < 15:
        return "low"
    if count < 40:
        return "medium"
    return "high"


@app.get("/health")
def health():
    return jsonify({"status": "ok", "device": str(DEVICE)})


@app.post("/predict")
def predict():
    if "image" not in request.files:
        return jsonify({"error": "image file is required (form field 'image')"}), 400

    file = request.files["image"]
    try:
        img = Image.open(io.BytesIO(file.read())).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"invalid image: {e}"}), 400

    tensor = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = model(tensor)
    count = float(output.detach().cpu().sum().item())
    rounded = int(round(count))
    label = density_label(count)

    return jsonify(
        {
            "humanCount": rounded,
            "rawCount": count,
            "density": label,
            "aiResult": f"{rounded} people ({label} density)",
        }
    )


def predict_pil(img: Image.Image) -> float:
    tensor = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = model(tensor)
    return float(output.detach().cpu().sum().item())


@app.post("/predict-video")
def predict_video():
    if "video" not in request.files:
        return jsonify({"error": "video file is required (form field 'video')"}), 400

    file = request.files["video"]
    sample_count = int(request.form.get("samples", 8))

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return jsonify({"error": "could not open video"}), 400

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        if total <= 0:
            return jsonify({"error": "empty video"}), 400

        n = max(1, min(sample_count, total))
        indices = np.linspace(0, total - 1, n, dtype=int)

        counts = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            counts.append(predict_pil(img))

        cap.release()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if not counts:
        return jsonify({"error": "no frames decoded"}), 400

    avg = float(np.mean(counts))
    peak = float(np.max(counts))
    rounded = int(round(avg))
    label = density_label(avg)

    return jsonify(
        {
            "humanCount": rounded,
            "rawCount": avg,
            "peakCount": peak,
            "framesAnalyzed": len(counts),
            "density": label,
            "aiResult": f"{rounded} people avg ({label} density)",
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("ML_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
