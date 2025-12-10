<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useIntervalFn } from '@vueuse/core';
import openweatherService from '../services/openweatherService';
import type { CurrentWeather } from '../types';

// State
const currentWeather = ref<CurrentWeather | null>(null);
const time = ref(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
const date = ref(new Date().toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' }));
const isLoading = ref(false);

// --- Data fetching ---

// Fetch CURRENT weather (polled)
const fetchCurrent = async () => {
  try {
    // Trigger loading spinner on the initial load
    if (!currentWeather.value) isLoading.value = true;

    const current = await openweatherService.getCurrentWeather();
    currentWeather.value = current;
  } catch (err) {
    console.error("Polling failed", err);
  } finally {
    isLoading.value = false;
  }
};

// --- Lifecycle ---

// Update Weather every 10 minutes (600,000 ms)
useIntervalFn(() => {
  fetchCurrent();
}, 600000);

// Update Clock every 1 second
useIntervalFn(() => {
  const now = new Date();
  time.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  date.value = now.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
}, 1000);

// Initial fetch on component mount
onMounted(() => {
  fetchCurrent();
});
</script>

<template>
  <div class="h-full w-full bg-slate-900/50 rounded-3xl border border-slate-800 flex items-center px-6 relative overflow-hidden">
      
    <div class="w-[65%] flex items-center gap-4 border-r border-slate-800/50 pr-4 h-full">
      
      <div v-if="currentWeather" class="flex items-center gap-4">
        <img 
          :src="currentWeather.icon_url" 
          :alt="currentWeather.description"
          class="w-20 h-20 object-contain drop-shadow-sm"
        />
        
        <div class="flex flex-col">
          <span class="text-5xl font-bold text-white leading-none tracking-tighter">
            {{ Math.round(currentWeather.temperature) }}°C
          </span>
          <div class="flex flex-col text-sm text-slate-400 font-medium mt-2 pl-1">
            <span class="capitalize leading-none text-white/90 mb-1">
              {{ currentWeather.description }}
            </span>
            <span class="leading-none text-xs opacity-70">
              Feels like {{ Math.round(currentWeather.temperature_feels_like) }}°
            </span>
          </div>
        </div>
      </div>

      <div v-else class="flex items-center gap-4 animate-pulse opacity-50">
        <div class="w-16 h-16 bg-slate-700 rounded-full"></div>
        <div class="flex flex-col gap-2">
          <div class="w-20 h-8 bg-slate-700 rounded"></div>
          <div class="w-24 h-4 bg-slate-700 rounded"></div>
        </div>
      </div>
    </div>

    <div class="w-[35%] flex flex-col items-end justify-center pl-4 h-full whitespace-nowrap">
      <div class="text-5xl font-bold text-white leading-none tracking-tight">{{ time }}</div>
      <div class="text-lg text-slate-400 uppercase tracking-widest font-medium mt-2">{{ date }}</div>
    </div>

  </div>
</template>
