import { Router } from "express";
import multer from "multer";
import {
  getAllTrains,
  getTrainByCode,
  upsertTrain,
} from "../controllers/trainController.js";
import { analyzeTrain } from "../controllers/analyzeController.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { requireAdmin } from "../services/authService.js";

const router = Router();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 200 * 1024 * 1024 },
});

router.get("/", getAllTrains);
router.get("/:trainCode", getTrainByCode);
router.post("/", upsertTrain);
router.post("/analyze", requireAuth, requireAdmin, upload.single("file"), analyzeTrain);

export default router;
