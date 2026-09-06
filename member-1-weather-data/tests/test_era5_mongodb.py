import asyncio

from app.era5.ingestion import ERA5IngestionService
from app.database.mongodb import mongodb
from app.core.dependencies import weather_repository


async def main():
    await mongodb.connect()

    try:
        service = ERA5IngestionService()

        records = await service.ingest(
            latitude=20.2961,
            longitude=85.8245,
            date="2026-08-20",
            output_path="data/era5_mongodb_test.nc",
        )

        print("INGESTED RECORDS:", len(records))

        saved = await weather_repository.save_era5(records)
        print("SAVED TO MONGODB:", saved)

        database = mongodb.get_database()
        collection = database["era5_weather"]

        count = await collection.count_documents(
            {
                "source": "era5",
                "latitude": 20.2961,
                "longitude": 85.8245,
            }
        )

        print("MONGODB RECORD COUNT:", count)

    finally:
        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())