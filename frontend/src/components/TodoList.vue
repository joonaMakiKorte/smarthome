<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useIntervalFn } from '@vueuse/core';
import todoService from '../services/todoService';
import type { TodoTask, CompletedTask } from '../types';

// State
const activeTodos = ref<TodoTask[]>([]);
const completedTodos = ref<CompletedTask[]>([]);
const currentTab = ref<'active' | 'completed'>('active');
const isLoading = ref(false);

const scrollContainer = ref<HTMLElement | null>(null);
let isDown = false;
let startY = 0;
let scrollTop = 0;

// --- Data Fetching ---

// Fetch ACTIVE and COMPLETED tasks
const fetchAll = async() => {
  try {
    const [active, completed] = await Promise.all([
      todoService.getActiveTodos(),
      todoService.getCompletedTodos()
    ]);
    activeTodos.value = active;
    completedTodos.value = completed;
  } catch (err) {
    console.error("Full fetch failed", err);
  }
};

// Fetch ACTIVE tasks (is polled)
const fetchActive = async () => {
  try {
    const active = await todoService.getActiveTodos();
    activeTodos.value = active;
  } catch (err) {
    console.error("Polling failed", err);
  }
}

// --- User Actions ---

const handleComplete = async (task: TodoTask) => {
  // Pause polling while user interacts to prevent jitter
  pause(); 

  // Optimistic UI update (remove task immediately)
  activeTodos.value = activeTodos.value.filter(t => t.id !== task.id);

  try {
    await todoService.completeTodo(task.id, task.content, task.priority);
    await fetchAll(); // Full refresh
  } catch (err) {
    console.error("Failed to complete task", err);
    await fetchAll(); // Revert
  }

  resume(); // Restart polling
};

const handleReopen = async (task: CompletedTask) => {
  pause();

  // Optimistic UI
  completedTodos.value = completedTodos.value.filter(t => t.id !== task.id);

  try {
    await todoService.reopenTodo(task.id);
    await fetchAll(); // Full refresh
  } catch (err) {
    console.error("Failed to reopen task", err);
    await fetchAll();
  }

  resume();
};

// --- UI Helpers ---

const getPriorityStyles = (priority: number) => {
  switch (priority) {
    case 1: // Gray
      return 'bg-gradient-to-r from-slate-700/40 to-slate-800/20 border-slate-600/30';
    case 2: // Blue
      return 'bg-gradient-to-r from-blue-900/40 to-blue-800/20 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.1)]';
    case 3: // Orange
      return 'bg-gradient-to-r from-orange-600/30 to-orange-800/10 border-orange-400/50 shadow-[0_0_15px_rgba(251,146,60,0.15)]';
    case 4: // Red
      return 'bg-gradient-to-r from-red-900/40 to-red-800/20 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.1)]';
    default:
      return 'bg-gradient-to-r from-slate-700/40 to-slate-800/20 border-slate-600/30';
  }
};

// Drag Scrolling
const onMouseDown = (e: MouseEvent) => {
  if (!scrollContainer.value) return;
  isDown = true;
  scrollContainer.value.classList.add('active');
  startY = e.pageY - scrollContainer.value.offsetTop;
  scrollTop = scrollContainer.value.scrollTop;
};
const onMouseLeave = () => { isDown = false; scrollContainer.value?.classList.remove('active'); };
const onMouseUp = () => { isDown = false; scrollContainer.value?.classList.remove('active'); };
const onMouseMove = (e: MouseEvent) => {
  if (!isDown || !scrollContainer.value) return;
  e.preventDefault();
  const y = e.pageY - scrollContainer.value.offsetTop;
  const walk = (y - startY) * 2; 
  scrollContainer.value.scrollTop = scrollTop - walk;
};

// --- Lifecycle ---

// Poll only ACTIVE tasks every 10 seconds
const { pause, resume } = useIntervalFn(() => {
  fetchActive();
}, 10000);

onMounted(() => {
  isLoading.value = true;
  fetchAll().finally(() => isLoading.value = false);
});
</script>

