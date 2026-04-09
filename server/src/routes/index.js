import { Router } from "express";
import authRoutes from "./authRoutes.js";
import stationRoutes from "./stationRoutes.js";
import trainRoutes from "./trainRoutes.js";
import roadRoutes from "./roadRoutes.js";
import congestionRoutes from "./congestionRoutes.js";
import navigationRoutes from "./navigationRoutes.js";

const router = Router();

router.use("/auth", authRoutes);
router.use("/stations", stationRoutes);
router.use("/trains", trainRoutes);
router.use("/roads", roadRoutes);
router.use("/congestion", congestionRoutes);
router.use("/nav", navigationRoutes);

export default router;
