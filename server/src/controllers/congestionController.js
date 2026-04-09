import * as mlService from "../services/mlService.js";

export async function getStatus(req, res, next) {
  try {
    const hourOffset = req.query.hour ? Number(req.query.hour) : undefined;
    const result = await mlService.getCongestionStatus({ hourOffset });
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getForecast(req, res, next) {
  try {
    const hourOffset = req.query.hour ? Number(req.query.hour) : undefined;
    const result = await mlService.getCongestionForecast({ hourOffset });
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
    const hourOffset = req.query.hour ? Number(req.query.hour) : undefined;
    const result = await mlService.getSmartRoute(start, end, { hourOffset });
    res.json(result);
  } catch (err) {
    next(err);
  }
}
