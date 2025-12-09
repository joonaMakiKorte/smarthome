import axios from "axios";
import type { CurrentWeather } from "../types";

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // GET /weather/current
  async getCurrentWeather(): Promise<CurrentWeather> {
    const response = await apiClient.get<CurrentWeather>('/weather/current');
    return response.data;
  }
};