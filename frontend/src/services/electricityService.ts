import axios from "axios";
import type { ElectricityPriceInterval, AvgElectricityPrice } from "../types";

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
    
}
