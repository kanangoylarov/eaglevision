import { Router } from "express";
import stationRoutes from "./stationRoutes.js";
import trainRoutes from "./trainRoutes.js";
import authRoutes from "./authRoutes.js";

const router = Router();

router.use("/auth", authRoutes);
router.use("/stations", stationRoutes);
router.use("/trains", trainRoutes);

export default router;
