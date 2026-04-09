import prisma from "../config/prisma.js";

export function getAll() {
  return prisma.road.findMany({ orderBy: { id: "asc" } });
}

export function getById(id) {
  return prisma.road.findUnique({ where: { id } });
}

export function updateTraffic({ roadId, roadName, vehicleCount, coverage, status, aiResult }) {
  const where = roadId ? { id: roadId } : { name: roadName };
  return prisma.road.update({
    where,
    data: {
      vehicleCount: vehicleCount ?? 0,
      coverage: coverage ?? 0,
      status: status ?? "FREE_FLOW",
      aiResult: aiResult ?? "",
    },
  });
}
