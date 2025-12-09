<script setup lang="ts">
import TodoList from './TodoList.vue';

// Minimal clock for the header (optional helper)
const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
</script>

<template>
  <div class="h-screen w-screen bg-slate-950 text-slate-200 p-6 overflow-hidden flex flex-col font-sans">
    
    <header class="flex justify-between items-end mb-6 shrink-0 px-2">
      <div>
        <h1 class="text-3xl font-bold text-white tracking-tight">Morning Dashboard</h1>
        <p class="text-slate-500">Lenovo Kiosk • {{ time }}</p>
      </div>
      <div class="flex gap-2">
        <span class="h-3 w-3 rounded-full bg-green-500 block" title="System Online"></span>
      </div>
    </header>

    <div class="flex-1 grid grid-cols-3 grid-rows-2 gap-6 min-h-0">
      
      <div class="col-span-1 row-span-2">
        <TodoList />
      </div>

      <div class="col-span-2 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-600">
        <span class="text-xl">Future Widget: Weather / Calendar</span>
      </div>

      <div class="col-span-1 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-600">
        <span>Future Widget: Smart Home</span>
      </div>

      <div class="col-span-1 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-600">
        <span>Future Widget: Server Stats</span>
      </div>

    </div>
  </div>
</template>