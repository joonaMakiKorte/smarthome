<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import type { SensorData } from '../types';

// State
const isConnected = ref(false);
const latestData = ref<SensorData | null>(null);
const displayData = ref<SensorData | null>(null); 

// Rolling average buffers
const tempHistory = ref<number[]>([]);
const humidityHistory = ref<number[]>([]);
const pressureHistory = ref<number[]>([]);

let socket: WebSocket | null = null;
let throttleTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let watchdogTimer: ReturnType<typeof setTimeout> | null = null;
let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
let healthCheckTimer: ReturnType<typeof setInterval> | null = null;

const lastMessageAt = ref(Date.now());

// --- WebSocket ---

// Automatically detect the host
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;
const URL = `${protocol}//${host}/api/ruuvitag/ws`;

const THROTTLE_MS = 2000; // Update UI every 2 seconds
const WATCHDOG_MS = 45000; // If silence for 45s, assume dead
const RECONNECT_MS = 3000; // Try reconnecting every 3s
const HEARTBEAT_MS = 20000; // Send a ping every 20s to keep WiFi radio active
const HEALTHCHECK_MS = 10000; // Health check every 10s

const resetWatchdog = () => {
  if (watchdogTimer) clearTimeout(watchdogTimer);
  watchdogTimer = setTimeout(() => {
    console.warn("Watchdog timeout: Connection stale. Force closing.");
    socket?.close(4000, "Watchdog timeout");
  }, WATCHDOG_MS);
};

const startHeartbeat = () => {
  if (heartbeatTimer) clearInterval(heartbeatTimer);
  heartbeatTimer = setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) {
      // Send data to keep Android WiFi radio from sleeping
      socket.send('ping'); 
    }
  }, HEARTBEAT_MS);
};

const startHealthCheck = () => {
  if (healthCheckTimer) clearInterval(healthCheckTimer);
  healthCheckTimer = setInterval(() => {
    if (Date.now() - lastMessageAt.value > WATCHDOG_MS) {
      console.warn('Health check failed — no data received');
      socket?.close(4001, 'Health check timeout');
    }
  }, HEALTHCHECK_MS);
};

const connect = () => {
  // Cleanup
  reconnectTimer && clearTimeout(reconnectTimer);
  reconnectTimer = null;

  if (socket) {
    socket.onopen = null;
    socket.onmessage = null;
    socket.onclose = null;
    socket.onerror = null;
    socket.close();
    socket = null;
  }

  // Update State
  isConnected.value = false;
  tempHistory.value.length = 0;
  humidityHistory.value.length = 0;
  pressureHistory.value.length = 0;

  // New Connection
  socket = new WebSocket(URL);

  socket.onopen = () => {
    console.log('WebSocket connected');
    isConnected.value = true;
    lastMessageAt.value = Date.now();
    resetWatchdog();
    startHeartbeat();
    startHealthCheck();
  };

  socket.onmessage = (event) => {
    lastMessageAt.value = Date.now();
    resetWatchdog();

    if (event.data === 'pong') return;

    try {
      const parsed: SensorData = JSON.parse(event.data);
      latestData.value = parsed;

      // Update History Buffers 
      updateHistory(tempHistory, parsed.temperature);
      updateHistory(humidityHistory, parsed.humidity);
      updateHistory(pressureHistory, parsed.pressure);
      
      // Throttle (1Hz)
      if (!throttleTimer) {
        displayData.value = parsed;
        throttleTimer = setTimeout(() => {
          if (latestData.value) displayData.value = latestData.value;
          throttleTimer = null;
        }, THROTTLE_MS);
      }
    } catch (e) {
      console.warn('Parse error', e);
    }
  };

  socket.onclose = (e) => {
    console.warn('WebSocket closed', e.code, e.reason);
    isConnected.value = false;

    watchdogTimer && clearTimeout(watchdogTimer);
    heartbeatTimer && clearInterval(heartbeatTimer);
    healthCheckTimer && clearInterval(healthCheckTimer);

    if (!reconnectTimer) {
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connect();
      }, RECONNECT_MS);
    }
  };

  socket.onerror = (err) => {
    console.error("WebSocket error", err);
    socket?.close();
  };
};

// --- Helpers ---

const HISTORY_SIZE = 50; // Ensure smoother data, slower reaction
const updateHistory = (historyRef: any, newValue: number) => {
  historyRef.value.push(newValue);
  if (historyRef.value.length > HISTORY_SIZE) {
    historyRef.value.shift();
  }
};

const calculateAverage = (arr: number[]) => {
  if (arr.length === 0) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
};

const averagedTemperature = computed(() => {
  return calculateAverage(tempHistory.value).toFixed(1);
});

const averagedHumidity = computed(() => {
  return calculateAverage(humidityHistory.value).toFixed(1);
});

const averagedPressure = computed(() => {
  return calculateAverage(pressureHistory.value).toFixed(0);
});

// --- UI Helpers ---

