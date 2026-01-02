<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import type { Stock, StockQuote, StockPriceEntry } from '../types';
import stockService from '../services/stockService';

// Types
type Interval = '1min' | '5min'

// State 
const stockWatchlist = ref<Record<string, Stock>>({});
const stockQuotes = ref<Record<string, StockQuote>>({});
const stockHistory = ref<{ [key in Interval]?: Record<string, StockPriceEntry[]> }>({});
const selectedSymbol = ref<string | null>(null);

const isLoading = ref(false); // Base loader for initial mount
const isDetailLoading = ref(false); // Specific loader for detailed view
const isInitialHistoryLoaded = ref(false); // Gatekeeper state

// Track last successful fetch times
const lastQuoteFetchTime = ref<number>(0);
const lastHistoryFetchTime = ref<number>(0);

let schedulerTimer: ReturnType<typeof setInterval> | null = null;

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

    // Merge new results into existing state
    const newQuotes = { ...stockQuotes.value };
    for (const quote of results) {
      newQuotes[quote.symbol] = quote;
    }
    stockQuotes.value = newQuotes;

    // Update timestamp only if this was a full fetch
    if (!forced) lastQuoteFetchTime.value = Date.now();

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
    let interval: Interval = '5min';
    // If forced, fetch only the selected symbol with 1 min interval
    if (forced && selectedSymbol.value) {
      symbolsString = selectedSymbol.value;
      interval = '1min';
    } else {
      symbolsString = symbols.join(',');
    }
    const results = await stockService.getStockHistory(symbolsString, interval);

    // Initialize interval bucket if missing
    if (!stockHistory.value[interval]) {
      stockHistory.value[interval] = {};
    }

    const historyBucket = { ...stockHistory.value[interval] };
    for (const data of results) {
      historyBucket[data.symbol] = data.history;
    }
    stockHistory.value[interval] = historyBucket;

    if (!forced) lastHistoryFetchTime.value = Date.now();

  } catch (err) {
    console.error("Fetching history failed", err);
  } finally {
    if (!forced) {
        isInitialHistoryLoaded.value = true;
    }
  }
}

// --- Helpers ---

// Is US Market Open (9:30-16:00 America/NY, real end is 16:00 but we use 30min buffer for safety)
const MARKET_OPEN_MIN = 9 * 60 + 30; // 9:30
const MARKET_CLOSE_MIN = 16 * 60; // 16:00
const CLOSE_OFFSET = 30;
const isMarketOpen = (): boolean => {
  const now = new Date();

  // Get NY time values directly
  const nyTime = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour12: false,
    weekday: 'short', 
    hour: 'numeric',
    minute: 'numeric'
  }).formatToParts(now);

  // Extract values
  const getPart = (type: Intl.DateTimeFormatPartTypes) => nyTime.find(p => p.type === type)?.value;
  const day = getPart('weekday');
  const hour = parseInt(getPart('hour') || '0', 10);
  const minute = parseInt(getPart('minute') || '0', 10);

  if (day === 'Sat' || day === 'Sun') return false;
  const currentMins = hour * 60 + minute;
  return currentMins >= MARKET_OPEN_MIN && currentMins < MARKET_CLOSE_MIN + CLOSE_OFFSET;
};

// Check if we missed the closing bell 
const needsClosingFetch = () => {
  if (isMarketOpen()) return false; 

  const now = new Date();
  // Ensure it's a weekday
  const day = now.getDay();
  if (day === 0 || day === 6) return false; 

  // Check if prev quote is older than 45 mins
  const timeSinceLastFetch = Date.now() - lastQuoteFetchTime.value;
  return timeSinceLastFetch > (45 * 60 * 1000); 
};

// Helper to check if we are at polling deadzone -> no data at this window when market open
const isDeadZone = (now = new Date()) => {
  const etNow = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const h = etNow.getHours();
  const m = etNow.getMinutes();
  return h === 9 && m >= 30 && m < 35;
};

const selectStock = async (symbol: string) => {
  if (!isInitialHistoryLoaded.value) return;

  selectedSymbol.value = symbol;
  isDetailLoading.value = true;

  // Force fetch high-res data for selected symbol
  await Promise.all([
    fetchQuotes(true),
    fetchHistory(true)
  ]);
  isDetailLoading.value = false;
};

const clearSelection = () => {
  selectedSymbol.value = null;
};

// --- UI Helpers ---

const getQuote = (symbol: string) => {
  return stockQuotes.value[symbol] || { price: 0, change: 0, changePercent: 0 };
};

const getQuoteChangeColor = (symbol: string) => {
  const change = getQuote(symbol).change;
  if (change > 0) return 'bg-green-500 text-white'; // IOS Green style
  if (change < 0) return 'bg-red-500 text-white';   // IOS Red style
  return 'bg-slate-700 text-slate-300';
};