<template>
  <div class="h-full w-full flex flex-col bg-slate-800 rounded-3xl border border-slate-700 shadow-xl overflow-hidden select-none">
    
    <div class="bg-slate-900/50 border-b border-slate-700 flex flex-col">
      <div class="p-5 flex justify-between items-center">
        <h2 class="text-xl font-bold text-white flex items-center gap-3">
          <span>Tasks</span>
          <span class="bg-blue-900 text-blue-200 text-sm px-2.5 py-0.5 rounded-full font-mono">
            {{ currentTab === 'active' ? activeTodos.length : completedTodos.length }}
          </span>
        </h2>
        <button @click="fetchAll" class="text-slate-500 hover:text-white transition-colors p-1" title="Force Refresh">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
        </button>
      </div>

      <div class="flex text-sm font-medium">
        <button 
          @click="currentTab = 'active'"
          class="flex-1 py-3 text-center transition-colors border-b-2 text-base"
          :class="currentTab === 'active' 
            ? 'text-blue-400 border-blue-500 bg-slate-800' 
            : 'text-slate-500 border-transparent hover:bg-slate-800/50 hover:text-slate-300'"
        >
          Active
        </button>
        <button 
          @click="currentTab = 'completed'"
          class="flex-1 py-3 text-center transition-colors border-b-2 text-base"
          :class="currentTab === 'completed' 
            ? 'text-green-400 border-green-500 bg-slate-800' 
            : 'text-slate-500 border-transparent hover:bg-slate-800/50 hover:text-slate-300'"
        >
          History
        </button>
      </div>
    </div>

    <div 
      ref="scrollContainer"
      @mousedown="onMouseDown"
      @mouseleave="onMouseLeave"
      @mouseup="onMouseUp"
      @mousemove="onMouseMove"
      class="flex-1 overflow-y-auto p-0 pb-2 scrollbar-hide relative cursor-grab active:cursor-grabbing"
    >
      
      <div v-if="isLoading && activeTodos.length === 0" class="absolute inset-0 flex items-center justify-center bg-slate-800 z-10">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
      </div>

      <template v-if="currentTab === 'active'">
        <div v-if="activeTodos.length === 0" class="flex flex-col items-center justify-center py-12 text-slate-500 space-y-4 h-full min-h-[200px]">
          <span class="italic text-base">No active tasks. Relax!</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor" class="w-24 h-24 opacity-20">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
          </svg>
        </div>
        
        <div 
          v-for="task in activeTodos" 
          :key="task.id" 
          class="p-4 rounded-2xl border flex justify-between items-center group transition-all duration-200 hover:scale-[1.01] hover:shadow-lg"
          :class="getPriorityStyles(task.priority)"
        >
          <span class="text-slate-200 text-lg font-medium truncate mr-3 drop-shadow-sm">{{ task.content }}</span>
          
          <button 
            @click.stop="handleComplete(task)"
            class="shrink-0 bg-slate-800/80 backdrop-blur-sm text-slate-300 border border-slate-600 hover:bg-green-600 hover:text-white hover:border-green-500 px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-sm"
          >
            Done
          </button>
        </div>
      </template>

      <template v-if="currentTab === 'completed'">
        <div v-if="completedTodos.length === 0" class="flex flex-col items-center justify-center py-12 text-slate-500 space-y-4 h-full min-h-[200px]">
          <span class="italic text-base">No history available.</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor" class="w-24 h-24 opacity-20">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
          </svg>
        </div>

        <div 
          v-for="task in completedTodos" 
          :key="task.id" 
          class="bg-slate-800/40 p-4 rounded-2xl border border-slate-700/50 flex justify-between items-center opacity-60 hover:opacity-100 transition-all duration-300"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <span class="text-green-500 font-bold text-lg">✓</span>
            <span class="text-slate-400 text-base line-through truncate">{{ task.content }}</span>
          </div>
          
          <button 
            @click.stop="handleReopen(task)"
            class="shrink-0 bg-slate-900/50 border border-slate-700 text-slate-400 hover:text-blue-200 hover:bg-blue-900/50 hover:border-blue-700 px-4 py-2 rounded-xl text-sm font-medium transition-all"
          >
            Reopen
          </button>
        </div>
      </template>

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