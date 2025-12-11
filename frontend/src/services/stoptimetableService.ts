import axios from "axios";
import type { StopWatchlist, StopTimetable } from "../types";

const apiClient = axios.create({
  baseURL: '/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // GET /stops/watchlist
  async getStopWatchlist(): Promise<StopWatchlist[]> {
    const response = await apiClient.get('/stops/watchlist');
    return response.data;
  },

  // POST /stops/watchlist
  async addStopWatchlistEntry(stop: StopWatchlist): Promise<StopWatchlist> {
    const response = await apiClient.post<StopWatchlist>('/stops/watchlist', stop);
    return response.data;
  },

  // DELETE /stops/watchlist/{gtfs_id}
  async deleteStopWatchlistEntry(gtfs_id: string): Promise<void> {
    await apiClient.delete(`/stops/watchlist/${gtfs_id}`);
  }
}