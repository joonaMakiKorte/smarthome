import axios from "axios";
import type { Stock, StockQuote, StockHistoryData } from "../types";

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // GET /stocks/watchlist
  async getStockWatchlist(): Promise<Stock[]> {
    const response = await apiClient.get('/stocks/watchlist');
    return response.data;
  },

  // POST /stocks/watchlist
  async addStockWatchlistEntry(stock: Stock): Promise<Stock> {
    const response = await apiClient.post<Stock>('/stocks/watchlist', stock);
    return response.data;
  },

  // DELETE /stocks/watchlist/{symbol}
  async deleteStockWatchlistEntry(symbol: string): Promise<void> {
    await apiClient.delete(`/stocks/watchlist/${symbol}`);
  },

  // GET /stocks/quotes
  async getStockQuotes(symbols: string): Promise<StockQuote[]> {
    const response = await apiClient.get<StockQuote[]>('/stocks/quotes', {
    params: {
      symbols: symbols
    }
    });
    return response.data;
  },

  // GET /stocks/history
  async getStockHistory(symbols: string, interval: string): Promise<StockHistoryData[]> {
    const response = await apiClient.get<StockHistoryData[]>('/stocks/history', {
    params: {
      symbols: symbols,
      interval: interval
    }
    });
    return response.data;
  }
}
