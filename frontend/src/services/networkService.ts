import axios from "axios";
import type { NetworkHealth } from "../types";

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // GET /network
  async getNetworkHealth(): Promise<NetworkHealth> {
    const response = await apiClient.get<NetworkHealth>('/network');
    return response.data;
  },

  // POST /network/refresh
  async refreshNetworkHealth(): Promise<void> {
    await apiClient.post('/network/refresh');
  }
};