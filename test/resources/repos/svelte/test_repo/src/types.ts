// Type definitions for the Svelte test repository

export interface Todo {
  id: number;
  text: string;
  completed: boolean;
  createdAt: Date;
}

export interface User {
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

export interface CalculatorState {
  display: string;
  previousValue: number | null;
  operation: string | null;
  waitingForNewValue: boolean;
}

export type FilterType = 'all' | 'active' | 'completed';

export type ViewType = 'counter' | 'todo' | 'calculator' | 'profile';

// Custom events
export interface CounterEvents {
  change: number;
  reset: void;
}

export interface TodoEvents {
  toggle: void;
  remove: void;
  update: string;
}