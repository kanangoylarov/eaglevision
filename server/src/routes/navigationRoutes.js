import { Router } from "express";
import { getStatus, getForecast, getRoute } from "../controllers/navigationController.js";

const router = Router();

router.get("/status", getStatus);
router.get("/forecast", getForecast);
router.get("/route", getRoute);

export default router;
