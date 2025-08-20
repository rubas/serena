<script lang="ts">
  let display = '0';
  let previousValue: number | null = null;
  let operation: string | null = null;
  let waitingForNewValue = false;
  
  const operations: Record<string, (a: number, b: number) => number> = {
    '+': (a, b) => a + b,
    '-': (a, b) => a - b,
    '*': (a, b) => a * b,
    '/': (a, b) => a / b,
    '%': (a, b) => a % b,
    '^': (a, b) => Math.pow(a, b)
  };
  
  function handleNumber(num: string) {
    if (waitingForNewValue) {
      display = num;
      waitingForNewValue = false;
    } else {
      display = display === '0' ? num : display + num;
    }
  }
  
  function handleDecimal() {
    if (waitingForNewValue) {
      display = '0.';
      waitingForNewValue = false;
    } else if (!display.includes('.')) {
      display += '.';
    }
  }
  
  function handleOperation(op: string) {
    const current = parseFloat(display);
    
    if (previousValue !== null && operation && !waitingForNewValue) {
      const result = operations[operation](previousValue, current);
      display = String(result);
      previousValue = result;
    } else {
      previousValue = current;
    }
    
    operation = op;
    waitingForNewValue = true;
  }
  
  function calculate() {
    if (previousValue !== null && operation) {
      const current = parseFloat(display);
      const result = operations[operation](previousValue, current);
      display = String(result);
      previousValue = null;
      operation = null;
      waitingForNewValue = true;
    }
  }
  
  function clear() {
    display = '0';
    previousValue = null;
    operation = null;
    waitingForNewValue = false;
  }
  
  function clearEntry() {
    display = '0';
    waitingForNewValue = false;
  }
  
  function toggleSign() {
    display = String(-parseFloat(display));
  }
  
  function handlePercent() {
    display = String(parseFloat(display) / 100);
  }
  
  function handleSquareRoot() {
    display = String(Math.sqrt(parseFloat(display)));
  }
  
  function handleKeypress(event: KeyboardEvent) {
    if (event.key >= '0' && event.key <= '9') {
      handleNumber(event.key);
    } else if (event.key === '.') {
      handleDecimal();
    } else if (event.key in operations) {
      handleOperation(event.key);
    } else if (event.key === 'Enter' || event.key === '=') {
      calculate();
    } else if (event.key === 'Escape') {
      clear();
    } else if (event.key === 'Backspace') {
      if (display.length > 1) {
        display = display.slice(0, -1);
      } else {
        display = '0';
      }
    }
  }
</script>

<svelte:window on:keydown={handleKeypress} />

<div class="calculator">
  <div class="display">
    {#if operation}
      <div class="operation-indicator">{operation}</div>
    {/if}
    <div class="value">{display}</div>
  </div>
  
  <div class="buttons">
    <button class="function" on:click={clear}>C</button>
    <button class="function" on:click={clearEntry}>CE</button>
    <button class="function" on:click={toggleSign}>+/-</button>
    <button class="operator" on:click={() => handleOperation('/')}>÷</button>
    
    <button class="number" on:click={() => handleNumber('7')}>7</button>
    <button class="number" on:click={() => handleNumber('8')}>8</button>
    <button class="number" on:click={() => handleNumber('9')}>9</button>
    <button class="operator" on:click={() => handleOperation('*')}>×</button>
    
    <button class="number" on:click={() => handleNumber('4')}>4</button>
    <button class="number" on:click={() => handleNumber('5')}>5</button>
    <button class="number" on:click={() => handleNumber('6')}>6</button>
    <button class="operator" on:click={() => handleOperation('-')}>−</button>
    
    <button class="number" on:click={() => handleNumber('1')}>1</button>
    <button class="number" on:click={() => handleNumber('2')}>2</button>
    <button class="number" on:click={() => handleNumber('3')}>3</button>
    <button class="operator" on:click={() => handleOperation('+')}>+</button>
    
    <button class="function" on:click={handlePercent}>%</button>
    <button class="number" on:click={() => handleNumber('0')}>0</button>
    <button class="number" on:click={handleDecimal}>.</button>
    <button class="equals" on:click={calculate}>=</button>
    
    <button class="function" on:click={handleSquareRoot}>√</button>
    <button class="operator" on:click={() => handleOperation('^')}>^</button>
    <button class="operator" on:click={() => handleOperation('%')}>mod</button>
    <button class="function" disabled>π</button>
  </div>
</div>

<style>
  .calculator {
    max-width: 320px;
    margin: 0 auto;
    padding: 1rem;
    background: #2d2d2d;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  }
  
  .display {
    background: #444;
    color: white;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 8px;
    text-align: right;
    min-height: 60px;
    position: relative;
  }
  
  .operation-indicator {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
    font-size: 0.875rem;
    color: #ff3e00;
  }
  
  .value {
    font-size: 2rem;
    font-weight: 300;
    word-wrap: break-word;
    word-break: break-all;
  }
  
  .buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
  }
  
  button {
    padding: 1.25rem;
    font-size: 1.25rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  button:hover {
    transform: translateY(-2px);
  }
  
  button:active {
    transform: translateY(0);
  }
  
  .number {
    background: #666;
    color: white;
  }
  
  .number:hover {
    background: #777;
  }
  
  .operator {
    background: #ff6b35;
    color: white;
  }
  
  .operator:hover {
    background: #ff8555;
  }
  
  .function {
    background: #555;
    color: white;
  }
  
  .function:hover {
    background: #666;
  }
  
  .equals {
    background: #ff3e00;
    color: white;
  }
  
  .equals:hover {
    background: #ff5a20;
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  button:disabled:hover {
    transform: none;
  }
</style>