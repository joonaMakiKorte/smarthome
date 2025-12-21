import os
import random
import asyncio
import logging
import struct
from datetime import datetime, timezone
from app.schemas import SensorData
from dotenv import load_dotenv
from bleak import BleakScanner

error_logger = logging.getLogger("uvicorn.error")
info_logger = logging.getLogger("uvicorn.info")

class RuuviSensor:
    def __init__(self, mac_address: str):
        """Interfaces with a real RuuviTag using Bleak."""
        self.mac_target = mac_address.upper()
        self._queue = asyncio.Queue()
        self.running = False
        self._scanner = None

        # Default Ruuvi Manufacturer ID
        self.RUUVI_MANUFACTURER_ID = 0x0499

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
                # Put into the async queue for the generator to pick up
                self._queue.put_nowait(parsed_data)
        except Exception:
            return # Quit gracefully
            
    async def stream_data(self):
        """Async generator that yields scanned BLE packets."""
        self.running = True
        self._scanner = BleakScanner(self._detection_callback)
        info_logger.info(f"Starting BLE scan for {self.mac_target}...")
    
        try:
            await self._scanner.start()
            while self.running:
                try:
                    # Wait for data from callback queue with a timeout to check if stopped running
                    packet = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    yield packet
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            info_logger.info("BLE scanning cancelled.")
        finally:
            await self._scanner.stop()
            info_logger.info("BLE Scanner stopped.")

    def stop(self):
        self.running = False

class MockRuuviSensor:
    def __init__(self, mac_address: str = "AA:BB:CC:DD:EE:FF"):
        """Simulates a RuuviTag sensor."""
        self.mac = mac_address
        
        # Initialize base values
        self._temp = 0.0
        self._hum = 45.0  
        self._pres = 1013.0 # standard atmospheric pressure
        self._batt = 3050  # fresh battery (mV)
        
        self.running = False

    def _random_walk(self, current_val, step_size, min_val, max_val, decimal_places=2):
        """Apply a small step to current value to mimic a stochastic process"""
        if random.random() > 0.95:
            return current_val # Randomly skip change (approx one in 20th)

        # Up of down
        step = random.uniform(-step_size, step_size)

        # Random scaling
        scale_p = random.random()
        step *= 3 if scale_p > 0.98 else 2 if scale_p > 0.95 else 1

        new_val = current_val + step

        # Ensure we stay within physical limits
        new_val = max(min_val, min(new_val, max_val))
        return round(new_val, decimal_places)

    async def stream_data(self, interval: float = 0.2):
        """Async generator that yields a new data packet continuously based on the previous state."""
        self.running = True

        info_logger.info(f"Starting scan for Mock Ruuvi Sensor")
        while self.running:
            # Apply random walk to temperature, humidity and pressure
            self._temp = self._random_walk(self._temp, step_size=0.1, min_val=-35, max_val=35)
            self._hum = self._random_walk(self._hum, step_size=0.5, min_val=0, max_val=100)
            self._pres = self._random_walk(self._pres, step_size=0.05, min_val=950, max_val=1050)
            
            # Simulate slow battery drain
            if random.random() > 0.98: 
                self._batt -= 1
                
            # Simulate RSSI fluctuation
            rssi_val = random.randint(-90, -55)

            packet = SensorData(
                mac=self.mac,
                humidity=self._hum,
                temperature=self._temp,
                pressure=self._pres,
                battery=self._batt,
                rssi=rssi_val,
                timestamp=datetime.now(timezone.utc)
            )

            yield packet

            # Non-blocking sleep allowing other services to run
            await asyncio.sleep(interval)

    def stop(self):
        self.running = False

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
        
        info_logger.info(f"Initializing Ruuvi Sensor: {ruuvi_mac}")
        _sensor_instance = RuuviSensor(mac_address=ruuvi_mac)
    else:
        info_logger.info("Initializing Mock Ruuvi Sensor")
        _sensor_instance = MockRuuviSensor()
        
    return _sensor_instance
