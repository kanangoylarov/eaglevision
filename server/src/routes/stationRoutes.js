import { Router } from "express";
import multer from "multer";
import {
  getAllStations,
  getStationTrains,
} from "../controllers/stationController.js";
import { analyzeStation } from "../controllers/analyzeController.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { requireAdmin } from "../services/authService.js";

const router = Router();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 200 * 1024 * 1024 },
});

router.get("/", getAllStations);
router.get("/:id/trains", getStationTrains);
router.post("/analyze", requireAuth, requireAdmin, upload.single("file"), analyzeStation);

export default router;
