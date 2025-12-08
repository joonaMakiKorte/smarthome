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

    // Optimistic UI update
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
  <div class="p-4 max-w-2xl mx-auto">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">My Tasks</h1>
      <span class="text-xs text-gray-400 animate-pulse">
        Live Sync Active
      </span>
    </div>
    
    <button 
      @click="() => loadData(false)" 
      class="bg-blue-500 text-white px-4 py-2 rounded mb-4 text-sm"
      :disabled="isLoading"
    >
      {{ isLoading ? 'Loading...' : 'Manual Refresh' }}
    </button>

    <div v-if="isLoading && activeTodos.length === 0" class="text-center py-4">
      Loading your tasks...
    </div>

    <ul v-else class="space-y-2">
      <li 
        v-for="task in activeTodos" 
        :key="task.id" 
        class="border p-3 rounded flex justify-between items-center bg-white shadow-sm"
      >
        <span>{{ task.content }}</span>
        <button 
          @click="handleComplete(task)"
          class="text-green-600 hover:text-green-800 font-bold text-sm border border-green-600 px-2 py-1 rounded hover:bg-green-50"
        >
          Check
        </button>
      </li>
    </ul>

    <div class="mt-8 border-t pt-4">
      <h2 class="text-xl font-bold mb-2 text-gray-700">Recent History</h2>
      <ul class="opacity-60 text-sm">
        <li v-for="task in completedTodos" :key="task.id" class="py-1">
          ✓ {{ task.content }}
        </li>
      </ul>
    </div>
  </div>
</template>