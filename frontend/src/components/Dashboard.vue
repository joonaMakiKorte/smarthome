<script setup lang="ts">
import TodoList from './TodoList.vue';
import Clock from './Clock.vue';
import HourlyForecast from './HourlyForecast.vue';
import ElectricityChart from './ElectricityChart.vue';
import NysseLiveBoard from './NysseLiveBoard.vue';
</script>

<template>
  <div class="h-screen w-screen bg-slate-950 text-slate-200 p-4 overflow-hidden grid grid-cols-[repeat(27,minmax(0,1fr))] grid-rows-[repeat(15,minmax(0,1fr))] gap-4 font-sans">
    
    <div class="col-start-1 col-end-10 row-start-1 row-end-3">
      <Clock />
    </div>

    <div class="col-start-1 col-end-10 row-start-3 row-end-6 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-500">
      <span>🏠 Status (Home Mode)</span>
    </div>

    <div class="col-start-1 col-end-10 row-start-6 row-end-12 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-500">
      <span>🌡️ Ruuvi Sensors</span>
    </div>

    <div class="col-start-1 col-end-[21] row-start-[12] row-end-[16]">
      <HourlyForecast />
    </div>

    <div class="col-start-[10] col-end-[21] row-start-1 row-end-8">
      <TodoList />
    </div>

    <div class="col-start-[10] col-end-[21] row-start-8 row-end-[12]">
      <ElectricityChart />
    </div>

    <div class="col-start-[21] col-end-[28] row-start-1 row-end-[9]">
      <NysseLiveBoard />
    </div>

    <div class="col-start-[21] col-end-[28] row-start-9 row-end-[16] bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed flex items-center justify-center text-slate-500">
      <span>📈 Stocks / Portfolio</span>
    </div>

  </div>
</template>