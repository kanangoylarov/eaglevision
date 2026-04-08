import { Router } from "express";
import { signup, signin, signout } from "../controllers/authController.js";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = Router();

router.post("/signup", signup);
router.post("/signin", signin);
router.post("/signout", requireAuth, signout);

export default router;
