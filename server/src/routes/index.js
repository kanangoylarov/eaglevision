import { Router } from "express";
import authRoutes from "./authRoutes.js";
import stationRoutes from "./stationRoutes.js";
import trainRoutes from "./trainRoutes.js";
import roadRoutes from "./roadRoutes.js";
import congestionRoutes from "./congestionRoutes.js";

const router = Router();

router.use("/auth", authRoutes);
router.use("/stations", stationRoutes);
router.use("/trains", trainRoutes);
router.use("/roads", roadRoutes);
router.use("/congestion", congestionRoutes);

export default router;
