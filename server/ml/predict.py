import io
import json
import os
import sys
import tempfile

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from model import CSRNet

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "model.pth")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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


def density_label(count):
    if count < 15:
        return "low"
    if count < 40:
        return "medium"
    return "high"


def predict_pil(img):
    tensor = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = model(tensor)
    return float(output.detach().cpu().sum().item())


def predict_image(data):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    count = predict_pil(img)
    rounded = int(round(count))
    label = density_label(count)
    return {
        "humanCount": rounded,
        "rawCount": count,
        "density": label,
        "aiResult": f"{rounded} people ({label} density)",
    }


def predict_video(data, samples=8):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {"error": "could not open video"}

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        if total <= 0:
            return {"error": "empty video"}

        n = max(1, min(samples, total))
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
        return {"error": "no frames decoded"}

    avg = float(np.mean(counts))
    peak = float(np.max(counts))
    rounded = int(round(avg))
    label = density_label(avg)

    return {
        "humanCount": rounded,
        "rawCount": avg,
        "peakCount": peak,
        "framesAnalyzed": len(counts),
        "density": label,
        "aiResult": f"{rounded} people avg ({label} density)",
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
