import { Router } from "express";
import multer from "multer";
import { getAllRoads, getRoadById } from "../controllers/roadController.js";
import { analyzeRoad } from "../controllers/analyzeController.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { requireAdmin } from "../services/authService.js";

const router = Router();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 200 * 1024 * 1024 },
});

router.get("/", getAllRoads);
router.get("/:id", getRoadById);
router.post("/analyze", requireAuth, requireAdmin, upload.single("file"), analyzeRoad);

export default router;
