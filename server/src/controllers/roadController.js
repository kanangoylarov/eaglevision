import * as roadService from "../services/roadService.js";

export async function getAllRoads(req, res, next) {
  try {
    const roads = await roadService.getAll();
    res.json(roads);
  } catch (err) {
    next(err);
  }
}

export async function getRoadById(req, res, next) {
  try {
    const road = await roadService.getById(Number(req.params.id));
    if (!road) return res.status(404).json({ error: "Road not found" });
    res.json(road);
  } catch (err) {
    next(err);
  }
}
