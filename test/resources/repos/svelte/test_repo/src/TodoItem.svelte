<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Todo } from './types';
  
  export let todo: Todo;
  
  let editing = false;
  let editText = todo.text;
  
  const dispatch = createEventDispatcher<{
    toggle: void;
    remove: void;
    update: string;
  }>();
  
  function startEdit() {
    editing = true;
    editText = todo.text;
  }
  
  function saveEdit() {
    if (editText.trim() && editText !== todo.text) {
      dispatch('update', editText.trim());
    }
    editing = false;
  }
  
  function cancelEdit() {
    editText = todo.text;
    editing = false;
  }
  
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      saveEdit();
    } else if (event.key === 'Escape') {
      cancelEdit();
    }
  }
</script>

<li class="todo-item" class:completed={todo.completed}>
  {#if editing}
    <input
      type="text"
      bind:value={editText}
      on:keydown={handleKeydown}
      on:blur={saveEdit}
      class="edit-input"
      autofocus
    />
  {:else}
    <label class="todo-content">
      <input
        type="checkbox"
        checked={todo.completed}
        on:change={() => dispatch('toggle')}
      />
      <span class="text" on:dblclick={startEdit}>
        {todo.text}
      </span>
    </label>
    <div class="actions">
      <button 
        class="edit-btn" 
        on:click={startEdit}
        aria-label="Edit todo">
        ✏️
      </button>
      <button 
        class="remove-btn" 
        on:click={() => dispatch('remove')}
        aria-label="Remove todo">
        🗑️
      </button>
    </div>
  {/if}
</li>

<style>
  .todo-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border: 1px solid #eee;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    background: white;
    transition: opacity 0.2s;
  }
  
  .todo-item.completed {
    opacity: 0.6;
  }
  
  .todo-content {
    flex: 1;
    display: flex;
    align-items: center;
    cursor: pointer;
  }
  
  .todo-content input[type="checkbox"] {
    margin-right: 0.75rem;
    cursor: pointer;
  }
  
  .text {
    flex: 1;
    user-select: none;
  }
  
  .completed .text {
    text-decoration: line-through;
    color: #999;
  }
  
  .actions {
    display: flex;
    gap: 0.25rem;
  }
  
  .actions button {
    padding: 0.25rem 0.5rem;
    border: none;
    background: none;
    cursor: pointer;
    font-size: 1rem;
    opacity: 0.6;
    transition: opacity 0.2s;
  }
  
  .actions button:hover {
    opacity: 1;
  }
  
  .edit-input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #ff3e00;
    border-radius: 4px;
    font-size: 1rem;
  }
</style>