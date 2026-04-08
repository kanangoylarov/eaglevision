import * as mlService from "../services/mlService.js";
import * as trainService from "../services/trainService.js";
import * as stationService from "../services/stationService.js";

function detectVideo(file) {
  return (
    file.mimetype?.startsWith("video/") ||
    /\.(mp4|mov|avi|mkv|webm)$/i.test(file.originalname || "")
  );
}

async function runPrediction(file) {
  const isVideo = detectVideo(file);
  return isVideo
    ? mlService.predictVideoDensity(file.buffer, file.originalname)
    : mlService.predictDensity(file.buffer, file.originalname);
}

export async function analyzeTrain(req, res, next) {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "file is required (image or video)" });
    }
    const { trainCode } = req.body;
    if (!trainCode) {
      return res.status(400).json({ error: "trainCode is required" });
    }

    const prediction = await runPrediction(req.file);
    const train = await trainService.upsert({
      trainCode,
      humanCount: prediction.humanCount,
      aiResult: prediction.aiResult,
    });

    res.json({ train, prediction });
  } catch (err) {
    if (err.response) {
      return res
        .status(err.response.status || 502)
        .json({ error: "ML service error", detail: err.response.data });
    }
    next(err);
  }
}

export async function analyzeStation(req, res, next) {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "file is required (image or video)" });
    }
    const { stationId, stationName } = req.body;
    if (!stationId && !stationName) {
      return res.status(400).json({ error: "stationId or stationName is required" });
    }

    const prediction = await runPrediction(req.file);
    const station = await stationService.updateDensity({
      stationId: stationId ? Number(stationId) : undefined,
      stationName,
      humanCount: prediction.humanCount,
      aiResult: prediction.aiResult,
    });

    res.json({ station, prediction });
  } catch (err) {
    if (err.response) {
      return res
        .status(err.response.status || 502)
        .json({ error: "ML service error", detail: err.response.data });
    }
    next(err);
  }
}
