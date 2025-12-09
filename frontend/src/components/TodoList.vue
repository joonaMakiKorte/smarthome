<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useIntervalFn } from '@vueuse/core';
import todoService from '../services/todoService';
import type { TodoTask, CompletedTask } from '../types';

// State
const activeTodos = ref<TodoTask[]>([]);
const completedTodos = ref<CompletedTask[]>([]);
const currentTab = ref<'active' | 'completed'>('active');
const isLoading = ref(false);

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
}

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
  <div class="h-full w-full flex flex-col bg-slate-800 rounded-3xl border border-slate-700 shadow-xl overflow-hidden">
    
    <div class="bg-slate-900/50 border-b border-slate-700 flex flex-col">
      <div class="p-4 flex justify-between items-center">
        <h2 class="text-lg font-bold text-white flex items-center gap-2">
          <span>Tasks</span>
          <span class="bg-blue-900 text-blue-200 text-xs px-2 py-0.5 rounded-full">
            {{ currentTab === 'active' ? activeTodos.length : completedTodos.length }}
          </span>
        </h2>
        <button @click="fetchAll" class="text-slate-500 hover:text-white transition-colors" title="Force Refresh">
          ↻
        </button>
      </div>

      <div class="flex text-sm font-medium">
        <button 
          @click="currentTab = 'active'"
          class="flex-1 py-3 text-center transition-colors border-b-2"
          :class="currentTab === 'active' 
            ? 'text-blue-400 border-blue-500 bg-slate-800' 
            : 'text-slate-500 border-transparent hover:bg-slate-800/50 hover:text-slate-300'"
        >
          Active
        </button>
        <button 
          @click="currentTab = 'completed'"
          class="flex-1 py-3 text-center transition-colors border-b-2"
          :class="currentTab === 'completed' 
            ? 'text-green-400 border-green-500 bg-slate-800' 
            : 'text-slate-500 border-transparent hover:bg-slate-800/50 hover:text-slate-300'"
        >
          History
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2 relative">
      
      <div v-if="isLoading && activeTodos.length === 0" class="absolute inset-0 flex items-center justify-center bg-slate-800 z-10">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>

      <template v-if="currentTab === 'active'">
        <div v-if="activeTodos.length === 0" class="text-center py-10 text-slate-500 italic text-sm">
          No active tasks. Relax!
        </div>
        
        <div 
          v-for="task in activeTodos" 
          :key="task.id" 
          class="bg-slate-700/40 p-3 rounded-xl border border-slate-600/30 flex justify-between items-center group hover:bg-slate-700/60 transition-colors"
        >
          <span class="text-slate-200 text-sm font-medium truncate mr-2">{{ task.content }}</span>
          <button 
            @click="handleComplete(task)"
            class="shrink-0 bg-slate-800 text-slate-400 border border-slate-600 hover:bg-green-600 hover:text-white hover:border-green-500 px-3 py-1 rounded-lg text-xs font-bold transition-all"
          >
            Done
          </button>
        </div>
      </template>

      <template v-if="currentTab === 'completed'">
        <div v-if="completedTodos.length === 0" class="text-center py-10 text-slate-500 italic text-sm">
          No history available.
        </div>

        <div 
          v-for="task in completedTodos" 
          :key="task.id" 
          class="bg-slate-800/30 p-3 rounded-xl border border-slate-700/30 flex justify-between items-center opacity-75 group hover:opacity-100 transition-opacity"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <span class="text-green-500 text-sm">✓</span>
            <span class="text-slate-400 text-sm line-through truncate">{{ task.content }}</span>
          </div>
          <button 
            @click="handleReopen(task)"
            class="shrink-0 text-xs text-slate-600 hover:text-blue-400 px-2 py-1"
          >
            Reopen
          </button>
        </div>
      </template>

    </div>
  </div>
</template>