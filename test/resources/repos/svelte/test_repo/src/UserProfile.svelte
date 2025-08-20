<script lang="ts">
  import { onMount } from 'svelte';
  import type { User } from './types';
  
  export let name: string;
  export let email: string;
  export let role: string = 'User';
  export let avatar: string | null = null;
  
  let isEditing = false;
  let editedUser: User = { name, email, role };
  let saveStatus: 'idle' | 'saving' | 'saved' | 'error' = 'idle';
  
  // Generate avatar URL if not provided
  $: avatarUrl = avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=ff3e00&color=fff`;
  
  // Validate email format
  $: emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editedUser.email);
  
  function startEdit() {
    isEditing = true;
    editedUser = { name, email, role };
  }
  
  function cancelEdit() {
    isEditing = false;
    editedUser = { name, email, role };
    saveStatus = 'idle';
  }
  
  async function saveProfile() {
    if (!emailValid || !editedUser.name.trim()) {
      saveStatus = 'error';
      return;
    }
    
    saveStatus = 'saving';
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Update props
    name = editedUser.name;
    email = editedUser.email;
    role = editedUser.role;
    
    saveStatus = 'saved';
    isEditing = false;
    
    // Reset status after 2 seconds
    setTimeout(() => {
      saveStatus = 'idle';
    }, 2000);
  }
  
  onMount(() => {
    // Component mounted
    console.log('UserProfile component mounted');
  });
</script>

<div class="profile-card">
  <div class="avatar-section">
    <img src={avatarUrl} alt="{name}'s avatar" class="avatar" />
    {#if !isEditing}
      <button class="edit-btn" on:click={startEdit}>
        Edit Profile
      </button>
    {/if}
  </div>
  
  <div class="info-section">
    {#if isEditing}
      <form on:submit|preventDefault={saveProfile}>
        <div class="form-group">
          <label for="name">Name</label>
          <input
            id="name"
            type="text"
            bind:value={editedUser.name}
            required
            placeholder="Enter your name"
          />
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            type="email"
            bind:value={editedUser.email}
            required
            class:invalid={!emailValid && editedUser.email}
            placeholder="Enter your email"
          />
          {#if !emailValid && editedUser.email}
            <span class="error">Please enter a valid email</span>
          {/if}
        </div>
        
        <div class="form-group">
          <label for="role">Role</label>
          <select id="role" bind:value={editedUser.role}>
            <option value="User">User</option>
            <option value="Developer">Developer</option>
            <option value="Designer">Designer</option>
            <option value="Manager">Manager</option>
            <option value="Admin">Admin</option>
          </select>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="save-btn" disabled={saveStatus === 'saving'}>
            {#if saveStatus === 'saving'}
              Saving...
            {:else}
              Save Changes
            {/if}
          </button>
          <button type="button" class="cancel-btn" on:click={cancelEdit}>
            Cancel
          </button>
        </div>
        
        {#if saveStatus === 'saved'}
          <div class="success-message">Profile saved successfully!</div>
        {:else if saveStatus === 'error'}
          <div class="error-message">Please fix the errors above</div>
        {/if}
      </form>
    {:else}
      <h3 class="name">{name}</h3>
      <p class="email">{email}</p>
      <div class="role-badge">{role}</div>
      
      <div class="stats">
        <div class="stat">
          <span class="stat-label">Member Since</span>
          <span class="stat-value">Jan 2024</span>
        </div>
        <div class="stat">
          <span class="stat-label">Projects</span>
          <span class="stat-value">12</span>
        </div>
        <div class="stat">
          <span class="stat-label">Contributions</span>
          <span class="stat-value">238</span>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .profile-card {
    display: flex;
    gap: 2rem;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    max-width: 600px;
  }
  
  .avatar-section {
    text-align: center;
  }
  
  .avatar {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    margin-bottom: 1rem;
  }
  
  .edit-btn {
    padding: 0.5rem 1rem;
    background: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .edit-btn:hover {
    background: #e63500;
  }
  
  .info-section {
    flex: 1;
  }
  
  .name {
    margin: 0 0 0.5rem 0;
    color: #333;
    font-size: 1.5rem;
  }
  
  .email {
    margin: 0 0 1rem 0;
    color: #666;
  }
  
  .role-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: #ff3e00;
    color: white;
    border-radius: 12px;
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }
  
  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }
  
  .stat {
    text-align: center;
  }
  
  .stat-label {
    display: block;
    font-size: 0.75rem;
    color: #999;
    margin-bottom: 0.25rem;
  }
  
  .stat-value {
    display: block;
    font-size: 1.25rem;
    font-weight: bold;
    color: #333;
  }
  
  /* Form styles */
  form {
    width: 100%;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.25rem;
    color: #666;
    font-size: 0.875rem;
  }
  
  input, select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  input.invalid {
    border-color: #ff6b6b;
  }
  
  .error {
    color: #ff6b6b;
    font-size: 0.75rem;
    margin-top: 0.25rem;
    display: block;
  }
  
  .form-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1.5rem;
  }
  
  .save-btn {
    flex: 1;
    padding: 0.75rem;
    background: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .save-btn:hover:not(:disabled) {
    background: #e63500;
  }
  
  .save-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .cancel-btn {
    flex: 1;
    padding: 0.75rem;
    background: #f5f5f5;
    color: #333;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .cancel-btn:hover {
    background: #e5e5e5;
  }
  
  .success-message {
    margin-top: 1rem;
    padding: 0.75rem;
    background: #d4edda;
    color: #155724;
    border-radius: 4px;
    text-align: center;
  }
  
  .error-message {
    margin-top: 1rem;
    padding: 0.75rem;
    background: #f8d7da;
    color: #721c24;
    border-radius: 4px;
    text-align: center;
  }
</style>