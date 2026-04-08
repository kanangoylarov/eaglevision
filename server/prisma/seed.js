import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const stations = [
  "Dərnəgül",
  "Azadlıq prospekti",
  "Nəsimi",
  "Memar Əcəmi",
  "20 Yanvar",
  "İnşaatçılar",
  "Elmlər Akademiyası",
  "Nizami",
  "28 May",
  "Gənclik",
  "Nəriman Nərimanov",
  "Ulduz",
  "Koroğlu",
  "Qara Qarayev",
  "Neftçilər",
  "Xalqlar Dostluğu",
  "Əhmədli",
  "Həzi Aslanov",
];

const trainCodes = ["T-101", "T-102", "T-103", "T-104", "T-105"];

async function main() {
  for (const name of stations) {
    await prisma.station.upsert({
      where: { name },
      update: {},
      create: { name },
    });
  }
  console.log(`Seeded ${stations.length} stations.`);

  const allStations = await prisma.station.findMany({ orderBy: { id: "asc" } });
  for (let i = 0; i < trainCodes.length; i++) {
    const code = trainCodes[i];
    const station = allStations[i % allStations.length];
    await prisma.train.upsert({
      where: { trainCode: code },
      update: {},
      create: {
        trainCode: code,
        currentStationId: station.id,
      },
    });
  }
  console.log(`Seeded ${trainCodes.length} trains.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
