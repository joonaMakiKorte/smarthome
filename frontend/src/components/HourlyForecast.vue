<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import openweatherService from '../services/openweatherService';
import type { HourlyWeather } from '../types';

// State 
const forecast = ref<HourlyWeather[]>([]);
const isLoading = ref(false);
const timerId = ref<ReturnType<typeof setTimeout> | null>(null);
const currentHour = ref(new Date().getHours());

const scrollContainer = ref<HTMLElement | null>(null);
let isDown = false;
let startX = 0;
let scrollLeft = 0;


// --- Data Fetching ---

// Fetch HOURLY forecast (scheduled)
const fetchForecast = async () => {
  try {
    const hourlyForecast = await openweatherService.getHourlyWeather();

    // Filter out any old entries
    const now = new Date();
    const currentHourTimestamp = now.setMinutes(0, 0, 0);
    const cleanForecast = hourlyForecast.filter(item => {
      return new Date(item.timestamp).getTime() >= currentHourTimestamp;
    });

    forecast.value = cleanForecast; // Update UI immediately

    // Stale check -> ping api until data is fresh, meaning no filtering
    const isStale = hourlyForecast.length !== cleanForecast.length;
    if (isStale) {
      scheduleRetry();
    } else {
      scheduleNextHourTick();
    }

    scheduleNextHourTick();

  } catch (err) {
    console.error("Polling failed", err);
    scheduleRetry(); // Schedule retry in 1 min
  }
};

// --- Helpers ---

// Updates forecast to match current hour and schedule API call
const handleHourChange = () => {
  // Update UI Theme Hour
  currentHour.value = new Date().getHours();

  // Filter out any old entries
  if (forecast.value.length > 0) {
    const now = new Date();
    const currentHourTimestamp = now.setMinutes(0, 0, 0);
    forecast.value = forecast.value.filter(item => {
      return new Date(item.timestamp).getTime() >= currentHourTimestamp;
    });
  }

  // Fetch in one minute
  if (timerId.value) clearTimeout(timerId.value);
  timerId.value = setTimeout(() => {
    fetchForecast();
  }, 60000); 
};

// Schedule handleHourChange function exetution to next hour tick
const scheduleNextHourTick = () => {
  if (timerId.value) clearTimeout(timerId.value);

  const now = new Date();
  const nextTarget = new Date(now);
  
  // Set target to next hour: XX:00:00
  nextTarget.setHours(now.getHours() + 1, 0, 0, 0);

  // Safety check -> jump to next hour
  if (nextTarget.getTime() <= now.getTime()) {
      nextTarget.setHours(nextTarget.getHours() + 1);
  }

  const msUntilTarget = nextTarget.getTime() - now.getTime();
  timerId.value = setTimeout(handleHourChange, msUntilTarget);
};

// Simple retry helper
const scheduleRetry = () => {
  if (timerId.value) clearTimeout(timerId.value);
  timerId.value = setTimeout(() => {
    fetchForecast();
  }, 60000); // 1 min timeout
};

// --- UI Helpers ---

const themeClasses = computed(() => {
  const h = currentHour.value;

  // Night (21:00 - 05:00) - Deep Slate/Black
  if (h >= 21 || h <= 5) {
    return {
      container: 'bg-gradient-to-br from-slate-900 via-slate-800 to-gray-900',
      text: 'text-slate-200',
      subText: 'text-slate-400',
      overlayLeft: 'from-slate-900/90',
      overlayRight: 'from-gray-900/90'
    };
  }
  
  // Morning (06:00 - 10:00) - Light Blue/Cyan
  if (h >= 6 && h <= 10) {
    return {
      container: 'bg-gradient-to-br from-sky-400 via-sky-300 to-blue-300',
      text: 'text-white',
      subText: 'text-blue-50',
      overlayLeft: 'from-sky-400/90',
      overlayRight: 'from-blue-300/90'
    };
  }

  // Day (11:00 - 16:00) - Bright Blue
  if (h >= 11 && h <= 16) {
    return {
      container: 'bg-gradient-to-br from-blue-500 via-blue-400 to-blue-400',
      text: 'text-white',
      subText: 'text-blue-100',
      overlayLeft: 'from-blue-500/90',
      overlayRight: 'from-blue-400/90'
    };
  }

  // Evening/Sunset (17:00 - 20:00) - Indigo/Purple
  return {
    container: 'bg-gradient-to-br from-indigo-500 via-purple-600 to-indigo-800',
    text: 'text-white',
    subText: 'text-indigo-200',
    overlayLeft: 'from-indigo-500/90',
    overlayRight: 'from-indigo-800/90'
  };
});

// --- Lifecycle ---

onMounted(() => {
  isLoading.value = true;
  currentHour.value = new Date().getHours();
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
  <div 
    class="w-full h-full rounded-3xl border border-white/10 flex flex-col justify-center relative overflow-hidden select-none group transition-colors duration-1000 ease-in-out"
    :class="themeClasses.container"
  >
    
    <div v-if="isLoading && forecast.length === 0" class="absolute inset-0 flex items-center justify-center text-white/70 animate-pulse text-xl">
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
        <span class="text-lg font-semibold transition-colors duration-700" :class="themeClasses.subText">
          {{ formatTime(item.timestamp, index) }}
        </span>

        <div class="h-16 w-16 flex items-center justify-center my-2">
          <img 
            :src="item.icon_url" 
            :alt="item.icon_code"
            class="h-full w-full object-contain filter drop-shadow-md opacity-90 transform group-hover:scale-110 transition-transform duration-300" 
            draggable="false" 
          />
        </div>

        <span class="text-3xl font-bold transition-colors duration-700" :class="themeClasses.text">
          {{ Math.round(parseFloat(item.temperature)) }}&deg;
        </span>
      </div>
    </div>
    
    <div 
      class="pointer-events-none absolute inset-y-0 left-0 w-12 bg-gradient-to-r to-transparent rounded-l-3xl transition-colors duration-1000"
      :class="themeClasses.overlayLeft"
    ></div>
    <div 
      class="pointer-events-none absolute inset-y-0 right-0 w-12 bg-gradient-to-l to-transparent rounded-r-3xl transition-colors duration-1000"
      :class="themeClasses.overlayRight"
    ></div>
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
