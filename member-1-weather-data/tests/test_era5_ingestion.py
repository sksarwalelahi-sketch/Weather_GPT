import asyncio

from app.era5.ingestion import ERA5IngestionService


async def main():
    service = ERA5IngestionService()

    results = await service.ingest(
        latitude=20.2961,
        longitude=85.8245,
        date="2026-08-20",
        output_path="data/era5_ingestion_test.nc",
    )

    print("NUMBER OF RECORDS:", len(results))

    for record in results:
        print(record)


if __name__ == "__main__":
    asyncio.run(main())