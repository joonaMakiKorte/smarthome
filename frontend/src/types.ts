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
    windSpeed: number;
    description: string;
    icon_code: string;
    icon_url: string;
}