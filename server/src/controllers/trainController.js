import * as trainService from "../services/trainService.js";

export async function getAllTrains(req, res, next) {
  try {
    const trains = await trainService.getAll();
    res.json(trains);
  } catch (err) {
    next(err);
  }
}

export async function getTrainByCode(req, res, next) {
  try {
    const train = await trainService.getByCode(req.params.trainCode);
    if (!train) return res.status(404).json({ error: "Train not found" });
    res.json(train);
  } catch (err) {
    next(err);
  }
}

export async function upsertTrain(req, res, next) {
  try {
    const { trainCode, humanCount, aiResult, currentStationId } = req.body;
    if (!trainCode || currentStationId == null) {
      return res
        .status(400)
        .json({ error: "trainCode and currentStationId are required" });
    }
    const train = await trainService.upsert({
      trainCode,
      humanCount,
      aiResult,
      currentStationId,
    });
    res.json(train);
  } catch (err) {
    next(err);
  }
}
