<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let initialValue: number = 0;
  export let step: number = 1;
  export let min: number | undefined = undefined;
  export let max: number | undefined = undefined;
  
  let count = initialValue;
  
  const dispatch = createEventDispatcher<{
    change: number;
    reset: void;
  }>();
  
  function increment() {
    if (max === undefined || count + step <= max) {
      count += step;
      dispatch('change', count);
    }
  }
  
  function decrement() {
    if (min === undefined || count - step >= min) {
      count -= step;
      dispatch('change', count);
    }
  }
  
  function reset() {
    count = initialValue;
    dispatch('reset');
    dispatch('change', count);
  }
  
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value);
    if (!isNaN(value)) {
      if (min !== undefined && value < min) {
        count = min;
      } else if (max !== undefined && value > max) {
        count = max;
      } else {
        count = value;
      }
      dispatch('change', count);
    }
  }
  
  // Reactive statements
  $: isAtMin = min !== undefined && count <= min;
  $: isAtMax = max !== undefined && count >= max;
  $: displayValue = count.toLocaleString();
</script>

<div class="counter">
  <h3>Counter Component</h3>
  
  <div class="display">
    <span class="label">Current Value:</span>
    <span class="value">{displayValue}</span>
  </div>
  
  <div class="controls">
    <button 
      on:click={decrement} 
      disabled={isAtMin}
      aria-label="Decrement">
      -
    </button>
    
    <input 
      type="number" 
      bind:value={count}
      on:input={handleInput}
      {min}
      {max}
      aria-label="Counter value"
    />
    
    <button 
      on:click={increment} 
      disabled={isAtMax}
      aria-label="Increment">
      +
    </button>
  </div>
  
  <div class="actions">
    <button on:click={reset} class="reset-btn">
      Reset to {initialValue}
    </button>
  </div>
  
  {#if min !== undefined || max !== undefined}
    <div class="limits">
      {#if min !== undefined}
        <span>Min: {min}</span>
      {/if}
      {#if max !== undefined}
        <span>Max: {max}</span>
      {/if}
    </div>
  {/if}
</div>

<style>
  .counter {
    padding: 1.5rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
    max-width: 400px;
  }
  
  h3 {
    margin: 0 0 1rem 0;
    color: #333;
  }
  
  .display {
    text-align: center;
    margin-bottom: 1rem;
  }
  
  .label {
    display: block;
    font-size: 0.875rem;
    color: #666;
    margin-bottom: 0.25rem;
  }
  
  .value {
    display: block;
    font-size: 2rem;
    font-weight: bold;
    color: #ff3e00;
  }
  
  .controls {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-bottom: 1rem;
  }
  
  .controls button {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
    border: 1px solid #ddd;
    background: white;
    cursor: pointer;
    border-radius: 4px;
  }
  
  .controls button:hover:not(:disabled) {
    background: #f0f0f0;
  }
  
  .controls button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  input[type="number"] {
    width: 100px;
    padding: 0.5rem;
    text-align: center;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  .actions {
    text-align: center;
    margin-bottom: 1rem;
  }
  
  .reset-btn {
    padding: 0.5rem 1rem;
    background: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .reset-btn:hover {
    background: #e63500;
  }
  
  .limits {
    display: flex;
    justify-content: center;
    gap: 2rem;
    font-size: 0.875rem;
    color: #666;
  }
</style>