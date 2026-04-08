import { verifyToken } from "../services/authService.js";

export function requireAuth(req, res, next) {
  let token = req.cookies?.token;
  if (!token) {
    const header = req.headers.authorization;
    if (header && header.startsWith("Bearer ")) {
      token = header.slice(7);
    }
  }
  if (!token) {
    return res.status(401).json({ error: "Missing or invalid token" });
  }
  try {
    req.user = verifyToken(token);
    next();
  } catch {
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}
