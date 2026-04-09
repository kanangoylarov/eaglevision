import * as mlService from "../services/mlService.js";
import * as trainService from "../services/trainService.js";
import * as stationService from "../services/stationService.js";
import * as roadService from "../services/roadService.js";

function detectVideo(file) {
  return (
    file.mimetype?.startsWith("video/") ||
    /\.(mp4|mov|avi|mkv|webm)$/i.test(file.originalname || "")
  );
}

// --- Metro: station analysis ---
export async function analyzeStation(req, res, next) {
  try {
    if (!req.file) return res.status(400).json({ error: "file is required" });
    const { stationId, stationName } = req.body;
    if (!stationId && !stationName) return res.status(400).json({ error: "stationId or stationName is required" });

    const isVideo = detectVideo(req.file);
    const prediction = isVideo
      ? await mlService.predictVideoDensity(req.file.buffer, req.file.originalname)
      : await mlService.predictDensity(req.file.buffer);

    const station = await stationService.updateDensity({
      stationId: stationId ? Number(stationId) : undefined,
      stationName,
      humanCount: prediction.humanCount,
      aiResult: prediction.aiResult,
    });

    res.json({ station, prediction });
  } catch (err) {
    next(err);
  }
}

// --- Metro: train analysis ---
export async function analyzeTrain(req, res, next) {
  try {
    if (!req.file) return res.status(400).json({ error: "file is required" });
    const { trainCode } = req.body;
    if (!trainCode) return res.status(400).json({ error: "trainCode is required" });

    const isVideo = detectVideo(req.file);
    const prediction = isVideo
      ? await mlService.predictVideoDensity(req.file.buffer, req.file.originalname)
      : await mlService.predictDensity(req.file.buffer);

    const train = await trainService.upsert({
      trainCode,
      humanCount: prediction.humanCount,
      aiResult: prediction.aiResult,
    });

    res.json({ train, prediction });
  } catch (err) {
    next(err);
  }
}

// --- Traffic: road analysis ---
export async function analyzeRoad(req, res, next) {
  try {
    if (!req.file) return res.status(400).json({ error: "file is required" });
    const { roadId, roadName } = req.body;
    if (!roadId && !roadName) return res.status(400).json({ error: "roadId or roadName is required" });

    const isVideo = detectVideo(req.file);
    const prediction = isVideo
      ? await mlService.predictTrafficVideo(req.file.buffer, req.file.originalname)
      : await mlService.predictTraffic(req.file.buffer);

    const road = await roadService.updateTraffic({
      roadId: roadId ? Number(roadId) : undefined,
      roadName,
      vehicleCount: prediction.vehicleCount,
      coverage: prediction.coverage ?? prediction.avgCoverage ?? 0,
      status: prediction.status,
      aiResult: prediction.aiResult,
    });

    res.json({ road, prediction });
  } catch (err) {
    next(err);
  }
}
