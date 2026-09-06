from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Protocol

from app.database.mongodb import MongoDB


class WeatherRepository(Protocol):
    async def save_current(
        self,
        weather: Any,
    ) -> str:
        ...

    async def save_forecast(
        self,
        forecast: Any,
    ) -> str:
        ...

    async def save_historical(
        self,
        historical: Any,
    ) -> str:
        ...

    async def save_gfs(
        self,
        weather: Any,
    ) -> str:
        ...

    async def save_era5(
        self,
        records: list[Any],
    ) -> int:
        ...

    async def save_mqtt_weather(
        self,
        weather: Any,
    ) -> str:
        ...

    async def save_satellite_weather(
        self,
        weather: Any,
    ) -> str:
        ...

    async def get_latest_era5(
        self,
        latitude: float,
        longitude: float,
    ):
        ...

    async def get_latest_mqtt(
        self,
        latitude: float,
        longitude: float,
    ):
        ...

    async def get_latest_satellite(
        self,
        latitude: float,
        longitude: float,
    ):
        ...


class MongoWeatherRepository:
    CURRENT_COLLECTION = "current_weather"
    FORECAST_COLLECTION = "weather_forecasts"
    HISTORICAL_COLLECTION = "historical_weather"
    GFS_COLLECTION = "gfs_weather"
    ERA5_COLLECTION = "era5_weather"
    MQTT_COLLECTION = "mqtt_weather"
    SATELLITE_COLLECTION = "satellite_weather"
    IMD_COLLECTION = "imd_weather"
    

    def __init__(
        self,
        mongodb: MongoDB,
    ):
        self.mongodb = mongodb

    @staticmethod
    def _dump(model: Any) -> dict:
        if hasattr(model, "model_dump"):
            return model.model_dump(
                mode="json"
            )

        if isinstance(model, dict):
            return model.copy()

        raise TypeError(
            "Unsupported weather model type: "
            f"{type(model).__name__}"
        )

    # ---------------------------------------------------------
    # CURRENT WEATHER
    # ---------------------------------------------------------

    async def save_current(
        self,
        weather: Any,
    ) -> str:
        document = self._dump(weather)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.CURRENT_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # FORECAST
    # ---------------------------------------------------------

    async def save_forecast(
        self,
        forecast: Any,
    ) -> str:
        document = self._dump(forecast)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.FORECAST_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # HISTORICAL
    # ---------------------------------------------------------

    async def save_historical(
        self,
        historical: Any,
    ) -> str:
        document = self._dump(historical)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.HISTORICAL_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # GFS
    # ---------------------------------------------------------

    async def save_gfs(
        self,
        weather: Any,
    ) -> str:
        document = self._dump(weather)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.GFS_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # ERA5
    # ---------------------------------------------------------

    async def save_era5(
        self,
        records: list[Any],
    ) -> int:

        if not records:
            return 0

        documents = []

        for record in records:
            document = self._dump(record)

            document["updated_at"] = datetime.now(
                UTC
            )

            documents.append(document)

        result = await self.mongodb.get_database()[
            self.ERA5_COLLECTION
        ].insert_many(documents)

        return len(result.inserted_ids)

    # ---------------------------------------------------------
    # MQTT
    # ---------------------------------------------------------

    async def save_mqtt_weather(
        self,
        weather: Any,
    ) -> str:

        document = self._dump(weather)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.MQTT_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # SATELLITE
    # ---------------------------------------------------------

    async def save_satellite_weather(
        self,
        weather: Any,
    ) -> str:

        document = self._dump(weather)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.SATELLITE_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)
    
    async def save_imd_weather(
        self,
        weather: Any,
    ) -> str:
        document = self._dump(weather)

        document["updated_at"] = datetime.now(
            UTC
        )

        result = await self.mongodb.get_database()[
            self.IMD_COLLECTION
        ].insert_one(document)

        return str(result.inserted_id)
    async def get_latest_imd(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.IMD_COLLECTION
        ].find_one(
            {
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("timestamp", -1)
            ],
        )
    # ---------------------------------------------------------
    # CURRENT QUERY
    # ---------------------------------------------------------

    async def get_current(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.CURRENT_COLLECTION
        ].find_one(
            {
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("updated_at", -1)
            ],
        )

    # ---------------------------------------------------------
    # FORECAST QUERY
    # ---------------------------------------------------------

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.FORECAST_COLLECTION
        ].find_one(
            {
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("updated_at", -1)
            ],
        )

    # ---------------------------------------------------------
    # HISTORICAL QUERY
    # ---------------------------------------------------------

    async def get_historical(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.HISTORICAL_COLLECTION
        ].find_one(
            {
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("updated_at", -1)
            ],
        )

    # ---------------------------------------------------------
    # GFS QUERY
    # ---------------------------------------------------------

    async def get_latest_gfs(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.GFS_COLLECTION
        ].find_one(
            {
                "latitude": {
                    "$gte": latitude - 0.5,
                    "$lte": latitude + 0.5,
                },
                "longitude": {
                    "$gte": longitude - 0.5,
                    "$lte": longitude + 0.5,
                },
            },
            sort=[
                ("valid_at", -1)
            ],
        )

    # ---------------------------------------------------------
    # ERA5 QUERY
    # ---------------------------------------------------------

    async def get_latest_era5(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.ERA5_COLLECTION
        ].find_one(
            {
                "source": "era5",
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("observed_at", -1)
            ],
        )

    # ---------------------------------------------------------
    # MQTT QUERY
    # ---------------------------------------------------------

    async def get_latest_mqtt(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.MQTT_COLLECTION
        ].find_one(
            {
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("updated_at", -1)
            ],
        )

    # ---------------------------------------------------------
    # SATELLITE QUERY
    # ---------------------------------------------------------

    async def get_latest_satellite(
        self,
        latitude: float,
        longitude: float,
    ):
        return await self.mongodb.get_database()[
            self.SATELLITE_COLLECTION
        ].find_one(
            {
                "latitude": latitude,
                "longitude": longitude,
            },
            sort=[
                ("timestamp", -1)
            ],
        )

    # ---------------------------------------------------------
    # INDEXES
    # ---------------------------------------------------------

    async def ensure_indexes(self):
        database = self.mongodb.get_database()

        # GFS indexes
        
        await database[
            self.GFS_COLLECTION
        ].create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("valid_at", -1),
            ]
        )

        await database[
            self.GFS_COLLECTION
        ].create_index(
            [
                ("source", 1),
                ("valid_at", -1),
            ]
        )

        # ERA5 indexes
        await database[
            self.ERA5_COLLECTION
        ].create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("observed_at", -1),
            ]
        )

        await database[
            self.ERA5_COLLECTION
        ].create_index(
            [
                ("source", 1),
                ("observed_at", -1),
            ]
        )

        # MQTT indexes
        await database[
            self.MQTT_COLLECTION
        ].create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("updated_at", -1),
            ]
        )

        await database[
            self.MQTT_COLLECTION
        ].create_index(
            [
                ("source", 1),
                ("updated_at", -1),
            ]
        )

        # Satellite indexes
        await database[
            self.SATELLITE_COLLECTION
        ].create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("timestamp", -1),
            ]
        )

        await database[
            self.SATELLITE_COLLECTION
        ].create_index(
            [
                ("source", 1),
                ("timestamp", -1),
            ]
        )
        await database[
            self.IMD_COLLECTION
        ].create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("timestamp", -1),
            ]
        )

        await database[
            self.IMD_COLLECTION
        ].create_index(
            [
                ("source", 1),
                ("timestamp", -1),
            ]
        )
    async def create_indexes(self):
        """
        Backward-compatible alias used by
        the existing test suite.
        """
        await self.ensure_indexes()