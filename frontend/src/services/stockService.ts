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
  async getStockQuotes(stocks: Stock[]): Promise<StockQuote[]> {
    // Extract symbols
    const symbolsString = stocks.map(s => s.symbol).join(',');

    const response = await apiClient.get<StockQuote[]>('/stocks/quotes', {
    params: {
      symbols: symbolsString
    }
    });
    return response.data;
  },

  // GET /stocks/history
  async getStockHistory(stocks: Stock[], interval: string): Promise<StockHistoryData[]> {
    const symbolsString = stocks.map(s => s.symbol).join(',');
    const response = await apiClient.get<StockHistoryData[]>('/stocks/history', {
    params: {
      symbols: symbolsString,
      interval: interval
    }
    });
    return response.data;
  }
}
