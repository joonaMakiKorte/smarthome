<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useIntervalFn, useNow } from '@vueuse/core';
import type { Stock, StockQuote, StockPriceEntry } from '../types';
import stockService from '../services/stockService';

// Types
type Interval = '1min' | '15min'

// State 
const stockWatchlist = ref<Record<string, Stock>>({});
const stockQuotes = ref<Record<string, StockQuote>>({});
const stockHistory = ref<{ [key in Interval]?: Record<string, StockPriceEntry[]> }>({});
const selectedSymbol = ref<string | null>(null);
const isLoading = ref(false);

let pollInterval: ReturnType<typeof setInterval> | null = null;

const scrollContainer = ref<HTMLElement | null>(null);
let isDown = false;
let startY = 0;
let scrollTop = 0;

// --- Data Fetching ---

const fetchWatchlist = async() => {
  try {
    const watchlist = await stockService.getStockWatchlist();
    
    const record: Record<string, Stock> = {};
    watchlist.forEach(stock => {
      record[stock.symbol] = stock;
    });
    stockWatchlist.value = record;
  } catch (err) {
    console.error("Fetching watchlist failed", err)
  }
}

// Fetch QUOTES for watchlist or only the selected symbol
const fetchQuotes = async(forced: boolean = false) => {
  let symbols = Object.keys(stockWatchlist.value);
  if (symbols.length === 0) return;

  try {
    let symbolsString = '';
    // If forced, fetch only the selected symbol
    if (forced && selectedSymbol.value) {
      symbolsString = selectedSymbol.value;
    } else {
      symbolsString = symbols.join(',');
    }
    const results = await stockService.getStockQuotes(symbolsString);

    // Map quotes to symbols
    const quotes: Record<string, StockQuote> = {};
    for (const quote of results) {
      quotes[quote.symbol] = quote;
    }
    stockQuotes.value = quotes;
  } catch (err) {
    console.error("Failed to update quotes", err);
  }
}

// Fetch HISTORY for watchlist or only the selected symbol
const fetchHistory = async(forced: boolean = false) => {
  let symbols = Object.keys(stockWatchlist.value);
  if (symbols.length === 0) return;
  try {
    let symbolsString = '';
    let interval: Interval = '15min';
    // If forced, fetch only the selected symbol with 1 min interval
    if (forced && selectedSymbol.value) {
      symbolsString = selectedSymbol.value;
      interval = '1min';
    } else {
      symbolsString = symbols.join(',');
    }
    const results = await stockService.getStockHistory(symbolsString, interval);
    const history: Record<string, StockPriceEntry[]> = {};
    for (const data of results) {
      history[data.symbol] = data.history;
    }
    stockHistory.value[interval] = history;
  } catch (err) {
    console.error("Fetching history failed", err);
  }
}

// --- Helpers ---

// Is US Market Open (9:30-17:00 America/NY, real end is 16:00 but we use 1h buffer for safety)
const isMarketOpen = (): boolean => {
  const now = new Date();
  
  // Convert current time to New York time
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'America/New_York',
    hour: 'numeric',
    minute: 'numeric',
    weekday: 'short',
    hour12: false
  };
  const formatter = new Intl.DateTimeFormat('en-US', options);
  const parts = formatter.formatToParts(now);
  const partMap: Record<string, string> = {};
  parts.forEach(p => partMap[p.type] = p.value);
  
  const day = partMap.weekday; 
  const hour = parseInt(partMap.hour);
  const minute = parseInt(partMap.minute);
  
  if (day === 'Sat' || day === 'Sun') return false;
  if (hour < 9 || hour >= 17) return false;
  if (hour === 9 && minute < 30) return false;

  return true;
};

// --- UI Helpers ---

const onMouseDown = (e: MouseEvent) => {
  if (!scrollContainer.value) return;
  isDown = true;
  scrollContainer.value.classList.add('active');
  startY = e.pageY - scrollContainer.value.offsetTop;
  scrollTop = scrollContainer.value.scrollTop;
};

const onMouseLeave = () => {
  isDown = false;
  scrollContainer.value?.classList.remove('active');
};

const onMouseUp = () => {
  isDown = false;
  scrollContainer.value?.classList.remove('active');
};

const onMouseMove = (e: MouseEvent) => {
  if (!isDown || !scrollContainer.value) return;
  e.preventDefault();
  const y = e.pageY - scrollContainer.value.offsetTop;
  const walk = (y - startY) * 2; 
  scrollContainer.value.scrollTop = scrollTop - walk;
};

// --- Lifecycle ---

const QUOTE_INTERVAL_MIN = 15;
const HISTORY_INTERVAL_MIN = 30;
const HISTORY_OFFSET_MIN = 5;
const startPolling = () => {
  pollInterval = setInterval(() => {

  }, 60000);
};

</script>