import FormData from "form-data";
import axios from "axios";

const ML_URL = process.env.ML_SERVICE_URL || "http://localhost:5000";

export async function predictDensity(buffer, filename = "frame.jpg") {
  const form = new FormData();
  form.append("image", buffer, { filename });

  const { data } = await axios.post(`${ML_URL}/predict`, form, {
    headers: form.getHeaders(),
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
  });

  return data;
}

export async function predictVideoDensity(buffer, filename = "video.mp4", samples = 8) {
  const form = new FormData();
  form.append("video", buffer, { filename });
  form.append("samples", String(samples));

  const { data } = await axios.post(`${ML_URL}/predict-video`, form, {
    headers: form.getHeaders(),
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
  });

  return data;
}
