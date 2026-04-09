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

// Roads matching the navigation grid — with simulated YOLO traffic data
const roads = [
  { name: "Neftçilər prospekti", fromPoint: "Sahil", toPoint: "Bayıl", distanceKm: 3.5, vehicleCount: 87, coverage: 38.2, status: "HEAVY", aiResult: "87 vehicles avg (heavy)" },
  { name: "Babək prospekti", fromPoint: "Memar Əcəmi", toPoint: "İçərişəhər", distanceKm: 7.6, vehicleCount: 62, coverage: 28.5, status: "HEAVY", aiResult: "62 vehicles avg (heavy)" },
  { name: "Tbilisi prospekti", fromPoint: "20 Yanvar", toPoint: "Nərimanov", distanceKm: 10.1, vehicleCount: 34, coverage: 15.3, status: "NORMAL", aiResult: "34 vehicles avg (normal)" },
  { name: "Z.Bünyadov prospekti", fromPoint: "Koroğlu", toPoint: "Həzi Aslanov", distanceKm: 15.2, vehicleCount: 12, coverage: 5.8, status: "FREE_FLOW", aiResult: "12 vehicles avg (free flow)" },
  { name: "Heydər Əliyev prospekti", fromPoint: "Dənizkənarı", toPoint: "Həzi Aslanov", distanceKm: 12.5, vehicleCount: 105, coverage: 48.7, status: "CONGESTED", aiResult: "105 vehicles avg (congested)" },
  { name: "Əziz Əliyev küçəsi", fromPoint: "Neftçilər pr.", toPoint: "Bünyadov pr.", distanceKm: 4.2, vehicleCount: 45, coverage: 22.1, status: "NORMAL", aiResult: "45 vehicles avg (normal)" },
  { name: "Mikayıl Müşfiq küçəsi", fromPoint: "Neftçilər pr.", toPoint: "Bünyadov pr.", distanceKm: 5.8, vehicleCount: 28, coverage: 12.4, status: "NORMAL", aiResult: "28 vehicles avg (normal)" },
  { name: "Moskva prospekti", fromPoint: "Nərimanov", toPoint: "Gənclik", distanceKm: 5.8, vehicleCount: 53, coverage: 26.3, status: "HEAVY", aiResult: "53 vehicles avg (heavy)" },
  { name: "Nobel prospekti", fromPoint: "Koroğlu", toPoint: "Neftçilər", distanceKm: 6.4, vehicleCount: 19, coverage: 8.7, status: "FREE_FLOW", aiResult: "19 vehicles avg (free flow)" },
  { name: "Xətai prospekti", fromPoint: "28 May", toPoint: "Xətai", distanceKm: 4.0, vehicleCount: 41, coverage: 18.9, status: "NORMAL", aiResult: "41 vehicles avg (normal)" },
];

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

  // Delete old roads and re-create with traffic data
  await prisma.road.deleteMany({});
  for (const road of roads) {
    await prisma.road.create({ data: road });
  }
  console.log(`Seeded ${roads.length} roads with traffic data.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
