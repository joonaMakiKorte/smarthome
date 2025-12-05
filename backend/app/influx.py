import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.schemas import SensorData

load_dotenv()

URL = os.getenv("INFLUX_URL", "http://localhost:8086")
TOKEN = os.getenv("INFLUX_TOKEN", "my-token")
ORG = os.getenv("INFLUX_ORG", "my-org")
BUCKET = os.getenv("INFLUX_BUCKET", "home_sensors")

class InfluxService:
    def __init__(self):
        self.client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def _write_sync(self, point):
        """Internal synchronous write method."""
        try:
            self.write_api.write(bucket=BUCKET, org=ORG, record=point)
        except Exception as e:
            print(f"InfluxDB Write Error: {e}")

    async def write_sensor_data(self, data: SensorData):
        """
        Non-blocking method to write RuuviTag data.
        """
        point = (
            Point("ruuvitag")
            .tag("mac", data.mac)
            .field("temperature", float(data.temperature))
            .field("humidity", float(data.humidity))
            .field("pressure", float(data.pressure))
            .field("battery", int(data.battery))
            .field("rssi", int(data.rssi))
            .time(data.timestamp)
        )

        # Run the blocking write operation in a separate thread
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_sync, point)

    async def write_weather_api_context(self, api_data: dict):
        """
        Non-blocking method to write Public Weather Context.
        """
        point = (
            Point("weather_context")
            .tag("source", "openweather")
            .field("temp_regional", float(api_data["main"]["temp"]))
            .field("wind_speed", float(api_data["wind"]["speed"]))
            .field("clouds", int(api_data["clouds"]["all"]))
            .time(datetime.now(tz=timezone.utc))
        )
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_sync, point)

    def close(self):
        self.client.close()

# Singleton instance
influx_service = InfluxService()
