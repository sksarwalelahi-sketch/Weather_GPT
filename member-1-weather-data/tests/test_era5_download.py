import asyncio
from pathlib import Path

from app.era5.client import ERA5Client


async def main():
    client = ERA5Client()

    output = Path("data/era5_test.nc")

    result = await client.download(
        latitude=20.2961,
        longitude=85.8245,
        date="2026-08-20",
        output_path=output,
    )

    print("ERA5 FILE:", result)
    print("EXISTS:", result.exists())
    print("SIZE BYTES:", result.stat().st_size)


if __name__ == "__main__":
    asyncio.run(main())