const getTextChangeColor = (symbol: string) => {
  const change = getQuote(symbol).change;
  if (change > 0) return 'text-green-500';
  if (change < 0) return 'text-red-500';
  return 'text-zinc-400';
};

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
const formatNumber = (val: number) => new Intl.NumberFormat('en-US', { notation: "compact", maximumFractionDigits: 1 }).format(val);

const formatPercentage = (val: number) => {
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(2)}%`;
};

const getHistoryForSymbol = (symbol: string, interval: Interval = '5min'): StockPriceEntry[] => {
  return stockHistory.value[interval]?.[symbol] || [];
};

const generateChartPath = (data: StockPriceEntry[], width: number, height: number) => {
  if (!data || data.length < 2) return '';

  const prices = data.map(d => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  const points = prices.map((price, index) => {
    const x = (index / (prices.length - 1)) * width;
    const normalizedPrice = (price - min) / range;
    // SVG y=0 is top, so we invert
    const y = height - (normalizedPrice * height); 
    return `${x.toFixed(1)} ${y.toFixed(1)}`;
  });

  return `M ${points.join(' L ')}`;
};

const generateAreaPath = (data: StockPriceEntry[], width: number, height: number) => {
  const linePath = generateChartPath(data, width, height);
  if (!linePath) return '';
  // Close the path to create an area (bottom-right -> bottom-left)
  return `${linePath} L ${width} ${height} L 0 ${height} Z`;
};

// Drag Scrolling
const onMouseDown = (e: MouseEvent) => {
  if (!scrollContainer.value) return;
  isDown = true;
  scrollContainer.value.classList.add('active');
  startY = e.pageY - scrollContainer.value.offsetTop;
  scrollTop = scrollContainer.value.scrollTop;
};
const onMouseLeave = () => { isDown = false; scrollContainer.value?.classList.remove('active'); };
const onMouseUp = () => { isDown = false; scrollContainer.value?.classList.remove('active'); };
const onMouseMove = (e: MouseEvent) => {
  if (!isDown || !scrollContainer.value) return;
  e.preventDefault();
  const y = e.pageY - scrollContainer.value.offsetTop;
  const walk = (y - startY) * 2; 
  scrollContainer.value.scrollTop = scrollTop - walk;
};

// --- Lifecycle ---

const QUOTE_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes
const HISTORY_INTERVAL_MS = 15 * 60 * 1000; // 15 minutes
const OFFSET_MS = 2 * 60 * 1000; // 2 minutes
const runScheduler = async () => {
  const active = isMarketOpen();
  const catchup = needsClosingFetch();

  // Return if market is closed and we have fresh enough data
  if (!active && !catchup) return;

  const now = Date.now();
  const timeSinceQuote = now - lastQuoteFetchTime.value;
  const timeSinceHistory = now - lastHistoryFetchTime.value;

  if (timeSinceQuote >= QUOTE_INTERVAL_MS) {
    await fetchQuotes();
    return; // Return to respect the API limit
  }

  // Ensure we are not in deadzone and fetch offset is passed to get history
  const isHistoryDue = timeSinceHistory >= HISTORY_INTERVAL_MS;
  const isSafeOffset = timeSinceQuote >= OFFSET_MS;

  if (isHistoryDue && isSafeOffset && !isDeadZone()) {
     await fetchHistory();
  }
};

const startPolling = () => {
  if (schedulerTimer) clearInterval(schedulerTimer);
  runScheduler();
  schedulerTimer = setInterval(runScheduler, 60000);
};

onMounted(async () => {
  isLoading.value = true;
  await fetchWatchlist();
  
  await fetchQuotes().finally(() => isLoading.value = false);
  
  // API has 8 tokens/min limit, meaning history fetch must be delayed for over 4 symbol watchlist
  const isDelayed = Object.keys(stockWatchlist.value).length >= 4;

  // Handle History with Dynamic Delay
  if (isDeadZone()) {
    // Calculate exact ms remaining until 9:35:05
    const now = new Date();
    const etNow = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
    const minutesWait = 35 - etNow.getMinutes();
    const secondsWait = 60 - etNow.getSeconds();
    let msUntilOpen = ((minutesWait - 1) * 60 * 1000) + (secondsWait * 1000) + 5000;

    // If fetch must also be delayed, ensure msUntilOpen is at least one minute
    if (isDelayed) msUntilOpen = Math.max(msUntilOpen, 60000)
   
    setTimeout(() => {
      fetchHistory();
    }, msUntilOpen); 
  } else {
    setTimeout(() => {
      fetchHistory();
    }, isDelayed ? 60000 : 2000); // 1 min delay if must be delayed, else 2 sec
  }

  startPolling();
});

onUnmounted(() => {
  if (schedulerTimer) clearInterval(schedulerTimer);
});
</script>

<template>
  <div class="h-full bg-black rounded-3xl border border-zinc-800 flex flex-col overflow-hidden relative select-none shadow-2xl transition-all duration-300">
    
    <div v-if="selectedSymbol" class="flex flex-col h-full bg-black relative z-20 min-h-0">
      <div class="px-6 py-3 flex items-center justify-between shrink-0">
        <button 
          @click="clearSelection"
          class="flex items-center justify-center w-8 h-8 -ml-2 rounded-full hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <span class="text-xs font-bold text-zinc-500 uppercase tracking-widest">{{ stockWatchlist[selectedSymbol]?.name }}</span>
        <div class="w-8"></div>
      </div>

      <div v-if="isDetailLoading" class="flex-1 flex items-center justify-center">
        <span class="animate-pulse text-zinc-500 font-medium">Loading {{ selectedSymbol }}...</span>
      </div>

      <div v-else class="flex flex-col flex-1 px-6 pb-4 min-h-0">
        <div class="flex flex-col mb-2 shrink-0">
          <div class="flex items-baseline gap-3">
            <h1 class="text-3xl font-bold text-white tracking-tight">{{ selectedSymbol }}</h1>
            <span class="text-xl font-semibold tracking-tight" :class="getTextChangeColor(selectedSymbol)">
              {{ formatCurrency(getQuote(selectedSymbol).close) }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="getTextChangeColor(selectedSymbol)" class="text-sm font-medium flex items-center">
              <span v-if="getQuote(selectedSymbol).change > 0">▲</span>
              <span v-if="getQuote(selectedSymbol).change < 0">▼</span>
              {{ Math.abs(getQuote(selectedSymbol).change).toFixed(2) }} 
              ({{ formatPercentage(getQuote(selectedSymbol).percent_change) }})
            </span>
            <span class="text-zinc-600 text-xs font-medium">Today</span>
          </div>
        </div>

        <div class="flex-1 w-full min-h-0 relative my-2">
          <svg 
            v-if="getHistoryForSymbol(selectedSymbol, '1min').length > 1" 
            viewBox="0 0 300 150" 
            class="w-full h-full overflow-visible" 
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient :id="'grad-detail-' + selectedSymbol" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" :stop-color="getQuote(selectedSymbol).change >= 0 ? '#22c55e' : '#ef4444'" stop-opacity="0.3"/>
                <stop offset="100%" :stop-color="getQuote(selectedSymbol).change >= 0 ? '#22c55e' : '#ef4444'" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path 
              :d="generateAreaPath(getHistoryForSymbol(selectedSymbol, '1min'), 300, 150)" 
              :fill="'url(#grad-detail-' + selectedSymbol + ')'" 
              class="transition-all duration-500 ease-out"
            />
            <path 
              :d="generateChartPath(getHistoryForSymbol(selectedSymbol, '1min'), 300, 150)" 
              fill="none" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round"
              :class="getQuote(selectedSymbol).change >= 0 ? 'stroke-green-500' : 'stroke-red-500'"
              class="transition-all duration-500 ease-out"
            />
          </svg>
          <div v-else class="w-full h-full border-2 border-dashed border-zinc-800 rounded-xl flex items-center justify-center text-zinc-600 text-xs">
            No intraday data
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mt-auto shrink-0">
          <div class="bg-zinc-900/50 rounded-lg p-2 border border-zinc-800/50 flex flex-col justify-center">
            <span class="block text-zinc-500 text-[10px] font-bold uppercase">High</span>
            <span class="block text-white font-mono text-sm font-medium">{{ formatCurrency(getQuote(selectedSymbol).high) }}</span>
          </div>
          <div class="bg-zinc-900/50 rounded-lg p-2 border border-zinc-800/50 flex flex-col justify-center">
            <span class="block text-zinc-500 text-[10px] font-bold uppercase">Low</span>
            <span class="block text-white font-mono text-sm font-medium">{{ formatCurrency(getQuote(selectedSymbol).low) }}</span>
          </div>
          <div class="bg-zinc-900/50 rounded-lg p-2 border border-zinc-800/50 flex flex-col justify-center">
            <span class="block text-zinc-500 text-[10px] font-bold uppercase">Volume</span>
            <span class="block text-white font-mono text-sm font-medium">{{ formatNumber(getQuote(selectedSymbol).volume) }}</span>
          </div>
          <div class="bg-zinc-900/50 rounded-lg p-2 border border-zinc-800/50 flex flex-col justify-center">
            <span class="block text-zinc-500 text-[10px] font-bold uppercase">Prev Close</span>
            <span class="block text-white font-mono text-sm font-medium">
              {{ formatCurrency(getQuote(selectedSymbol).close - getQuote(selectedSymbol).change) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex flex-col h-full relative">
      <div class="px-6 pt-6 pb-3 bg-black z-10 border-b border-zinc-800 flex-shrink-0">
        <div class="flex justify-between items-end mb-1">
          <h2 class="text-3xl font-bold text-white tracking-tight">Stocks</h2>
          <span class="text-[10px] font-bold uppercase tracking-widest mb-1.5 px-2 py-0.5 rounded"
            :class="isMarketOpen() ? 'text-green-500 bg-green-500/10' : 'text-zinc-500 bg-zinc-800/50'">
            {{ isMarketOpen() ? 'Market Open' : 'Closed' }}
          </span>
        </div>
        <div class="text-sm text-zinc-400 font-semibold tracking-wide">
          {{ new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' }) }}
        </div>
      </div>

      <div 
        ref="scrollContainer"
        class="flex-1 overflow-y-auto cursor-grab active:cursor-grabbing scrollbar-hide relative flex flex-col bg-black"
        @mousedown="onMouseDown"
        @mouseleave="onMouseLeave"
        @mouseup="onMouseUp"
        @mousemove="onMouseMove"
      >
        <div v-if="isLoading" class="flex items-center justify-center h-full text-zinc-500">
          <span class="animate-pulse font-medium">Loading market data...</span>
        </div>

        <div v-else class="flex flex-col min-h-full">
          <ul class="divide-y divide-zinc-800">
            <li 
              v-for="symbol in Object.keys(stockWatchlist)" 
              :key="symbol"
              @click="selectStock(symbol)"
              class="flex items-center justify-between py-4 px-6 transition-all duration-300 group"
              :class="isInitialHistoryLoaded 
                ? 'cursor-pointer hover:bg-zinc-900' 
                : 'cursor-wait opacity-60 grayscale-[0.5]'"
            >
              <div class="w-[28%] flex flex-col">
                <span class="text-lg font-bold text-white tracking-wide transition-colors"
                  :class="{'group-hover:text-blue-400': isInitialHistoryLoaded}">
                  {{ symbol }}
                </span>
                <span class="text-xs text-zinc-500 truncate font-medium tracking-wide">{{ stockWatchlist[symbol].name }}</span>
              </div>

              <div class="w-[32%] h-10 flex items-center justify-center px-2">
                <svg 
                  v-if="getHistoryForSymbol(symbol, '5min').length > 1" 
                  viewBox="0 0 60 20" 
                  class="w-full h-full overflow-visible"
                  preserveAspectRatio="none"
                >
                   <defs>
                    <linearGradient :id="'grad-list-' + symbol" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" :stop-color="getQuote(symbol).change >= 0 ? '#22c55e' : '#ef4444'" stop-opacity="0.3"/>
                      <stop offset="100%" :stop-color="getQuote(symbol).change >= 0 ? '#22c55e' : '#ef4444'" stop-opacity="0"/>
                    </linearGradient>
                  </defs>

                  <path 
                    :d="generateAreaPath(getHistoryForSymbol(symbol, '5min'), 60, 20)" 
                    :fill="'url(#grad-list-' + symbol + ')'" 
                    class="transition-all duration-500 ease-out"
                  />

                  <path 
                    :d="generateChartPath(getHistoryForSymbol(symbol, '5min'), 60, 20)" 
                    fill="none" 
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    :class="getQuote(symbol).change >= 0 ? 'stroke-[#32D74B]' : 'stroke-[#FF453A]'"
                    class="transition-all duration-500 ease-out"
                  />
                </svg>
                <div v-else class="w-1/2 h-[2px] bg-zinc-800 rounded" 
                    :class="isInitialHistoryLoaded ? 'animate-pulse' : 'opacity-30'">
                </div>
              </div>

              <div class="w-[40%] flex flex-col items-end gap-1">
                <span class="text-xl font-bold text-white tabular-nums tracking-tight">
                  {{ formatCurrency(getQuote(symbol).close) }}
                </span>
                <div 
                  class="px-3 py-1 rounded-md text-sm font-bold tabular-nums min-w-[74px] text-center"
                  :class="getQuoteChangeColor(symbol)"
                >
                  {{ formatPercentage(getQuote(symbol).percent_change) }}
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
      
      <div class="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-black to-transparent pointer-events-none z-20"></div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
.scrollbar-hide::-webkit-scrollbar {
  display: none; /* Chrome, Safari and Opera */
}
</style>