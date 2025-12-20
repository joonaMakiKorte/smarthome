import asyncio
import psutil
import subprocess
import re
from app.schemas import NetworkHealth
import os
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

# IP config
load_dotenv()
LAN_IP = os.getenv("ROUTER_IP")
WAN_IP = os.getenv("INTERNET_TARGET")

class HealthCache:
    """Single Source of Truth Cache holding network health status in memory"""
    def __init__(self):
        self._cache: Optional[NetworkHealth] = None
        self._last_updated: Optional[datetime] = None
        self._lock = asyncio.Lock() # Prevent read/write conflicts

    @property
    def cache(self) -> Optional[NetworkHealth]:
        return self._cache

    def is_empty(self) -> bool:
        return not self._cache and not self._last_updated
    
    async def replace_cache(self, status: NetworkHealth):
        async with self._lock:
            self._cache = status
            self._last_updated = datetime.now()

# Init global cache
health_cache = HealthCache()

# --- Public functions ---

async def run_network_status_scan():
    """Runs network performance metric scans and updates cache"""
    # Get WiFi status
    iwconfig_result = await _get_wifi_status()

    # Run WAN burst (5 packets) and LAN single check concurrently
    wan_result, lan_result = await asyncio.gather(
        _perform_ping(WAN_IP, count=5),
        _perform_ping(LAN_IP, count=1)
    )

    # Get server traffic
    speed_result = await _measure_server_traffic()

    # Unpack results
    is_connected, ssid, signal_quality = iwconfig_result
    wan_lat, wan_loss = wan_result
    lan_lat, _ = lan_result # Ignore LAN packet loss
    tx_speed, rx_speed = speed_result

    # Cache
    await health_cache.replace_cache(
        NetworkHealth(
            connected=is_connected,
            ssid=ssid,
            signal_quality=signal_quality,
            wan_latency_ms=wan_lat,
            lan_latency_ms=lan_lat,
            packet_loss=wan_loss,
            server_upload_mbps=round(tx_speed, 2),
            server_download_mbps=round(rx_speed,2)
        )
    )

# --- Helpers ---

async def _get_wifi_status():
    """Get WiFi SSID and link quality."""
    connected = False
    ssid = "N/A"
    signal_quality = 0
    try: 
        # Run iwconfig to get WiFi details
        output = subprocess.check_output("iwconfig wlan0", shell=True).decode()
        
        # Parse SSID
        ssid_match = re.search(r'ESSID:"([^"]+)"', output)
        if ssid_match:
            connected = True
            ssid = ssid_match.group(1)

        # Parse Link Quality (e.g., Link Quality=58/70)
        quality_match = re.search(r'Link Quality=(\d+)/(\d+)', output)
        if quality_match:
            current = int(quality_match.group(1))
            total = int(quality_match.group(2))
            signal_quality = int((current / total) * 100)
    
    except Exception as e:
        print(f"Error reading WiFi stats: {e}")
    
    return connected, ssid, signal_quality

async def _perform_ping(host: str, count=5):
    """Pings host 'count' times. Returns latency and packet loss."""
    try:
        # 1s interval for safety
        process = await asyncio.create_subprocess_exec(
            "ping", "-c", str(count), "-q", host,  # -q = quiet output
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        output = stdout.decode()
        
        # Parse packet loss
        loss_match = re.search(r"(\d+)% packet loss", output)
        packet_loss = float(loss_match.group(1)) if loss_match else 100.0

        # Parse latency
        latency = None
        if packet_loss < 100:
            rtt_match = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", output)
            if rtt_match:
                latency = float(rtt_match.group(1))

        return latency, packet_loss

    except Exception as e:
        print(f"Ping Error: {e}")
        return None, 100.0
    
async def _measure_server_traffic():
    # Get current counters
    net1 = psutil.net_io_counters()
    await asyncio.sleep(0.5) 
    net2 = psutil.net_io_counters()

    # Calculate Speed in Mbps
    # (Bytes2 - Bytes1) * 8 bits / 1024 / 1024 / 0.5 seconds
    tx_speed = (net2.bytes_sent - net1.bytes_sent) * 8 / 1_000_000 / 0.5 # Upload
    rx_speed = (net2.bytes_recv - net1.bytes_recv) * 8 / 1_000_000 / 0.5 # Download

    return tx_speed, rx_speed
