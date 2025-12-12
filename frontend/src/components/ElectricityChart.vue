<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import type { ElectricityPriceInterval, AvgElectricityPrice } from '../types';
import electricityService from '../services/electricityService';

// Types
type Interval = '15min' | '1h'
type ViewDay = 'today' | 'tomorrow'

// Colors
const COLORS = {
  low: '#84cc16',    // Lime-500
  medium: '#eab308', // Yellow-500
  high: '#f97316',   // Orange-500
  avgLine: '#22d3ee' // Cyan-400
};

// State
const cache = ref<{ [key in Interval]?: ElectricityPriceInterval[] }>({});
const avgPrice = ref<number | null>(null);
const selectedInterval = ref<Interval>('15min');
const selectedDay = ref<ViewDay>('today');
const isLoading = ref(false);

const now = ref(new Date());
const canvasRef = ref<HTMLCanvasElement | null>(null);
let resizeObserver: ResizeObserver | null = null;
let pollInterval: ReturnType<typeof setInterval> | null = null;

// --- Data Fetching ---

const fetchData = async (interval: Interval, force: boolean = false) => {
  // Return if cache found and is not forced update
  if (!force && cache.value[interval]) return;
  try {
    isLoading.value = true;
    const data = await electricityService.getElectricityPrices(interval);
    cache.value[interval] = data;
  } catch (err) {
    console.error("Full fetch failed", err);
  } finally {
    isLoading.value = false;
  }
};

const fetchAvg = async () => {
  try {
    const data: AvgElectricityPrice = await electricityService.getElectricityAvg();
    if (data && typeof data.average_price === 'number') {
      avgPrice.value = data.average_price;
    }
  } catch (err) {
    console.error("Avg fetch failed", err);
  }
}

// --- Chart Helpers ---

// Define if we have enough data to display tomorrows prices
const isFullDay = (count: number, interval: Interval) => {
  const minRequired = interval === '1h' ? 12 : 48; 
  return count >= minRequired;
};

// Get the data for the specific day currently selected
const displayedData = computed(() => {
  const interval = selectedInterval.value;
  const allData = cache.value[selectedInterval.value] || [];
  if (!allData.length) return [];

  const targetDate = new Date(now.value);
  if (selectedDay.value === 'tomorrow') {
    targetDate.setDate(targetDate.getDate() + 1);
  }

  const targetDateStr = targetDate.toLocaleDateString();
  const dayData = allData.filter(d => new Date(d.time).toLocaleDateString() === targetDateStr);

  // Do we have enough data for tomorrow?
  if (selectedDay.value === 'tomorrow') {
    if (!isFullDay(dayData.length, interval)) return [];
  }

  return dayData;
});

// Global Max Price
const globalMaxPrice = computed(() => {
  const allData = cache.value[selectedInterval.value] || [];
  const defaults = [10]; // Minimum scale base

  // Filter out any data points from yesterday or before
  const todayDate = new Date(now.value)
  const relevantData = allData.filter(d => new Date(d.time) >= todayDate);

  if (relevantData.length) {
    defaults.push(...relevantData.map(d => d.price));
  }
  if (avgPrice.value) {
    defaults.push(avgPrice.value);
  }
  return Math.max(Math.max(...defaults), 5) * 1.1;
});

const hasTomorrowData = computed(() => {
  const interval = selectedInterval.value;
  const allData = cache.value[interval] || [];
  if (!allData.length) return false;

  const tomorrow = new Date(now.value);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toDateString();
  
  const tomorrowData = allData.filter(d => new Date(d.time).toDateString() === tomorrowStr);
  
  // Only enambe 'Tomorrow' button if we have the full dataset
  return isFullDay(tomorrowData.length, interval);
});

const isPendingRelease = computed(() => {
    const h = now.value.getHours();
    // It's after 14:00, before 16:00, and we still don't have data
    return h >= 14 && h < 16 && !hasTomorrowData.value;
});

const currentPrice = computed(() => {
  const data = cache.value['15min'];
  if (!data || !data.length) return null;

  const nowTime = now.value.getTime();
  return data.find(d => {
    const tStart = new Date(d.time).getTime();
    const tEnd = tStart + (15 * 60000);
    return nowTime >= tStart && nowTime < tEnd;
  });
});

// --- Drawing ---

const drawChart = () => {
  const canvas = canvasRef.value;
  const data = displayedData.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;

  ctx.clearRect(0, 0, W, H);

  if (!data.length) return;

  // Scaling
  const maxVal = globalMaxPrice.value;
  const barWidth = (W / data.length);
  const gap = data.length > 50 ? 0.5 : 1;
  
  // Draw Bars
  data.forEach((item, index) => {
    const price = Math.max(0, item.price);
    const barHeight = (price / maxVal) * H;
    const x = index * barWidth;
    const y = H - barHeight;

    let color = COLORS.low;
    if (price >= 5) color = COLORS.medium;
    if (price >= 10) color = COLORS.high;

    ctx.fillStyle = color;
    ctx.fillRect(x, y, Math.max(barWidth - gap, 1), barHeight);
  });

  // Draw Average Price Line (Horizontal) 
  if (avgPrice.value !== null) {
    const avgY = H - ((avgPrice.value / maxVal) * H);
    
    ctx.beginPath();
    ctx.strokeStyle = COLORS.avgLine;
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]); // Dashed
    ctx.moveTo(0, avgY);
    ctx.lineTo(W, avgY);
    ctx.stroke();
    
    ctx.setLineDash([]); // Reset
  }

  // Draw Current Time Line (Vertical)
  if (selectedDay.value === 'today') {
    const currentIndex = data.findIndex(d => {
      const t = new Date(d.time);
      return t.getHours() === now.value.getHours() && 
             (selectedInterval.value === '1h' || Math.floor(t.getMinutes() / 15) === Math.floor(now.value.getMinutes() / 15));
    });

    if (currentIndex !== -1) {
      const x = currentIndex * barWidth;
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
  }
};

