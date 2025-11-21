# Smart Home Dashboard - Tech Stack & Architecture

## 1. Development Environment (Local)
*   **OS:** Windows 11 via **WSL2 (Ubuntu 24.04)**
*   **IDE:** Visual Studio Code
*   **VS Code Extensions:**
    *   *Python* (Microsoft)
    *   *Vue - Official* (Vue.js)
    *   *Tailwind CSS IntelliSense*
    *   *Gemini Cli Companion* (Gemini AI)
    *   *Docker*
*   **Languages:**
    *   Python 3.10+ (Backend)
    *   Node.js v20+ (Frontend Tooling - managed via NVM)
*   **Version Control:** Git & GitHub

---

## 2. Backend (The API & Logic)
**Location:** `/backend`
**Framework:** FastAPI (Python)

| Component | Library/Tool | Purpose |
| :--- | :--- | :--- |
| **Core Server** | `fastapi` | The web framework for creating the API. |
| **ASGI Server** | `uvicorn[standard]` | Runs the Python application (lightning fast). |
| **Database ORM** | `sqlmodel` | Interact with the database using Python classes. |
| **Environment** | `python-dotenv` | Load secrets (API keys) from `.env` file. |
| **HTTP Client** | `httpx` | To fetch weather data or call other 3rd party APIs asynchronously. |
| **WebSockets** | `fastapi` (Built-in) | Real-time updates to the tablet (no refresh needed). |

**Future/Hardware Libraries (Phase 2):**
*   `paho-mqtt` (If communicating with Zigbee2MQTT or other devices).
*   `requests` (Alternative simple synchronous HTTP calls).

---

## 3. Frontend (The Dashboard UI)
**Location:** `/frontend`
**Framework:** Vue.js 3 (Composition API + TypeScript)

| Component | Library/Tool | Purpose |
| :--- | :--- | :--- |
| **Build Tool** | `Vite` | Extremely fast build tool (standard for Vue 3). |
| **State Manager** | `Pinia` | Managing global state (Is the light on?) across components. |
| **Styling** | `Tailwind CSS` | Utility-first CSS framework for custom designs. |
| **Icons** | `lucide-vue-next` | Modern, clean icons for your dashboard buttons. |
| **HTTP Client** | `axios` | Fetching data from your FastAPI backend. |
| **Utilities** | `@vueuse/core` | "Swiss Army Knife" for Vue (helpers for WebSockets, Dark mode, etc). |

---

## 4. Database & Storage
**Strategy:** Hybrid (File-based for config, Time-series for logs).

| Type | Technology | Purpose |
| :--- | :--- | :--- |
| **Relational** | **SQLite** | Stores device list, names, settings, and current status. (Zero-config file). |
| **Time-Series** | **InfluxDB** (Docker) | *Future Phase:* Stores historical sensor data for graphs (temp over 24h). |

---

## 5. Deployment (Production on Raspberry Pi)
**Strategy:** Containerized applications.

*   **Docker:** To package the application.
*   **Docker Compose:** To orchestrate running the Backend, Frontend, and Databases simultaneously.
*   **Reverse Proxy (Optional):** `Nginx` (Handles traffic routing for remote access).

---

## 6. Hardware Client
*   **Device:** Lenovo Tab M11 (ZAEH0028SE)
*   **Software:** Fully Kiosk Browser (Android App)
*   **Features:** Camera motion wake, battery protection mode, REST API control.