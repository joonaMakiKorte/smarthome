<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useIntervalFn, useNow } from '@vueuse/core';
import type { StopTimetable, StopWatchlist } from '../types';
import stopService from '../services/stopService';

// State
const stopWatchlist = ref<Record<string, StopWatchlist>>({});
const stopLiveBoards = ref<Record<string, StopTimetable>>({});
const selectedStopId = ref<string | null>(null);
const isLoading = ref(false);

const now = useNow({ interval: 1000 }); // Reactive time updating every second

// --- Data Fetching ---

const fetchWatchlist = async() => {
  try {
    const watchlist = await stopService.getStopWatchlist();
    
    const record: Record<string, StopWatchlist> = {};
    watchlist.forEach(stop => {
      record[stop.gtfs_id] = stop;
    });
    stopWatchlist.value = record;

    // Auto-select first stop if nothing selected
    if (!selectedStopId.value && watchlist.length > 0) {
      selectedStopId.value = watchlist[0].gtfs_id;
    }
  } catch (err) {
    console.error("Fetching watchlist failed", err)
  }
}

const fetchLiveBoards = async() => {
  const ids = Object.keys(stopWatchlist.value);
  if (ids.length === 0) return;

  try {
    const stopsArray = Object.values(stopWatchlist.value);
    const results = await stopService.getLiveBoard(stopsArray);

    // Map live-boards to gtfs_ids
    const liveBoards: Record<string, StopTimetable> = {};
    for (const timetable of results) {
      liveBoards[timetable.gtfs_id] = timetable;
    }
    stopLiveBoards.value = liveBoards;
  } catch (err) {
    console.error("Failed to update timetables", err);
  }
}

// --- Helpers ---

const currentTimetable = computed(() => {
    if (!selectedStopId.value) return [];
    return stopLiveBoards.value[selectedStopId.value]?.timetable || [];
});

const currentStopName = computed(() => {
    if (!selectedStopId.value) return 'Select Stop';
    const stop = stopWatchlist.value[selectedStopId.value];
    return stop ? (stop.original_name ? stop.original_name: stop.custom_name) : 'Unknown Stop';
});

const formatArrivalTime = (isoString: string, index: number) => {
  const arrival = new Date(isoString);
  const diffMs = arrival.getTime() - now.value.getTime();
  const diffMins = diffMs >= 0 ? Math.floor(diffMs / 60000) : 0; // Force 0 for negative diffs

  // First 3 items AND under 30 minutes -> show minutes
  if (index < 3 && diffMins <= 30) {
    return diffMins.toString(); 
  }

  // Otherwise HH:MM format
  return arrival.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const selectStop = (id: string) => {
  selectedStopId.value = id;
};

// --- Lifecycle ---

// Poll LIVEBOARD every minute
const { pause, resume } = useIntervalFn(() => {
  fetchLiveBoards();
}, 60000, { immediate: false});

watch(stopWatchlist, (newVal) => {
  if (Object.keys(newVal).length > 0) {
    isLoading.value = true;
    fetchLiveBoards().finally(() => isLoading.value = false);
  }
})

onMounted(() => {
  fetchWatchlist();
  resume();
});

</script>

<template>
  <div class="h-full w-full flex flex-col overflow-hidden rounded-3xl shadow-xl bg-[#0066FF] text-white border-4 border-slate-900/50">
    
    <div class="flex w-full bg-black/20 shrink-0">
      <button 
        v-for="(stop, id) in stopWatchlist" 
        :key="id"
        @click="selectStop(id as string)"
        class="flex-1 py-2 text-xs font-medium transition-colors duration-200 border-r border-white/10 last:border-r-0 truncate px-1"
        :class="selectedStopId === id ? 'bg-white text-[#0066FF] font-bold' : 'bg-transparent hover:bg-white/10 text-white/80'"
      >
        {{ stop.custom_name }}
      </button>
    </div>

    <div class="px-5 pt-4 pb-2 border-b-2 border-white/20 shrink-0">
      <div class="flex items-center gap-2 mb-1 opacity-90">
        <span class="text-xs font-extrabold tracking-widest uppercase">NYSSE</span>
      </div>
      <h2 class="text-2xl font-semibold truncate leading-tight">
        {{ currentStopName }}
      </h2>
    </div>

    <div class="flex-1 overflow-y-auto p-0 pb-2 scrollbar-hide relative">
      
      <div v-if="currentTimetable.length > 0" class="flex flex-col">
        <div 
          v-for="(entry, index) in currentTimetable.slice(0, 10)" 
          :key="index"
          class="grid grid-cols-[45px_1fr_60px] items-center gap-x-2 px-5 py-2.5 border-b border-white/10 text-lg"
        >
          <div class="font-extrabold text-left">{{ entry.route }}</div>
          <div class="truncate font-medium pr-2">{{ entry.headsign }}</div>
          
          <div class="text-right font-bold tabular-nums">
            {{ formatArrivalTime(entry.arrival_time, index) }}
          </div>
        </div>
      </div>
      
      <div v-else class="absolute inset-0 flex flex-col items-center justify-center opacity-60 gap-2">
        <span v-if="isLoading" class="animate-pulse">Updating...</span>
        <span v-else>No departures found</span>
      </div>

    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
.scrollbar-hide::-webkit-scrollbar {
  display: none; /* Chrome, Safari and Opera */
}
</style>