const getPriceColorClass = (price: number) => {
  if (price < 5) return 'text-lime-400';
  if (price < 10) return 'text-yellow-400';
  return 'text-red-400';
};

// --- Lifecycle ---

const startPolling = () => {
  pollInterval = setInterval(() => {
    const current = new Date();
    const prevMinute = now.value.getMinutes();
    const hour = current.getHours();
    
    // Day Change
    if (current.getDate() !== now.value.getDate()) {
      cache.value = {}; 
      selectedDay.value = 'today';
      fetchData('1h', true);
      fetchData('15min', true);
      fetchAvg();
    }

    // Poll Average Price (Every 15 mins)
    if (current.getMinutes() % 15 === 0 && current.getMinutes() !== prevMinute) {
      fetchAvg();
    }

    // Check for new data during 14:00-16:00
    if (hour >= 14 && hour < 16 && !hasTomorrowData.value && !isLoading.value) {
      fetchData('1h', true); 
      fetchData('15min', true);
    }

    now.value = current;
  }, 60000); 
};

watch([displayedData, selectedInterval, selectedDay, now, avgPrice], () => nextTick(drawChart));

onMounted(() => {
  fetchData('1h');
  fetchData('15min');
  fetchAvg();
  startPolling();
  
  if (canvasRef.value) {
    resizeObserver = new ResizeObserver(() => drawChart());
    resizeObserver.observe(canvasRef.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect();
  if (pollInterval) clearInterval(pollInterval);
});
</script>

<template>
  <div class="w-full h-full bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex flex-col p-5 relative overflow-hidden group select-none">
    
    <div class="flex justify-between items-center mb-4 z-10">
      
      <div class="flex bg-slate-800/80 p-1 rounded-lg border border-slate-700/50 h-fit">
        <button 
          @click="selectedDay = 'today'"
          class="w-28 py-1.5 rounded-md text-base font-bold transition-all duration-200 flex justify-center"
          :class="selectedDay === 'today' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
        >
          Today
        </button>
        
        <button 
          @click="selectedDay = 'tomorrow'"
          :disabled="!hasTomorrowData"
          class="w-28 py-1.5 rounded-md text-base font-bold transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
          :class="selectedDay === 'tomorrow' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
        >
          <span v-if="isPendingRelease" class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-yellow-500"></span>
          </span>
          {{ isPendingRelease ? 'Pending...' : 'Tomorrow' }}
        </button>
      </div>

      <div v-if="currentPrice" class="flex items-baseline gap-2">
        <span class="text-sm text-slate-500 uppercase font-bold tracking-wider">Current</span>
        
        <div class="flex items-baseline gap-1">
          <span 
            class="text-4xl font-black tracking-tight"
            :class="getPriceColorClass(currentPrice.price)"
          >
            {{ currentPrice.price.toFixed(2) }}
          </span>
          <span class="text-sm text-slate-500 font-medium">c/kWh</span>
        </div>
      </div>
      <div v-else class="flex items-center opacity-0">
          <span class="text-4xl">-</span>
      </div>

      <div class="flex items-center space-x-2 bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700/30 h-fit">
        <label class="cursor-pointer group">
          <input type="radio" value="1h" v-model="selectedInterval" @change="fetchData('1h')" class="peer hidden">
          <span class="text-base font-mono px-2 py-0.5 rounded transition-colors text-slate-500 peer-checked:text-blue-300 peer-checked:bg-slate-700/50">1H</span>
        </label>
        <span class="text-slate-700 text-sm">|</span>
        <label class="cursor-pointer group">
          <input type="radio" value="15min" v-model="selectedInterval" @change="fetchData('15min')" class="peer hidden">
          <span class="text-base font-mono px-2 py-0.5 rounded transition-colors text-slate-500 peer-checked:text-blue-300 peer-checked:bg-slate-700/50">15M</span>
        </label>
      </div>
    </div>

    <div class="flex flex-1 min-h-0 w-full gap-3">
      
      <div class="flex flex-col justify-between items-end text-sm text-slate-500 font-mono py-1 w-10 flex-shrink-0">
        <span>{{ Math.round(globalMaxPrice) }}</span>
        <span>{{ Math.round(globalMaxPrice * 0.75) }}</span>
        <span>{{ Math.round(globalMaxPrice * 0.5) }}</span>
        <span>{{ Math.round(globalMaxPrice * 0.25) }}</span>
        <span>0</span>
      </div>

      <div class="flex flex-col flex-1 min-w-0 relative">
        <div class="flex-1 w-full min-h-0 relative">
          <canvas ref="canvasRef" class="w-full h-full block"></canvas>

          <div v-if="isLoading && displayedData.length === 0" class="absolute inset-0 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm rounded-lg">
            <span class="text-slate-400 animate-pulse text-base">Loading...</span>
          </div>
          <div v-if="!isLoading && displayedData.length === 0" class="absolute inset-0 flex items-center justify-center text-slate-500 text-base">
            No Data
          </div>
        </div>

        <div class="flex justify-between w-full mt-2 text-sm text-slate-600 font-mono px-0.5">
          <span>00</span>
          <span>06</span>
          <span>12</span>
          <span>18</span>
          <span>23</span>
        </div>
      </div>
    </div>
    
  </div>
</template>
