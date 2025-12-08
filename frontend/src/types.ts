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