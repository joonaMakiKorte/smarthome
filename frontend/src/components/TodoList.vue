<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useIntervalFn } from '@vueuse/core';
import todoService from '../services/todoService';
import type { TodoTask, CompletedTask } from '../types';

const activeTodos = ref<TodoTask[]>([]);
const completedTodos = ref<CompletedTask[]>([]);
const isLoading = ref(false);

const loadData = async (isBackground = false) => {
    try {
    // Only show spinner if not background refresh
    if (!isBackground) {
        isLoading.value = true;
    }

    const [active, completed] = await Promise.all([
        todoService.getActiveTodos(),
        todoService.getCompletedTodos()
    ]);

    activeTodos.value = active;
    completedTodos.value = completed;

    } catch (error) {
        console.error("Failed to load todos:", error);
    } finally {
        isLoading.value = false;
    }
};

const handleComplete = async (task: TodoTask) => {
    // Pause polling while user interacts to prevent jitter
    pause(); 

    activeTodos.value = activeTodos.value.filter(t => t.id !== task.id);

    await todoService.completeTodo(task.id, task.content, task.priority);
    await loadData(true); // Silent reload

    resume(); // Restart polling
};


// Polling: Run loadData(true) every 5000ms (5 seconds)
const { pause, resume } = useIntervalFn(() => {
    loadData(true);
}, 5000);

// Initial load (show spinner)
onMounted(() => {
    loadData(false);
});
</script>

<template>
  <div class="h-full w-full flex flex-col bg-slate-800 rounded-3xl border border-slate-700 shadow-xl overflow-hidden">
    
    <div class="p-5 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
      <h2 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-blue-400">📝</span> Tasks
        <span class="bg-blue-900 text-blue-200 text-xs px-2 py-1 rounded-full">{{ activeTodos.length }}</span>
      </h2>
      <button 
        @click="() => loadData(false)" 
        class="text-sm text-slate-400 hover:text-white transition-colors"
      >
        {{ isLoading ? '...' : '↻' }}
      </button>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
      
      <div v-if="activeTodos.length === 0" class="text-center py-8 text-slate-500 italic text-sm">
        No active tasks.
      </div>
      
      <div 
        v-for="task in activeTodos" 
        :key="task.id" 
        class="bg-slate-700/40 p-3 rounded-xl border border-slate-600/30 flex justify-between items-center group"
      >
        <span class="text-slate-200 font-medium truncate mr-2">{{ task.content }}</span>
        <button 
          @click="handleComplete(task)"
          class="opacity-60 group-hover:opacity-100 bg-green-500/10 text-green-400 border border-green-500/30 hover:bg-green-500 hover:text-white px-3 py-1.5 rounded-lg text-sm font-bold transition-all"
        >
          Done
        </button>
      </div>

      <div class="pt-4 mt-4 border-t border-slate-700/50">
        <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Recently Completed</h3>
        <ul class="space-y-2">
          <li v-for="task in completedTodos" :key="task.id" class="text-sm text-slate-500 flex items-center gap-2">
            <span class="text-green-500/50">✓</span>
            <span class="line-through">{{ task.content }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>