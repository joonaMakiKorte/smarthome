import random
import time
from datetime import datetime, timezone
from app.schemas import SensorData

class MockRuuviSensor:
    def __init__(self, mac_address: str = "AA:BB:CC:DD:EE:FF"):
        self.mac = mac_address
        
        # Initialize base values
        self._temp = 0.0
        self._hum = 45.0  
        self._pres = 1013.0 # standard atmospheric pressure
        self._batt = 3050  # fresh battery (mV)
        
    def _random_walk(self, current_val, step_size, min_val, max_val, decimal_places=2):
        """Apply a small step to current value to mimic a stochastic process"""
        if random.random() > 0.95: return # Randomly skip change (approx one in 20th)

        # Up of down
        step = random.uniform(-step_size, step_size)

        # Random scaling
        scale_p = random.random()
        step *= 3 if scale_p > 0.98 else 2 if scale_p > 0.95 else 1

        new_val = current_val + step

        # Ensure we stay within physical limits
        new_val = max(min_val, min(new_val, max_val))
        return round(new_val, decimal_places)

    def read(self) -> SensorData:
        """Generates a new data packet based on the previous state."""
        # Apply random walk to temperature, humidity and pressure
        self._temp = self._random_walk(self._temp, step_size=0.1, min_val=-35, max_val=35)
        self._hum = self._random_walk(self._hum, step_size=0.5, min_val=0, max_val=100)
        self._pres = self._random_walk(self._pres, step_size=0.05, min_val=950, max_val=1050)
        
        # Simulate slow battery drain
        if random.random() > 0.98: 
            self._batt -= 1
            
        # Simulate RSSI fluctuation
        rssi_val = random.randint(-90, -55)

        return SensorData(
            mac=self.mac,
            humidity=self._hum,
            temperature=self._temp,
            pressure=self._pres,
            battery=self._batt,
            rssi=rssi_val,
            time=datetime.now(timezone.utc)
        )