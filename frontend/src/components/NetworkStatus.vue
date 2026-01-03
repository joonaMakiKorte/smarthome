<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useIntervalFn } from '@vueuse/core';
import networkService from '../services/networkService';
import type { NetworkHealth } from '../types';

// State 
const currentHealth = ref<NetworkHealth | null>(null);
const isLoading = ref(false);

// --- Data Fetching ---

// Fetch NETWORK HEALTH (polled)
const fetchHealth = async () => {
  try {
    if (!currentHealth.value) isLoading.value = true;

    const health = await networkService.getNetworkHealth();
    currentHealth.value = health;
  } catch (err) {
    console.error("Polling failed", err)
  } finally {
    isLoading.value = false;
  }
}

// --- UI Helpers ---

const isOnline = computed(() => {
    return currentHealth.value?.connected && currentHealth.value?.wan_latency_ms !== null;
});

const signalColorClass = computed(() => {
    const q = currentHealth.value?.signal_quality || 0;
    if (q === 0) return isOnline.value ? 'text-slate-500' : 'text-slate-700';
    if (q > 70) return 'text-green-400 drop-shadow-[0_0_8px_rgba(74,222,128,0.6)]';
    if (q > 40) return 'text-yellow-400';
    return 'text-red-500';
});

const lossColorClass = computed(() => {
    const loss = currentHealth.value?.packet_loss;
    if (!loss) return 'text-green-400';
    if (loss < 5) return 'text-yellow-400';
    return 'text-red-500 animate-pulse'; 
});

const formatMetric = (val: number | null) => {
    if (val === null || val === undefined) return '--';
    return Math.round(val);
};

// --- Lifecycle ---

useIntervalFn(() => {
  fetchHealth();
}, 5000);

onMounted(() => {
  fetchHealth();
});

</script>

