<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
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
const MARKET_OPEN_MIN = 9 * 60 + 30; // 9:30
const MARKET_CLOSE_MIN = 16 * 60; // 16:00
const CLOSE_OFFSET = 60; // 1h offset
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
  const getPart = (type: Intl.DateTimeFormatPartTypes) => 
    nyTime.find(p => p.type === type)?.value;

  const day = getPart('weekday');
  const hour = parseInt(getPart('hour') || '0', 10);
  const minute = parseInt(getPart('minute') || '0', 10);

  // Only open during weekdays
  if (day === 'Sat' || day === 'Sun') return false;

  const currentMins = hour * 60 + minute;
  return currentMins >= MARKET_OPEN_MIN && currentMins < MARKET_CLOSE_MIN + CLOSE_OFFSET;
};

// --- UI Helpers ---

const MIN_ROWS = 6;
const getPlaceholderCount = () => {
    const currentCount = Object.keys(stockWatchlist.value).length;
    return Math.max(0, MIN_ROWS - currentCount);
};

const getQuote = (symbol: string) => {
  return stockQuotes.value[symbol] || { price: 0, change: 0, changePercent: 0 };
};

const getQuoteChangeColor = (symbol: string) => {
  const change = getQuote(symbol).change;
  if (change > 0) return 'bg-green-500 text-white'; // IOS Green style
  if (change < 0) return 'bg-red-500 text-white';   // IOS Red style
  return 'bg-slate-700 text-slate-300';
};

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
};

const formatPercentage = (val: number) => {
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(2)}%`;
};

const getHistoryForSymbol = (symbol: string): StockPriceEntry[] => {
  // Default to 15min interval for list view
  return stockHistory.value['15min']?.[symbol] || [];
};

const generateSparkline = (data: StockPriceEntry[]) => {
  if (!data || data.length < 2) return '';

  const prices = data.map(d => d.price); // Handle potential structure diffs
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;

  // SVG Dimension: 60 x 20
  const width = 60;
  const height = 20;

  // Generate Points
  const points = prices.map((price, index) => {
    const x = (index / (prices.length - 1)) * width;
    const normalizedPrice = (price - min) / range;
    const y = height - (normalizedPrice * height); 
    return `${x.toFixed(1)} ${y.toFixed(1)}`;
  });

  return `M ${points.join(' L ')}`;
};

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
const HISTORY_OFFSET_MIN = 2;
const runScheduler = async () => {
  if (!isMarketOpen()) return;
  const now = new Date();
  const minutes = now.getMinutes();

  if (minutes % QUOTE_INTERVAL_MIN === 0) {
    await fetchQuotes();
  }

  if (minutes % HISTORY_INTERVAL_MIN === HISTORY_OFFSET_MIN) {
    await fetchHistory();
  }
};

const startPolling = () => {
  if (schedulerTimer) clearInterval(schedulerTimer);
  
  // Sync to next minute
  const msToNextMinute = 60000 - (new Date().getTime() % 60000);

  // Add small jitter
  const jitter = Math.floor(Math.random() * 5000);
  
  setTimeout(() => {
    runScheduler();
    schedulerTimer = setInterval(runScheduler, 60000);
  }, msToNextMinute + jitter);
};

onMounted(async () => {
  isLoading.value = true;
  await fetchWatchlist();
  
  // Initial Fetch on Mount
  await fetchQuotes().finally(() => isLoading.value = false);
  
  // Fetch history with 1-min delay
  setTimeout(async () => {
    await fetchHistory();
    startPolling(); 
  }, 60000); 
});

onUnmounted(() => {
  if (schedulerTimer) clearInterval(schedulerTimer);
});
</script>

<template>
  <div class="h-full bg-black rounded-3xl border border-zinc-800 flex flex-col overflow-hidden relative select-none shadow-2xl">
    
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
            class="flex items-center justify-between py-4 px-6 hover:bg-zinc-900 transition-colors group"
          >
            <div class="w-[28%] flex flex-col">
              <span class="text-lg font-bold text-white tracking-wide">{{ symbol }}</span>
              <span class="text-xs text-zinc-500 truncate font-medium tracking-wide">{{ stockWatchlist[symbol].name }}</span>
            </div>

            <div class="w-[32%] h-10 flex items-center justify-center px-2">
              <svg 
                v-if="getHistoryForSymbol(symbol).length > 1" 
                viewBox="0 0 60 20" 
                class="w-full h-full overflow-visible"
                preserveAspectRatio="none"
              >
                <path 
                  :d="generateSparkline(getHistoryForSymbol(symbol))" 
                  fill="none" 
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :class="getQuote(symbol).change >= 0 ? 'stroke-[#32D74B]' : 'stroke-[#FF453A]'"
                />
              </svg>
              <div v-else class="w-1/2 h-[2px] bg-zinc-800 rounded animate-pulse"></div>
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

        <div class="flex-1 flex flex-col bg-black">
             <div 
               v-for="n in getPlaceholderCount()" 
               :key="n"
               class="border-b border-zinc-800 h-[80px] w-full"
             ></div>
        </div>
      </div>
    </div>
    
    <div class="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-black to-transparent pointer-events-none z-20"></div>
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