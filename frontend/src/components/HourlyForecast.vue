<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import openweatherService from '../services/openweatherService';
import type { HourlyWeather } from '../types';

// State 
const forecast = ref<HourlyWeather[]>([]);
const isLoading = ref(false);
const timerId = ref<ReturnType<typeof setTimeout> | null>(null);

const scrollContainer = ref<HTMLElement | null>(null);
let isDown = false;
let startX = 0;
let scrollLeft = 0;


// --- Data Fetching ---

// Fetch HOURLY forecast (scheduled)
const fetchForecast = async() => {
  try {
    const hourlyForecast = await openweatherService.getHourlyWeather();

    // Check if the api returned fresh data
    const now = new Date();
    now.setMinutes(0, 0, 0);
    const currentHour = now.getHours();
    const firstSlotDate = new Date(hourlyForecast[0].timestamp);
    const firstSlotHour = firstSlotDate.getHours();

    const isMidnight = currentHour === 0 && firstSlotHour === 23 // Consider edge case (midnight)
    const isStale = firstSlotHour < currentHour && !isMidnight;

    if (isStale) {
      const currentHourTimestamp = now.getTime();
        // Filter out old timestamps if stale
        const cleanForecast = hourlyForecast.filter(item => {
        const itemTime = new Date(item.timestamp).getTime();
        return itemTime >= currentHourTimestamp;
      });
      forecast.value = cleanForecast;
      scheduleNextFetch(true); // Schedule as 'retry'
    } else {
      forecast.value = hourlyForecast;
      scheduleNextFetch(false);
    }
  } catch (err) {
    console.log("Polling failed", err);
    scheduleNextFetch(true); // Schedule fetch
  }
};

// --- Helpers ---

// Schedule NEXT FETCH
const scheduleNextFetch = (isRetry: boolean) => {
  if (timerId.value) clearTimeout(timerId.value);

  if (isRetry) {
    timerId.value = setTimeout(fetchForecast, 60000); // Scheduled to next minute
    return;
  }

  // Set next fetch to next hour
  const now = new Date();
  const nextTarget = new Date(now);
  nextTarget.setHours(now.getHours() + 1, 0, 0, 0);

  // Push schedule to next hour if already over buffer
  if (nextTarget.getTime() <= now.getTime()) {
     nextTarget.setHours(nextTarget.getHours() + 1);
  }

  const msUntilTarget = nextTarget.getTime() - now.getTime();
  timerId.value = setTimeout(fetchForecast, msUntilTarget);
};

// --- Lifecycle ---

onMounted(() => {
  isLoading.value = true;
  fetchForecast().finally(() => isLoading.value = false);
});

onUnmounted(() => {
  if (timerId.value) clearTimeout(timerId.value);
});

// --- UI Helpers ---

const formatTime = (isoString: string, index: number) => {
  if (index === 0) return 'Now';
  const date = new Date(isoString);
  return date.toLocaleTimeString([], { hour: '2-digit'}).replace(' ', '');
}

const onMouseDown = (e: MouseEvent) => {
  if (!scrollContainer.value) return;
  isDown = true;
  scrollContainer.value.classList.add('active');
  startX = e.pageX - scrollContainer.value.offsetLeft;
  scrollLeft = scrollContainer.value.scrollLeft;
};

const onMouseLeave = () => {
  isDown = false;
  scrollContainer.value?.classList.remove('active');
};

const onMouseUp = () => {
  isDown = false;
  scrollContainer.value?.classList.remove('active');
};

const onMouseMove = (e: MouseEvent) => {
  if (!isDown || !scrollContainer.value) return;
  e.preventDefault();
  const x = e.pageX - scrollContainer.value.offsetLeft;
  const walk = (x - startX) * 2; // Scroll speed multiplier
  scrollContainer.value.scrollLeft = scrollLeft - walk;
};

</script>

<template>
  <div class="w-full h-full bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex flex-col justify-center relative overflow-hidden select-none group">
    
    <div v-if="isLoading && forecast.length === 0" class="absolute inset-0 flex items-center justify-center text-slate-500 animate-pulse text-xl">
      Loading...
    </div>

    <div 
      v-else
      ref="scrollContainer"
      class="flex overflow-x-auto space-x-12 px-8 py-4 hide-scrollbar cursor-grab active:cursor-grabbing items-center h-full"
      @mousedown="onMouseDown"
      @mouseleave="onMouseLeave"
      @mouseup="onMouseUp"
      @mousemove="onMouseMove"
    >
      <div 
        v-for="(item, index) in forecast" 
        :key="index"
        class="flex flex-col items-center justify-between flex-shrink-0 min-w-[6rem] h-[80%]"
      >
        <span class="text-lg font-semibold text-slate-400/90">
          {{ formatTime(item.timestamp, index) }}
        </span>

        <div class="h-16 w-16 flex items-center justify-center my-2">
          <img 
            :src="item.icon_url" 
            :alt="item.icon_code"
            class="h-full w-full object-contain filter drop-shadow-md opacity-90" 
            draggable="false" 
          />
        </div>

        <span class="text-3xl font-bold text-slate-200">
          {{ Math.round(parseFloat(item.temperature)) }}&deg;
        </span>
      </div>
    </div>
    
    <div class="pointer-events-none absolute inset-y-0 left-0 w-12 bg-gradient-to-r from-slate-900/90 to-transparent rounded-l-3xl"></div>
    <div class="pointer-events-none absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-slate-900/90 to-transparent rounded-r-3xl"></div>
  </div>
</template>

<style scoped>
.hide-scrollbar {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
.hide-scrollbar::-webkit-scrollbar {
  display: none; /* Chrome, Safari and Opera */
}
</style>
