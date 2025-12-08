import axios from "axios";
import type {TodoTask, CompletedTask} from '../types';

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // GET /todos
  async getActiveTodos(): Promise<TodoTask[]> {
    const response = await apiClient.get<TodoTask[]>('/todos');
    return response.data;
  },

  // GET /todos/completed
  async getCompletedTodos(): Promise<CompletedTask[]> {
    const response = await apiClient.get<CompletedTask[]>('/todos/completed');
    return response.data;
  },

  // POST /todos/refresh
  async refreshTodos(): Promise<void> {
    await apiClient.post('/todos/refresh');
  },

  // POST /todos/{task_id}/complete
  async completeTodo(id: string, content: string, priority: number): Promise<void> {
    await apiClient.post(`/todos/${id}/complete`, null, {
      params: { 
        task_content: content, 
        priority: priority 
      }
    });
  },

  // POST /todos/{task_id}/reopen
  async reopenTodo(id: string): Promise<void> {
    await apiClient.post(`/todos/${id}/reopen`);
  }
};