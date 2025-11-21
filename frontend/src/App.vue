<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

type Task = {
  id: number;
  content: string;
  is_completed: boolean;
};

// 1. State: Where we store the list
// We use 'ref' to make it reactive (update screen when data changes)
const tasks = ref<Task[]>([]);
const error = ref('');

// 2. Function to fetch data
const fetchTasks = async () => {
  try {
    const response = await axios.get<Task[]>('http://localhost:8000/todos');
    tasks.value = response.data;
    console.log("Tasks loaded:", tasks.value);
  } catch (err) {
    console.error(err);
    error.value = "Could not connect to Backend (Is it running?)";
  }
};

// 3. Run this when the page loads
onMounted(() => {
  fetchTasks();
});
</script>

<template>
  <div style="font-family: sans-serif; padding: 2rem;">
    <h1>Smart Home Dashboard</h1>
    
    <div v-if="error" style="color: red; font-weight: bold;">
      {{ error }}
    </div>

    <h2>Todo List (From iPhone)</h2>
    <button @click="fetchTasks" style="margin-bottom: 20px; padding: 10px;">
      Refresh List
    </button>

    <ul v-if="tasks.length > 0">
      <li v-for="task in tasks" :key="task.id" style="margin-bottom: 10px; font-size: 1.2rem;">
        <!-- Checkbox logic later, just visuals for now -->
        <span v-if="task.is_completed">✅</span>
        <span v-else>⬜</span> 
        {{ task.content }}
      </li>
    </ul>
    <p v-else>No tasks found for Today or #Dashboard!</p>
  </div>
</template>