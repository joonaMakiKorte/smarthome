<script setup lang="ts">
import TodoList from './TodoList.vue';

const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
</script>

<template>
  <div class="h-screen w-screen bg-slate-950 text-slate-200 p-6 overflow-hidden flex flex-col font-sans">
    
    <header class="flex justify-between items-end mb-6 shrink-0 px-2">
      <div>
        <h1 class="text-3xl font-bold text-white tracking-tight">Dashboard</h1>
        <p class="text-slate-500">Lenovo Kiosk • {{ time }}</p>
      </div>
    </header>

    <div class="flex-1 grid grid-cols-3 grid-rows-2 gap-6 min-h-0">
      
      <div class="col-span-1 row-span-1 min-h-0">
        <TodoList />
      </div>

      <div class="col-span-1 row-span-1 bg-slate-900/30 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-600">
        <span>Future Widget (Small)</span>
      </div>

      <div class="col-span-2 bg-slate-900/30 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-600">
        <span>Future Widget: Weather / Calendar</span>
      </div>

      <div class="col-span-2 bg-slate-900/30 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-600">
        <span>Future Widget: Smart Home / Logs</span>
      </div>

    </div>
  </div>
</template>