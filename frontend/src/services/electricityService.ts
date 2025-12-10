import axios from "axios";
import type { ElectricityPriceInterval, AvgElectricityPrice } from "../types";

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // POST /electricity/refresh
  async refreshElectricity(): Promise<void> {
    await apiClient.post('/electricity/refresh');
  },

  // GET /electricity/prices
  async getElectricityPrices(interval: '15min' | '1h'): Promise<ElectricityPriceInterval[]> {
    const response = await apiClient.get<ElectricityPriceInterval[]>('/electricity/prices', {
      params: { interval }
    });
    return response.data;
  },

  // GET /electricity/average-10d
  async getElectricityAvg(): Promise<AvgElectricityPrice> {
    const response = await apiClient.get<AvgElectricityPrice>('/electricity/average-10d');
    return response.data;
  }
}