// CR2477: Max ~3000mV, Min ~2000mV (approximate linear curve)
const batteryPercentage = computed(() => {
  if (!displayData.value) return '0';
  const mv = displayData.value.battery;
  const max = 3000;
  const min = 2000;
  
  let pct = ((mv - min) / (max - min)) * 100;
  return Math.min(Math.max(pct, 0), 100).toFixed(0);
});

// Defines signal thresholds for the bars (4 bars = > -60dBm, etc.)
const RSSI_THRESHOLDS = [-85, -75, -65, -55];
const signalBars = computed(() => {
  if (!displayData.value) return 0;
  const dbm = displayData.value.rssi;
  let bars = 0;
  if (dbm > RSSI_THRESHOLDS[3]) bars = 4;
  else if (dbm > RSSI_THRESHOLDS[2]) bars = 3;
  else if (dbm > RSSI_THRESHOLDS[1]) bars = 2;
  else if (dbm > RSSI_THRESHOLDS[0]) bars = 1;
  return bars;
});

// --- Lifecycle ---

const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      connect();
    } else {
      resetWatchdog();
    }
  }
};

onMounted(() => {
  connect();
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  reconnectTimer && clearTimeout(reconnectTimer);
  watchdogTimer && clearTimeout(watchdogTimer);
  heartbeatTimer && clearInterval(heartbeatTimer);
  healthCheckTimer && clearInterval(healthCheckTimer);
  socket?.close();
  socket = null;
});

</script>

<template>
  <div class="h-full w-full bg-black rounded-3xl border border-slate-700 relative overflow-hidden flex flex-col p-8 shadow-2xl">
    
    <div v-if="!displayData" class="flex-1 flex flex-col items-center justify-center text-slate-400 animate-pulse gap-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
      <span class="text-lg font-bold tracking-widest">CONNECTING...</span>
    </div>

    <div v-else class="flex flex-col h-full justify-between z-10">
      
      <div class="flex justify-between items-center w-full">
        
        <div class="text-slate-500 font-bold text-xl uppercase tracking-widest">
          RuuviTag
        </div>

        <div class="flex items-center gap-6">
          
          <div class="flex items-center" :title="`Signal: ${displayData.rssi} dBm`">
            <div class="flex items-end gap-1 h-6">
              <div 
                v-for="bar in 4" 
                :key="bar"
                class="w-2 rounded-sm transition-colors duration-500"
                :class="[
                  bar <= signalBars ? 'bg-green-400' : 'bg-slate-800',
                  bar === 1 ? 'h-2' : bar === 2 ? 'h-3' : bar === 3 ? 'h-5' : 'h-6'
                ]"
              ></div>
            </div>
          </div>

          <div class="flex items-center gap-3 text-slate-200">
             <span class="text-sm font-mono font-bold">{{ batteryPercentage }}%</span>
             <div class="relative w-8 h-4 border-2 border-slate-400 rounded-sm p-0.5">
               <div class="absolute -right-1.5 top-1/2 -translate-y-1/2 w-1 h-2 bg-slate-400 rounded-r-sm"></div>
               <div 
                  class="h-full rounded-[1px] transition-all duration-500"
                  :class="{
                    'bg-green-400': parseInt(batteryPercentage) > 50,
                    'bg-yellow-400': parseInt(batteryPercentage) <= 50 && parseInt(batteryPercentage) > 20,
                    'bg-red-500': parseInt(batteryPercentage) <= 20
                  }"
                  :style="{ width: `${batteryPercentage}%` }"
               ></div>
             </div>
          </div>

        </div>
      </div>

      <div class="flex items-end justify-between flex-1 w-full">
        
        <div class="flex flex-col justify-end -mb-2">
          <div class="flex items-center gap-2 text-slate-500 text-xl font-bold uppercase tracking-wider pl-2 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="M12 11.1V4"/></svg>
            Temperature
          </div>
          <div class="text-[8rem] lg:text-[10rem] font-black text-white tracking-tighter leading-[0.75] -ml-2">
            {{ averagedTemperature }}<span class="text-6xl text-slate-600 font-light ml-2">°C</span>
          </div>
        </div>

        <div class="flex flex-col items-end gap-10">
          
          <div class="flex flex-col items-end">
            <div class="flex items-center gap-2 text-slate-400 text-sm font-bold uppercase tracking-wider mb-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-5-9-7-15-2 6-7 13-7 15a7 7 0 0 0 7 7Z"/></svg>
              Humidity
            </div>
            <div class="text-4xl font-bold text-slate-200">
              {{ averagedHumidity }} <span class="text-xl text-slate-500 font-medium">%</span>
            </div>
          </div>

          <div class="flex flex-col items-end">
             <div class="flex items-center gap-2 text-slate-400 text-sm font-bold uppercase tracking-wider mb-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M3 12h18"/><circle cx="12" cy="12" r="9" /></svg>
              Pressure
            </div>
            <div class="text-4xl font-bold text-slate-200">
              {{ averagedPressure }} <span class="text-xl text-slate-500 font-medium">hPa</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>