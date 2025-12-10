<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import type { ElectricityPriceInterval, AvgElectricityPrice } from '../types';
import electricityService from '../services/electricityService';

// Types
type Interval = '15min' | '1h'
type ViewDay = 'today' | 'tomorrow'

// Colors for electricity price chart
const COLORS = {
  low: '#84cc16',    // Lime-500 (Cheap)
  medium: '#eab308', // Yellow-500 (Moderate)
  high: '#f97316',   // Orange-500 (Expensive)
};

// State
const cache = ref<{ [key in Interval]?: ElectricityPriceInterval[] }>({});
const selectedInterval = ref<Interval>('15min');
const selectedDay = ref<ViewDay>('today');
const isLoading = ref(false);

const canvasRef = ref<HTMLCanvasElement | null>(null);
let resizeObserver: ResizeObserver | null = null;

// --- Data Fetching ---

// Fetch ALL valid data (Today + Tomorrow)
const fetchData = async (interval: Interval) => {
  // Check cache for data
  if (cache.value[interval]) return;
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

// --- Chart Helpers ---

// Data for the currently selected day
const displayedData = computed(() => {
  const allData = cache.value[selectedInterval.value] || [];
  if (!allData.length) return [];

  const now = new Date();
  const targetDate = new Date(now);
  if (selectedDay.value === 'tomorrow') {
    targetDate.setDate(targetDate.getDate() + 1);
  }
  const targetDateStr = targetDate.toLocaleDateString();

  return allData.filter(d => new Date(d.time).toLocaleDateString() === targetDateStr);
});

// Global Max Price (For consistent scaling across days)
const globalMaxPrice = computed(() => {
  const allData = cache.value[selectedInterval.value] || [];
  if (!allData.length) return 10; // Default fallback
  // Get max from ALL data (Today + Tomorrow) to keep scale consistent
  return Math.max(Math.max(...allData.map(d => d.price)), 5) * 1.1; 
});

const hasTomorrowData = computed(() => {
  const allData = cache.value[selectedInterval.value] || [];
  if (!allData.length) return false;
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return allData.some(d => new Date(d.time).toDateString() === tomorrow.toDateString());
});

// Find Current Price (Always uses 15min data for accuracy)
const currentPrice = computed(() => {
  const data = cache.value['15min'];
  if (!data || !data.length) return null;

  const now = new Date();
  // Find the interval that covers the current time
  return data.find(d => {
    const t = new Date(d.time);
    const end = new Date(t.getTime() + 15 * 60000); // +15 mins
    return now >= t && now < end;
  });
});

// --- Drawing ---

const drawChart = () => {
  const canvas = canvasRef.value;
  const data = displayedData.value;
  if (!canvas || !data.length) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;

  // Clear
  ctx.clearRect(0, 0, W, H);

  // Scaling: Use the Unified Global Max
  const maxVal = globalMaxPrice.value;
  const barWidth = (W / data.length); // Full width per slot
  const gap = data.length > 50 ? 0.5 : 1; // Smaller gap for 15min view
  
  // Bars
  data.forEach((item, index) => {
    const price = Math.max(0, item.price);
    const barHeight = (price / maxVal) * H;
    const x = index * barWidth;
    const y = H - barHeight;

    let color = COLORS.low;
    if (price >= 5) color = COLORS.medium;
    if (price >= 10) color = COLORS.high;

    ctx.fillStyle = color;
    // Draw bar with gap
    ctx.fillRect(x, y, Math.max(barWidth - gap, 1), barHeight);
  });

  // Current Time Line (Only for Today)
  if (selectedDay.value === 'today') {
    const now = new Date();
    const currentIndex = data.findIndex(d => {
      const t = new Date(d.time);
      return t.getHours() === now.getHours() && 
             (selectedInterval.value === '1h' || Math.floor(t.getMinutes() / 15) === Math.floor(now.getMinutes() / 15));
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

// Helper for color class
const getPriceColorClass = (price: number) => {
  if (price < 5) return 'text-lime-400';
  if (price < 10) return 'text-yellow-400';
  return 'text-red-400';
};

// --- Lifecycle ---

watch([displayedData, selectedInterval, selectedDay], () => nextTick(drawChart));

onMounted(() => {
  fetchData('1h');
  fetchData('15min'); // Prefetch both for smoothness
  
  if (canvasRef.value) {
    resizeObserver = new ResizeObserver(() => drawChart());
    resizeObserver.observe(canvasRef.value);
  }
});

onUnmounted(() => resizeObserver?.disconnect());
</script>

<template>
  <div class="w-full h-full bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex flex-col p-4 relative overflow-hidden group select-none">
    
    <div class="flex justify-between items-start mb-3 z-10">
      
      <div class="flex bg-slate-800/80 p-0.5 rounded-lg border border-slate-700/50 h-fit">
        <button 
          @click="selectedDay = 'today'"
          class="px-3 py-1 rounded-md text-xs font-bold transition-all duration-200"
          :class="selectedDay === 'today' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
        >
          Today
        </button>
        <button 
          @click="selectedDay = 'tomorrow'"
          :disabled="!hasTomorrowData"
          class="px-3 py-1 rounded-md text-xs font-bold transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
          :class="selectedDay === 'tomorrow' ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
        >
          Tmrw
        </button>
      </div>

      <div v-if="currentPrice" class="flex flex-col items-center leading-none -mt-1">
        <span class="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Current</span>
        <div class="flex items-baseline space-x-0.5">
          <span 
            class="text-2xl font-black tracking-tight"
            :class="getPriceColorClass(currentPrice.price)"
          >
            {{ currentPrice.price.toFixed(1) }}
          </span>
          <span class="text-[10px] text-slate-500 font-medium">c/kWh</span>
        </div>
      </div>
      <div v-else class="flex flex-col items-center leading-none -mt-1 opacity-0">
         <span class="text-2xl">-</span>
      </div>


      <div class="flex items-center space-x-2 bg-slate-800/50 px-2 py-1 rounded-lg border border-slate-700/30 h-fit">
        <label class="cursor-pointer group">
          <input type="radio" value="1h" v-model="selectedInterval" @change="fetchData('1h')" class="peer hidden">
          <span class="text-xs font-mono px-2 py-0.5 rounded transition-colors text-slate-500 peer-checked:text-blue-300 peer-checked:bg-slate-700/50">1H</span>
        </label>
        <span class="text-slate-700 text-[10px]">|</span>
        <label class="cursor-pointer group">
          <input type="radio" value="15min" v-model="selectedInterval" @change="fetchData('15min')" class="peer hidden">
          <span class="text-xs font-mono px-2 py-0.5 rounded transition-colors text-slate-500 peer-checked:text-blue-300 peer-checked:bg-slate-700/50">15M</span>
        </label>
      </div>
    </div>

    <div class="flex flex-1 min-h-0 w-full space-x-2">
      
      <div class="flex flex-col justify-between items-end text-[10px] text-slate-500 font-mono py-1 w-8 flex-shrink-0">
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
            <span class="text-slate-400 animate-pulse text-xs">Loading...</span>
          </div>
          <div v-if="!isLoading && displayedData.length === 0" class="absolute inset-0 flex items-center justify-center text-slate-500 text-xs">
            No Data
          </div>
        </div>

        <div class="flex justify-between w-full mt-1 text-[10px] text-slate-600 font-mono px-0.5">
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
