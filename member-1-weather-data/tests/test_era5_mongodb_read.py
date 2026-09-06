import asyncio

from app.database.mongodb import mongodb


async def main():
    await mongodb.connect()

    try:
        database = mongodb.get_database()
        collection = database["era5_weather"]

        record = await collection.find_one(
            {
                "source": "era5",
                "latitude": 20.2961,
                "longitude": 85.8245,
            },
            sort=[("observed_at", -1)],
        )

        if record is None:
            print("NO ERA5 RECORD FOUND")
            return

        print("ERA5 RECORD FOUND")
        print("Latitude:", record.get("latitude"))
        print("Longitude:", record.get("longitude"))
        print("Observed At:", record.get("observed_at"))
        print("Temperature:", record.get("temperature"))
        print("Dewpoint:", record.get("dewpoint"))
        print("Surface Pressure:", record.get("surface_pressure"))
        print("Wind Speed:", record.get("wind_speed"))
        print("Wind Direction:", record.get("wind_direction"))
        print("Precipitation:", record.get("precipitation"))
        print("Source:", record.get("source"))

    finally:
        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())