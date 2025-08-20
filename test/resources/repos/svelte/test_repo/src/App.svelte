<script lang="ts">
  import Counter from './Counter.svelte';
  import TodoList from './TodoList.svelte';
  import Calculator from './Calculator.svelte';
  import UserProfile from './UserProfile.svelte';
  
  let appName = 'Svelte Test Application';
  let currentView: 'counter' | 'todo' | 'calculator' | 'profile' = 'counter';
  
  function changeView(view: typeof currentView) {
    currentView = view;
  }
  
  // Example of reactive statement
  $: viewTitle = currentView.charAt(0).toUpperCase() + currentView.slice(1);
</script>

<main>
  <header>
    <h1>{appName}</h1>
    <nav>
      <button 
        class:active={currentView === 'counter'} 
        on:click={() => changeView('counter')}>
        Counter
      </button>
      <button 
        class:active={currentView === 'todo'} 
        on:click={() => changeView('todo')}>
        Todo List
      </button>
      <button 
        class:active={currentView === 'calculator'} 
        on:click={() => changeView('calculator')}>
        Calculator
      </button>
      <button 
        class:active={currentView === 'profile'} 
        on:click={() => changeView('profile')}>
        Profile
      </button>
    </nav>
  </header>
  
  <section class="content">
    <h2>{viewTitle} Component</h2>
    
    {#if currentView === 'counter'}
      <Counter initialValue={0} />
    {:else if currentView === 'todo'}
      <TodoList />
    {:else if currentView === 'calculator'}
      <Calculator />
    {:else if currentView === 'profile'}
      <UserProfile 
        name="John Doe" 
        email="john@example.com" 
        role="Developer" 
      />
    {/if}
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  }
  
  main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  header {
    border-bottom: 2px solid #eee;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
  }
  
  h1 {
    color: #ff3e00;
    margin: 0 0 1rem 0;
  }
  
  nav {
    display: flex;
    gap: 1rem;
  }
  
  button {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    background: white;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
  }
  
  button:hover {
    background: #f5f5f5;
  }
  
  button.active {
    background: #ff3e00;
    color: white;
    border-color: #ff3e00;
  }
  
  .content {
    min-height: 400px;
  }
  
  h2 {
    color: #333;
    margin-bottom: 1.5rem;
  }
</style>