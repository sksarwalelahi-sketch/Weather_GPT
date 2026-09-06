import asyncio

from app.gfs.client import GFSClient
from app.gfs.ingestion import GFSIngestion


async def main():
    ingestion = GFSIngestion()

    try:
        result = await ingestion.ingest_grib2(
            file_path="data/gfs_live_06z.grib2",
            latitude=20.2961,
            longitude=85.8245,
        )

        print("\nREAL GFS RESULT")
        print("================")

        print(
            result.model_dump(
                mode="json"
            )
        )

    finally:
        await ingestion.close()


if __name__ == "__main__":
    asyncio.run(main())