<template>
  <div class="h-full w-full bg-[#0B1120] rounded-3xl border border-slate-800 relative overflow-hidden flex flex-col p-4 shadow-2xl">

    <div v-if="!currentHealth && isLoading" class="absolute inset-0 flex items-center justify-center text-slate-500 animate-pulse z-20 bg-[#0B1120]">
      <div class="flex flex-col items-center gap-3">
        <svg class="w-10 h-10 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" stroke-width="2" stroke-linecap="round"/></svg>
        <span class="text-xs font-bold uppercase tracking-widest">Scanning...</span>
      </div>
    </div>

    <div v-else-if="currentHealth" class="flex flex-col h-full w-full">

      <div class="h-1/4 flex items-center justify-between w-full border-b border-slate-800/80 mb-2 pb-1">
        
        <div class="flex items-center gap-3 overflow-hidden">
            <div class="relative flex-shrink-0 flex h-3 w-3">
              <span class="relative inline-flex rounded-full h-3 w-3 transition-colors duration-300"
                :class="isOnline ? 'bg-green-500' : 'bg-red-600'">
              </span>
            </div>
            
            <h1 class="text-2xl font-black text-white tracking-tight leading-none truncate min-w-0">
              {{ currentHealth.ssid }}
            </h1>
        </div>

        <div class="flex-shrink-0">
            <svg class="w-8 h-8 text-white"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h.01" stroke-width="4"/>
              <path d="M8.5 16.5a5 5 0 0 1 7 0" :class="{'opacity-20': currentHealth.signal_quality < 25}" />
              <path d="M5 12.5a10 10 0 0 1 14 0" :class="{'opacity-20': currentHealth.signal_quality < 50}" />
              <path d="M2 9a15 15 0 0 1 20 0" :class="{'opacity-20': currentHealth.signal_quality < 75}" />
            </svg>
        </div>
      </div>

      <div class="h-3/4 grid grid-cols-5 gap-2">

            <div class="bg-[#151E32] rounded-xl flex flex-col justify-center items-start pl-3 pr-1 border border-slate-800/50 min-w-0">
              <div class="flex items-baseline gap-1 w-full mb-0.5">
                <span class="text-2xl xl:text-3xl font-black text-green-400 leading-none tracking-tight truncate">
                  {{ currentHealth.server_download_mbps.toFixed(2) }}
                </span>
                <span class="text-[10px] font-bold text-slate-500 flex-shrink-0">Mbps</span>
              </div>
              <div class="flex items-center text-slate-400 text-xs font-extrabold uppercase tracking-wide whitespace-nowrap">
                 <svg class="w-3 h-3 mr-1.5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>
                 Down
              </div>
            </div>

            <div class="bg-[#151E32] rounded-xl flex flex-col justify-center items-start pl-3 pr-1 border border-slate-800/50 min-w-0">
              <div class="flex items-baseline gap-1 w-full mb-0.5">
                <span class="text-2xl xl:text-3xl font-black text-blue-400 leading-none tracking-tight truncate">
                  {{ currentHealth.server_upload_mbps.toFixed(2) }}
                </span>
                <span class="text-[10px] font-bold text-slate-500 flex-shrink-0">Mbps</span>
              </div>
              <div class="flex items-center text-slate-400 text-xs font-extrabold uppercase tracking-wide whitespace-nowrap">
                 <svg class="w-3 h-3 mr-1.5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 10l7-7m0 0l7 7m-7-7v18"></path></svg>
                 Up
              </div>
            </div>

            <div class="bg-[#151E32] rounded-xl flex flex-col justify-center items-start pl-3 pr-1 border border-slate-800/50 min-w-0">
              <div class="flex items-baseline gap-1 w-full mb-0.5">
                <span class="text-2xl xl:text-3xl font-black text-yellow-400 leading-none tracking-tight truncate">
                  {{ formatMetric(currentHealth.wan_latency_ms) }}
                </span>
                <span class="text-[10px] font-bold text-slate-500 flex-shrink-0">ms</span>
              </div>
              <div class="flex items-center text-slate-400 text-xs font-extrabold uppercase tracking-wide whitespace-nowrap">
                 <svg class="w-3 h-3 mr-1.5 text-yellow-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                 Ping
              </div>
            </div>

            <div class="bg-[#151E32] rounded-xl flex flex-col justify-center items-start pl-3 pr-1 border border-slate-800/50 min-w-0">
              <div class="flex items-baseline gap-1 w-full mb-0.5">
                <span class="text-2xl xl:text-3xl font-black text-cyan-400 leading-none tracking-tight truncate">
                  {{ formatMetric(currentHealth.lan_latency_ms) }}
                </span>
                <span class="text-[10px] font-bold text-slate-500 flex-shrink-0">ms</span>
              </div>
              <div class="flex items-center text-slate-400 text-xs font-extrabold uppercase tracking-wide whitespace-nowrap">
                 <svg class="w-3 h-3 mr-1.5 text-cyan-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
                 Router
              </div>
            </div>

            <div class="bg-[#151E32] rounded-xl flex flex-col justify-center items-start pl-3 pr-1 border border-slate-800/50 min-w-0">
              <div class="flex items-baseline gap-1 w-full mb-0.5">
                <span class="text-2xl xl:text-3xl font-black leading-none tracking-tight truncate" :class="lossColorClass">
                  {{ formatMetric(currentHealth.packet_loss) }}
                </span>
                <span class="text-[10px] font-bold text-slate-500 flex-shrink-0">%</span>
              </div>
              <div class="flex items-center text-slate-400 text-xs font-extrabold uppercase tracking-wide whitespace-nowrap">
                 <svg class="w-3 h-3 mr-1.5 flex-shrink-0" :class="currentHealth.packet_loss && currentHealth.packet_loss > 0 ? 'text-red-500' : 'text-slate-500'" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                 Loss
              </div>
            </div>

      </div>

    </div>
  </div>
</template>