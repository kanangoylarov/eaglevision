import prisma from "../config/prisma.js";

export function getAll() {
  return prisma.train.findMany({
    include: { currentStation: true },
    orderBy: { updatedAt: "desc" },
  });
}

export function getByCode(trainCode) {
  return prisma.train.findUnique({
    where: { trainCode },
    include: { currentStation: true },
  });
}

async function nextStationId(currentId) {
  const next = await prisma.station.findFirst({
    where: { id: { gt: currentId } },
    orderBy: { id: "asc" },
  });
  if (next) return next.id;
  const first = await prisma.station.findFirst({ orderBy: { id: "asc" } });
  return first?.id ?? currentId;
}

export async function upsert({ trainCode, humanCount, aiResult, currentStationId }) {
  const existing = await prisma.train.findUnique({ where: { trainCode } });

  if (existing) {
    const advancedId = await nextStationId(existing.currentStationId);
    return prisma.train.update({
      where: { trainCode },
      data: {
        humanCount: humanCount ?? existing.humanCount,
        aiResult: aiResult ?? existing.aiResult,
        currentStationId: advancedId,
      },
      include: { currentStation: true },
    });
  }

  const firstStation = await prisma.station.findFirst({ orderBy: { id: "asc" } });
  if (!firstStation) {
    const err = new Error("No stations available. Run seed first.");
    err.status = 500;
    throw err;
  }

  return prisma.train.create({
    data: {
      trainCode,
      humanCount: humanCount ?? 0,
      aiResult: aiResult ?? "",
      currentStationId: currentStationId ?? firstStation.id,
    },
    include: { currentStation: true },
  });
}
