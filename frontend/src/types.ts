export interface TodoTask {
    id: string;
    content: string;
    priority: number;
}

export interface CompletedTask {
    id: string;
    content: string;
    priority: number;
    completed_at: string;
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
    timestamp: string;
    temperature: string;
    icon_code: string;
    icon_url: string;
}


export interface ElectricityPriceInterval {
    time: string;
    price: number;
}

export interface AvgElectricityPrice {
    start_window: string;
    end_window: string;
    average_price: number;
}
