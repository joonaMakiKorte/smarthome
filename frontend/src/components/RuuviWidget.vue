<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import type { SensorData } from '../types';

// State
const isConnected = ref(false);
const latestData = ref<SensorData | null>(null);
const displayData = ref<SensorData | null>(null); 
let socket: WebSocket | null = null;
let throttleTimer: ReturnType<typeof setTimeout> | null = null;

// --- WebSocket ---

const connect = () => {
  const url = import.meta.env.VITE_RUUVI_URL;
  if (!url) { console.error("Missing VITE_RUUVI_URL"); return; }
  
  socket = new WebSocket(url);

  socket.onopen = () => {
    isConnected.value = true;
  };

  socket.onmessage = (event) => {
    try {
      const parsed: SensorData = JSON.parse(event.data);
      latestData.value = parsed;
      
      // Throttle (0.2Hz)
      if (!throttleTimer) {
        displayData.value = parsed;
        throttleTimer = setTimeout(() => {
          if (latestData.value) displayData.value = latestData.value;
          throttleTimer = null;
        }, 5000);
      }
    } catch (e) {
      console.error('Parse error', e);
    }
  };

  socket.onclose = () => {
    isConnected.value = false;
  };
};

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

onMounted(() => {
  connect();
});

onUnmounted(() => {
  if (socket) socket.close();
});

</script>
