<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useIntervalFn, useNow } from '@vueuse/core';
import type { Stock, StockQuote, StockHistoryData } from '../types';
import stockService from '../services/stockService';

// Types
type Interval = '1min' | '15min'

// State 
const stockWatchlist = ref<Record<string, Stock>>({});
const stockQuotes = ref<Record<string, StockQuote>>({});
const selectedSymbol = ref<string | null>(null);

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

// Fetch all QUOTES by watchlist or only the selected symbol
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

    // Map live-boards to gtfs_ids
    const quotes: Record<string, StockQuote> = {};
    for (const quote of results) {
      quotes[quote.symbol] = quote;
    }
    stockQuotes.value = quotes;
  } catch (err) {
    console.error("Failed to update quotes", err);
  }
}

</script>