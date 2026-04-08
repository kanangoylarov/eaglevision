import * as stationService from "../services/stationService.js";

export async function getAllStations(req, res, next) {
  try {
    const stations = await stationService.getAll();
    res.json(stations);
  } catch (err) {
    next(err);
  }
}

export async function getStationTrains(req, res, next) {
  try {
    const id = Number(req.params.id);
    const trains = await stationService.getTrainsAtStation(id);
    res.json(trains);
  } catch (err) {
    next(err);
  }
}
