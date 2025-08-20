<script lang="ts">
  import { onMount } from 'svelte';
  import TodoItem from './TodoItem.svelte';
  import type { Todo } from './types';
  
  let todos: Todo[] = [];
  let newTodoText = '';
  let filter: 'all' | 'active' | 'completed' = 'all';
  let nextId = 1;
  
  // Reactive statements
  $: filteredTodos = filterTodos(todos, filter);
  $: activeTodoCount = todos.filter(t => !t.completed).length;
  $: completedTodoCount = todos.filter(t => t.completed).length;
  $: allCompleted = todos.length > 0 && activeTodoCount === 0;
  
  function filterTodos(todos: Todo[], filter: typeof filter): Todo[] {
    switch (filter) {
      case 'active':
        return todos.filter(t => !t.completed);
      case 'completed':
        return todos.filter(t => t.completed);
      default:
        return todos;
    }
  }
  
  function addTodo() {
    if (newTodoText.trim()) {
      todos = [...todos, {
        id: nextId++,
        text: newTodoText.trim(),
        completed: false,
        createdAt: new Date()
      }];
      newTodoText = '';
    }
  }
  
  function removeTodo(id: number) {
    todos = todos.filter(t => t.id !== id);
  }
  
  function toggleTodo(id: number) {
    todos = todos.map(t => 
      t.id === id ? { ...t, completed: !t.completed } : t
    );
  }
  
  function updateTodoText(id: number, text: string) {
    todos = todos.map(t => 
      t.id === id ? { ...t, text } : t
    );
  }
  
  function clearCompleted() {
    todos = todos.filter(t => !t.completed);
  }
  
  function toggleAll() {
    const shouldComplete = activeTodoCount > 0;
    todos = todos.map(t => ({ ...t, completed: shouldComplete }));
  }
  
  onMount(() => {
    // Load todos from localStorage if available
    const saved = localStorage.getItem('todos');
    if (saved) {
      try {
        todos = JSON.parse(saved);
        nextId = Math.max(...todos.map(t => t.id), 0) + 1;
      } catch (e) {
        console.error('Failed to load todos:', e);
      }
    }
  });
  
  // Save todos to localStorage whenever they change
  $: if (typeof window !== 'undefined') {
    localStorage.setItem('todos', JSON.stringify(todos));
  }
</script>

<div class="todo-list">
  <h3>Todo List</h3>
  
  <div class="input-group">
    <input
      type="text"
      bind:value={newTodoText}
      on:keydown={(e) => e.key === 'Enter' && addTodo()}
      placeholder="What needs to be done?"
      aria-label="New todo"
    />
    <button on:click={addTodo}>Add</button>
  </div>
  
  {#if todos.length > 0}
    <div class="filters">
      <button
        class:active={filter === 'all'}
        on:click={() => filter = 'all'}>
        All ({todos.length})
      </button>
      <button
        class:active={filter === 'active'}
        on:click={() => filter = 'active'}>
        Active ({activeTodoCount})
      </button>
      <button
        class:active={filter === 'completed'}
        on:click={() => filter = 'completed'}>
        Completed ({completedTodoCount})
      </button>
    </div>
    
    <div class="bulk-actions">
      <button on:click={toggleAll}>
        {allCompleted ? 'Uncheck All' : 'Check All'}
      </button>
      {#if completedTodoCount > 0}
        <button on:click={clearCompleted}>
          Clear Completed
        </button>
      {/if}
    </div>
  {/if}
  
  <ul class="todos">
    {#each filteredTodos as todo (todo.id)}
      <TodoItem
        {todo}
        on:toggle={() => toggleTodo(todo.id)}
        on:remove={() => removeTodo(todo.id)}
        on:update={(e) => updateTodoText(todo.id, e.detail)}
      />
    {:else}
      <li class="empty">
        {#if filter === 'all'}
          No todos yet. Add one above!
        {:else if filter === 'active'}
          No active todos.
        {:else}
          No completed todos.
        {/if}
      </li>
    {/each}
  </ul>
</div>

<style>
  .todo-list {
    max-width: 500px;
    margin: 0 auto;
  }
  
  h3 {
    color: #333;
    margin-bottom: 1rem;
  }
  
  .input-group {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .input-group input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  .input-group button {
    padding: 0.75rem 1.5rem;
    background: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .input-group button:hover {
    background: #e63500;
  }
  
  .filters {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .filters button {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .filters button.active {
    background: #ff3e00;
    color: white;
    border-color: #ff3e00;
  }
  
  .bulk-actions {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .bulk-actions button {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
  }
  
  .bulk-actions button:hover {
    background: #f5f5f5;
  }
  
  .todos {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .empty {
    padding: 2rem;
    text-align: center;
    color: #999;
    font-style: italic;
  }
</style>