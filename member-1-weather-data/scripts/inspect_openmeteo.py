import asyncio

from app.openmeteo.client import OpenMeteoClient


async def main():
    client = OpenMeteoClient()

    try:
        weather = await client.get_weather(
            latitude=20.2961,
            longitude=85.8245,
        )

        print(weather)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())