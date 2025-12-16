export interface TodoTask {
    id: string;
    content: string;
    priority: number;
}

export interface CompletedTask {
    id: string;
    content: string;
    priority: number;
    completed_at: string; // ISO 8601 string (UTC)
}


export interface CurrentWeather {
    temperature: number;
    temperature_feels_like: number;
    humidity: number;
    wind_speed: number;
    description: string;
    icon_code: string;
    icon_url: string;
}

export interface HourlyWeather {
    timestamp: string; // ISO 8601 string (UTC)
    temperature: string;
    icon_code: string;
    icon_url: string;
}


export interface ElectricityPriceInterval {
    time: string; // ISO 8601 string (UTC)
    price: number;
}

export interface AvgElectricityPrice {
    start_window: string; // ISO 8601 string (UTC)
    end_window: string; // ISO 8601 string (UTC)
    average_price: number;
}


export interface StopWatchlist {
    gtfs_id: string;
    custom_name: string;
    original_name: string | null;
}

export interface StopTimeEntry {
    arrival_time: string; // ISO 8601 string (UTC)
    headsign: string;
    route: string;
}

export interface StopTimetable {
    gtfs_id: string;
    name: string;
    timetable: StopTimeEntry[];
}


export interface Stock {
    symbol: string;
    name: string | null;
}

export interface StockQuote {
    symbol: string;
    name: string;
    close: number;
    change: number;
    percent_change: number;
    high: number;
    low: number;
    volume: number;
    timestamp: string; // ISO 8601 string (UTC)
}

export interface StockPriceEntry {
    symbol: string;
    interval: string;
    timestamp: string; // ISO 8601 string (UTC)
    price: number;
}

export interface StockHistoryData {
    symbol: string;
    history: StockPriceEntry[];
}


export interface SensorData {
    mac: string;
    humidity: number;
    temperature: number;
    pressure: number;
    battery: number;
    rssi: number;
    timestamp: string; // ISO 8601 string (UTC)
}
