import prisma from "../config/prisma.js";

export function getAll() {
  return prisma.station.findMany({ orderBy: { id: "asc" } });
}

export function getTrainsAtStation(currentStationId) {
  return prisma.train.findMany({
    where: { currentStationId },
    include: { currentStation: true },
  });
}

export function updateDensity({ stationId, stationName, humanCount, aiResult }) {
  const where = stationId ? { id: stationId } : { name: stationName };
  return prisma.station.update({
    where,
    data: {
      humanCount: humanCount ?? 0,
      aiResult: aiResult ?? "",
    },
  });
}
