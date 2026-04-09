import * as mlService from "../services/mlService.js";

export async function getStatus(req, res, next) {
  try {
    const result = await mlService.getNavStatus();
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getForecast(req, res, next) {
  try {
    const result = await mlService.getNavForecast();
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getRoute(req, res, next) {
  try {
    const { start, end } = req.query;
    if (!start || !end) {
      return res.status(400).json({ error: "start and end query params required" });
    }
    const result = await mlService.getNavRoute(start, end);
    res.json(result);
  } catch (err) {
    next(err);
  }
}
