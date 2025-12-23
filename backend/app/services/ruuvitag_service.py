import os
import random
import asyncio
import logging
import struct
from datetime import datetime, timezone
from app.schemas import SensorData
from dotenv import load_dotenv
from bleak import BleakScanner
from typing import Optional

error_logger = logging.getLogger("uvicorn.error")
info_logger = logging.getLogger("uvicorn.info")

class RuuviSensor:
    def __init__(self, mac_address: str):
        """Interfaces with a real RuuviTag using Bleak."""
        self.mac_target = mac_address.upper()
        self._scanner = None
        self._latest_data: Optional[SensorData] = None

        # Default Ruuvi Manufacturer ID
        self.RUUVI_MANUFACTURER_ID = 0x0499

    @property
    def latest_data(self) -> Optional[SensorData]:
        """Read-only access to the latest known data."""
        return self._latest_data

    def _decode_data(self, raw_data: bytes, rssi: int, device_mac: str) -> SensorData:
        """Decodes Ruuvi Raw Format 5 (RAWv2)"""
        if len(raw_data) < 24:
            return None
        
        # Format 5 check
        data_format = raw_data[0]
        if data_format != 0x05:
            return None
        
        # Unpack raw bytes
        # Format:   Format(1) Temp(2) Hum(2) Pres(2) AccX(2) AccY(2) AccZ(2) Power(2) Move(1) Seq(2) MAC(6)
        payload = raw_data[1:]

        (temp_raw, hum_raw, pres_raw, acc_x, acc_y, acc_z, 
         power_info, move_count, seq, mac_raw) = struct.unpack('>hHHhhhHBH6s', payload)
        
        temperature = temp_raw * 0.005 # Temperature in 0.005 degrees
        humidity = hum_raw * 0.0025 # Humidity in 0.0025%
        pressure = (pres_raw + 50000) / 100.0 # Pressure with offset of -50000 Pa, convert to hPa
        battery_voltage = (power_info >> 5) + 1600 # First 11 bits are voltage (mV) + 1600

        return SensorData(
            mac=device_mac,
            humidity=round(humidity, 2),
            temperature=round(temperature, 2),
            pressure=round(pressure, 2),
            battery=battery_voltage,
            rssi=rssi,
            timestamp=datetime.now(timezone.utc)
        )
    
    def _detection_callback(self, device, advertisement_data):
        """Callback triggered by BleakScanner when a packet is found."""
        # Filter by MAC address
        if device.address.upper() != self.mac_target:
            return
        
        if self.RUUVI_MANUFACTURER_ID not in advertisement_data.manufacturer_data:
            return
        
        raw_data = advertisement_data.manufacturer_data[self.RUUVI_MANUFACTURER_ID]

        # Decode
        try:
            parsed_data = self._decode_data(raw_data, advertisement_data.rssi, device.address)
            if parsed_data:
                self._latest_data = parsed_data
        except Exception as e:
            error_logger.error(f"Error decoding BLE packet: {e}")
            
    async def start_scanning(self):
        """Starts the scanner ONCE."""
        if self._scanner: return # Already running
        
        info_logger.info(f"STARTUP: Starting Global BLE Scanner for {self.mac_target}...")
        self._scanner = BleakScanner(self._detection_callback)
        await self._scanner.start()

    async def stop_scanning(self):
        """Stops the scanner."""
        if self._scanner:
            info_logger.info("SHUTDOWN: Stopping BLE Scanner...")
            await self._scanner.stop()
            self._scanner = None

class MockRuuviSensor:
    def __init__(self, mac_address: str = "AA:BB:CC:DD:EE:FF"):
        """Simulates a RuuviTag sensor."""
        self.mac = mac_address
        self._temp = 20.0
        self._hum = 45.0
        self._pres = 1013.0
        self._batt = 3000
        self._latest_data = None
        self._running = False
        self._task = None

    @property
    def latest_data(self) -> SensorData | None:
        return self._latest_data

    def _random_walk(self, val, step, min_v, max_v):
        """Helper to simulate sensor drift"""
        change = random.uniform(-step, step)
        return max(min_v, min(val + change, max_v))

    async def _simulation_loop(self):
        """Background task that updates data every 1s."""
        while self._running:
            self._temp = self._random_walk(self._temp, 0.1, -30, 50)
            self._hum = self._random_walk(self._hum, 0.5, 0, 100)
            self._pres = self._random_walk(self._pres, 0.1, 950, 1050)
            
            # Update the shared state
            self._latest_data = SensorData(
                mac=self.mac,
                temperature=round(self._temp, 2),
                humidity=round(self._hum, 2),
                pressure=round(self._pres, 2),
                battery=self._batt,
                rssi=random.randint(-90, -60),
                timestamp=datetime.now(timezone.utc)
            )
            await asyncio.sleep(1) # Update rate

    async def start_scanning(self):
        info_logger.info("STARTUP: Starting Mock Sensor Loop...")
        self._running = True
        # Start the simulation loop in the background
        self._task = asyncio.create_task(self._simulation_loop())

    async def stop_scanning(self):
        info_logger.info("SHUTDOWN: Stopping Mock Sensor Loop...")
        self._running = False
        if self._task:
            await self._task

# Global singleton instance of the sensor
_sensor_instance = None

def get_sensor_service():
    """Return a singleton instance"""
    global _sensor_instance
    if _sensor_instance:
        return _sensor_instance

    load_dotenv()
    is_production = os.getenv("APP_ENV", "development") == "production"
    
    if is_production:
        ruuvi_mac = os.getenv("RUUVI_MAC")
        _sensor_instance = RuuviSensor(mac_address=ruuvi_mac)
    else:
        _sensor_instance = MockRuuviSensor()
        
    return _sensor_instance
