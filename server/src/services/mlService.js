import { execFile } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ML_DIR = path.join(__dirname, "../../ml");
const PYTHON = process.env.PYTHON_PATH || "python3";

function runScript(scriptName, buffer, args = []) {
  return new Promise((resolve, reject) => {
    const script = path.join(ML_DIR, scriptName);
    const proc = execFile(
      PYTHON,
      [script, ...args],
      { maxBuffer: 50 * 1024 * 1024 },
      (err, stdout, stderr) => {
        if (err) return reject(new Error(stderr || err.message));
        try {
          const result = JSON.parse(stdout);
          if (result.error) return reject(new Error(result.error));
          resolve(result);
        } catch (e) {
          reject(new Error(`ML parse error: ${stdout.slice(0, 200)}`));
        }
      }
    );
    proc.stdin.write(buffer);
    proc.stdin.end();
  });
}

function runJson(scriptName, jsonData, args = []) {
  return runScript(scriptName, Buffer.from(JSON.stringify(jsonData)), args);
}

// --- Metro (CSRNet) ---
export function predictDensity(buffer) {
  return runScript("predict.py", buffer, ["image"]);
}

export function predictVideoDensity(buffer, _filename, samples = 8) {
  return runScript("predict.py", buffer, ["video", String(samples)]);
}

// --- Traffic (YOLO) ---
export function predictTraffic(buffer) {
  return runScript("predict_traffic.py", buffer, ["image"]);
}

export function predictTrafficVideo(buffer, _filename, samples = 8) {
  return runScript("predict_traffic.py", buffer, ["video", String(samples)]);
}

// --- Congestion (ConvLSTM — legacy grid) ---
export function getCongestionStatus(params = {}) {
  return runJson("predict_congestion.py", params, ["status"]);
}

export function getCongestionForecast(params = {}) {
  return runJson("predict_congestion.py", params, ["forecast"]);
}

export function getSmartRoute(start, end, params = {}) {
  return runJson("predict_congestion.py", { start, end, ...params }, ["route"]);
}

// --- Full Navigation Pipeline (DataFusion + LightGBM + A* Routing) ---
export function getNavStatus() {
  return runJson("navigation_engine.py", {}, ["status"]);
}

export function getNavForecast() {
  return runJson("navigation_engine.py", {}, ["forecast"]);
}

export function getNavRoute(start, end) {
  return runJson("navigation_engine.py", { start, end }, ["route"]);
}
