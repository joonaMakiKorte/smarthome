<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useIntervalFn, useNow } from '@vueuse/core';
import type { StopTimetable, StopWatchlist } from '../types';
import stopService from '../services/stopService';

// State
const stopWatchlist = ref<Record<string, StopWatchlist>>({});
const stopOrder = ref<string[]>([]);
const stopLiveBoards = ref<Record<string, StopTimetable>>({});
const selectedStopId = ref<string | null>(null);
const isLoading = ref(false);

// Drag State
const viewport = ref<HTMLElement | null>(null);
const listRefs = ref<HTMLElement[]>([]);
const dragOffset = ref(0);
const isDragging = ref(false);
const isTransitioning = ref(false);

// Drag logic variables
let startX = 0;
let startY = 0;
let initialScrollTop = 0;
let isLockedHorizontal = false;
let isLockedVertical = false;

const now = useNow({ interval: 1000 }); // Reactive time updating every second

// --- Data Fetching ---

const fetchWatchlist = async() => {
  try {
    const watchlist = await stopService.getStopWatchlist();
    
    const record: Record<string, StopWatchlist> = {};
    const order: string[] = [];

    watchlist.forEach(stop => {
      record[stop.gtfs_id] = stop;
      order.push(stop.gtfs_id);
    });

    stopWatchlist.value = record;
    stopOrder.value = order;

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

const currentIndex = computed(() => {
  if (!selectedStopId.value) return 0;
  return stopOrder.value.indexOf(selectedStopId.value);
});

const currentTimetable = (id: string) => {
    return stopLiveBoards.value[id]?.timetable || [];
};

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

// --- Drag Logic ---

const trackStyle = computed(() => {
  const percentage = currentIndex.value * 100;
  const pixelOffset = dragOffset.value; 
  return {
    transform: `translateX(calc(-${percentage}% + ${pixelOffset}px))`,
    transition: isDragging.value ? 'none' : 'transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1)'
  };
});

// Helper to get X/Y from either MouseEvent or TouchEvent
const getClientCoords = (e: MouseEvent | TouchEvent) => {
    if ((e as TouchEvent).touches && (e as TouchEvent).touches.length > 0) {
        return { x: (e as TouchEvent).touches[0].pageX, y: (e as TouchEvent).touches[0].pageY };
    }
    return { x: (e as MouseEvent).pageX, y: (e as MouseEvent).pageY };
};

const onStart = (e: MouseEvent | TouchEvent) => {
  isDragging.value = true;
  const { x, y } = getClientCoords(e);
  startX = x;
  startY = y;
  isLockedHorizontal = false;
  isLockedVertical = false;

  const activeList = listRefs.value[currentIndex.value];
  if (activeList) initialScrollTop = activeList.scrollTop;
};

const onMove = (e: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return;

  const { x, y } = getClientCoords(e);
  const diffX = x - startX;
  const diffY = y - startY;

  // Determine Lock Direction (if not yet locked)
  if (!isLockedHorizontal && !isLockedVertical) {
    if (Math.abs(diffX) > 10 && Math.abs(diffX) > Math.abs(diffY)) {
      isLockedHorizontal = true;
    } else if (Math.abs(diffY) > 10) {
      isLockedVertical = true;
    }
  }

  // Handle Horizontal Drag (Carousel)
  if (isLockedHorizontal) {
    if (e.cancelable) e.preventDefault(); // Stop native page swipe navigation
    
    const isFirst = currentIndex.value === 0 && diffX > 0;
    const isLast = currentIndex.value === stopOrder.value.length - 1 && diffX < 0;
    
    // Strict Edge Limits
    if (isFirst || isLast) {
        dragOffset.value = 0;
    } else {
        dragOffset.value = diffX;
    }
  } 
  
  // Handle Vertical Drag 
  if (isLockedVertical) {
    if (e.cancelable) e.preventDefault(); 
    
    const activeList = listRefs.value[currentIndex.value];
    if (activeList) {
      activeList.scrollTop = initialScrollTop - diffY * 1.5;
    }
  }
};

const onEnd = () => {
  if (!isDragging.value) return;
  isDragging.value = false;

  if (isLockedHorizontal && viewport.value) {
    const width = viewport.value.offsetWidth;
    const threshold = width * 0.25; // 25% threshold for snappier feel

    if (dragOffset.value < -threshold) {
      if (currentIndex.value < stopOrder.value.length - 1) {
        selectedStopId.value = stopOrder.value[currentIndex.value + 1];
      }
    } else if (dragOffset.value > threshold) {
      if (currentIndex.value > 0) {
        selectedStopId.value = stopOrder.value[currentIndex.value - 1];
      }
    }
  }
  
  dragOffset.value = 0;
  isLockedHorizontal = false;
  isLockedVertical = false;
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
  <div class="h-full w-full flex flex-col overflow-hidden rounded-3xl shadow-xl bg-[#0066FF] text-white border-4 border-slate-900/50 select-none">
    
    <div class="flex w-full bg-black/20 shrink-0 z-10 relative">
      <button 
        v-for="(id) in stopOrder" 
        :key="id"
        @click="selectStop(id)"
        class="flex-1 py-2 text-xs font-medium transition-colors duration-200 border-r border-white/10 last:border-r-0 truncate px-1"
        :class="selectedStopId === id ? 'bg-white text-[#0066FF] font-bold' : 'bg-transparent hover:bg-white/10 text-white/80'"
      >
        {{ stopWatchlist[id]?.custom_name }}
      </button>
    </div>

    <div 
      ref="viewport"
      @mousedown="onStart"
      @mousemove="onMove"
      @mouseup="onEnd"
      @mouseleave="onEnd"
      @touchstart="onStart"
      @touchmove="onMove"
      @touchend="onEnd"
      class="flex-1 overflow-hidden relative cursor-grab active:cursor-grabbing"
    >
      <div class="flex h-full w-full will-change-transform" :style="trackStyle">
        
        <div 
          v-for="(id, index) in stopOrder" 
          :key="id"
          class="w-full h-full flex-shrink-0 flex flex-col"
        >
          <div class="px-5 pt-4 pb-2 border-b-2 border-white/20 shrink-0">
            <div class="flex items-center gap-2 mb-1 opacity-90">
              <span class="text-xs font-extrabold tracking-widest uppercase">NYSSE</span>
            </div>
            <h2 class="text-2xl font-semibold truncate leading-tight">
              {{ stopWatchlist[id]?.original_name || stopWatchlist[id]?.custom_name }}
            </h2>
          </div>

          <div 
            :ref="(el) => listRefs[index] = el as HTMLElement"
            class="flex-1 overflow-y-auto p-0 pb-2 scrollbar-hide relative"
          >
            <div v-if="currentTimetable(id).length > 0" class="flex flex-col">
              <div 
                v-for="(entry, idx) in currentTimetable(id).slice(0, 10)" 
                :key="idx"
                class="grid grid-cols-[45px_1fr_60px] items-center gap-x-2 px-5 py-2.5 border-b border-white/10 text-lg"
              >
                <div class="font-extrabold text-left">{{ entry.route }}</div>
                <div class="truncate font-medium pr-2">{{ entry.headsign }}</div>
                
                <div class="text-right font-bold tabular-nums">
                  {{ formatArrivalTime(entry.arrival_time, idx) }}
                </div>
              </div>
            </div>
            
            <div v-else class="absolute inset-0 flex flex-col items-center justify-center opacity-60 gap-2">
              <span v-if="isLoading" class="animate-pulse">Updating...</span>
              <span v-else>No departures found</span>
            </div>
          </div>

        </div> 
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