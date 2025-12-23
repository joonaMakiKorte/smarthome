# Smart Home Dashboard
A modern, containerized personal information hub built for Raspberry Pi. This full-stack application aggregates real-time hardware sensor data, 
external APIs, and local network metrics into a unified interface designed for a wall-mounted kiosk display.

## About 
This project is a custom dashboard designed to run 24/7 on a **Raspberry Pi 4 Model B**. It acts as a central home server that collects data via Bluetooth (BLE)
and various REST APIs, visualizing it on a **Lenovo Tab** running **Fully Kiosk Browser**.

The architecture is fully **Dockerized** for seamless deployment. Development occurs on a local machine, where images are built for ARM64 architecture and pushed to
Docker Hub. The Raspberry Pi automatically pulls and runs the containers in a headless production environment using **Watchtower** for automated updates.

### Dashboard Snapshot
<img width="1439" height="752" alt="smarthome" src="https://github.com/user-attachments/assets/fda9f37b-70ae-42a7-9c1d-6ab332a3c47b" />

## Tech Stack

### Hardware Setup
- **Server:** Raspberry Pi 4 Model B (Raspberry Pi OS Lite, Docker Engine).
- **Sensor:** RuuviTag Pro (Environmental Sensor communicating via Bluetooth Low Energy).
- **Display:** Lenovo Tab (Wall-mounted tablet via Fully Kiosk Browser).

### Backend
- **Python 3.11 & FastAPI:** High-performance async API with Uvicorn.
- **Bleak:** Asynchronous Bluetooth Low Energy scanner for hardware integration.
- **SQLModel**: ORM interactions with a persistent SQLite database.
- **APScheduler & Asyncache:** Robust background task scheduling and caching.
- **WebSockets:** Real-time data streaming to the client.

### Frontend
- **Vue 3 (TypeScript):** Reactive UI with Composition API.
- **Vite:** Next-generation frontend tooling.
- **Nginx:** Production-grade web server and reverse proxy.

## Dashboard Features & Widgets
The dashboard integrates distinct data sources into a single responsive view:
- **Real-Time Environment:** Streaming of Temperature, Humidity, Air Pressure, and RSSI from a local [**RuuviTag Pro**](https://ruuvi.com/ruuvitag-pro/) sensor via Bluetooth (BLE).
- **Weather Forecast:** Current local conditions and forecast via [**OpenWeatherMap**](https://openweathermap.org/api/one-call-3).
- **Electricity Prices:** Real-time spot prices for the Finnish market via [**Pörssisähkö.net**](https://porssisahko.net/).
- **Public Transport:** Live departure times for local stops (Tampere) via the [**Digitansit (Nysse)**](https://portal-api.digitransit.fi/) API.
- **Stock Market:** Watchlist tracking and market indices via [**Twelve Data**](https://twelvedata.com/docs#overview).
- **Todo List:** Personal task synchronization via the [**Todoist API**](https://github.com/Doist/todoist-api-python).
- **Network Status:** Monitoring of network performance metrics using `psutil` and `iwconfig`.

## Getting Started
### Prerequisites
- **Development:** Python 3.11+, Node.js 18+, Docker Desktop (optional for building).
- **Production:** Raspberry Pi 4 (or newer) with Docker Engine installed.

### Local Development Installation
**1. Clone The Repository**
```bash
git clone https://github.com/joonaMakiKorte/smarthome.git
cd smarthome
```

**2. Backend Setup**
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (including dev tools like pytest)
pip install -r requirements-dev.txt

# Create .env file
cp .env.example .env
# (Edit .env with your API keys)

# Run the API server with hot-reload
uvicorn app.main:app --reload
```
*The backend API docs will be available at `http://localhost:8000/docs`*

**3. Frontend Setup**
```bash
cd frontend

# Install dependencies
chmod +x install_frontend.sh
./install_frontend.sh

# Run the development server
npm run dev
```
*The UI will be available at `http://localhost:5173`*

### Production Deployment (Raspberry Pi)
The production environment runs entirely on Docker. The workflow involves building multi-architecture images on your PC, pushing them to Docker Hub,
and pulling them onto the Raspberry Pi.

**1. Build & Push (From PC)**
```bash
# Login to Docker Hub
# Login to Docker Hub
docker login

# Build and Push Backend
docker buildx build --platform linux/arm64 -t your_username/dashboard_backend:latest ./backend --push

# Build and Push Frontend
docker buildx build --platform linux/arm64 -t your_username/dashboard_frontend:latest ./frontend --push
```

**2. Deploy to Raspberry Pi**
SSH into your Raspberry Pi and set up the project folder. You do not need the source codeo n the Pi, only the configuration files.
1. **Create Project Directory:**
   ```bash
   mkdir ~/smarthome
   cd ~/smarthome
   ```
2. **Create Configuration Files:**
   - Create a `.env` file with your production API keys.
   - Create a `docker-compose.yml` file (use the production version, referencing the images you pushed).
3. **Launch the Application:**
   ```bash
   # Pull the latest images from Hub
   docker compose pull
  
   # Start the containers in background mode
   docker compose up -d
   ```

### Environment Variables
Create a `.env` file in the `backend/` directory (for dev) or project root (for prod) with the following keys:
```Ini
# API keys
TODOIST_API_KEY=...
OPENWEATHER_API_KEY=...
TWELVEDATA_API_KEY=...
DIGITRANSIT_API_KEY=...

# Weather location coordinates
LAT=...
LON=...

# Network settings
ROUTER_IP=... # LAN address
INTERNET_TARGET=1.1.1.1 # WAN address, Cloudflare DNS for default
WIFI_INTERFACE=wlan0 # WiFi interface of the device, wlan0 for the Pi

RUUVI_MAC=... # Your sensor MAC address

APP_ENV=development # IMPORTANT, set to 'production' on Pi
```

### Production `docker-compose.yml`
Create the following `docker-compose.yml` file in the project root for Pi:
```YAML
services:
  backend:
    image: your_username/smarthome_backend:latest
    container_name: smarthome_backend
    restart: unless-stopped
    network_mode: host
    privileged: true
    volumes:
      - /var/run/dbus:/var/run/dbus
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - DBUS_SYSTEM_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket
      - PYTHONUNBUFFERED=1
      - DB_FILE=data/database.db

  frontend:
    image: your_username/smarthome_frontend:latest
    container_name: smarthome_frontend
    restart: unless-stopped
    network_mode: host

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    # Check for updates every hour (3600 seconds)
    command: --interval 3600

networks:
  default:
    driver: bridge
```

## Testing
The project uses **pytest** to validate the logic of each widget independently, mocking API responses to ensure stability without relying on external services during CI/CD.
- To disable caching during unit tests, create the following `pytest.ini` file in the `backend/` folder:
   ```Ini
   [pytest]
   env = 
       TESTING=True
   ```
   
```bash
# Example: running all unit tests
cd backend
pytest
```

## License
Distributed under the MIT License. See `LICENSE` for more information.
