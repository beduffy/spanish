<template>
  <div v-if="user" class="greeting">
    Hello {{ user.email }}
  </div>
  <nav>
    <router-link to="/">Review Cards</router-link> | 
    <router-link to="/cards">All Cards</router-link> |
    <router-link to="/dashboard">Dashboard</router-link> |
    <router-link to="/reader">Reader</router-link> |
    <router-link to="/calendar">Calendar</router-link>
    <span v-if="user" class="user-info">
      <button @click="toggleTheme" class="theme-toggle-btn" :title="isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'">
        {{ isDarkMode ? '☀️' : '🌙' }}
      </button>
      <button @click="handleLogout" class="logout-btn">Logout</button>
    </span>
  </nav>
  <router-view/>
</template>

<script>
import SupabaseService from '@/services/SupabaseService'

export default {
  name: 'App',
  data() {
    return {
      user: null,
      isDarkMode: true  // Default to dark mode
    }
  },
  methods: {
    async checkUser() {
      try {
        const currentUser = await SupabaseService.getUser()
        this.user = currentUser
      } catch (error) {
        this.user = null
      }
    },
    async handleLogout() {
      try {
        await SupabaseService.signOut()
        this.user = null
        this.$router.push('/login')
      } catch (error) {
        console.error('Logout error:', error)
      }
    },
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode
      this.applyTheme()
      localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light')
    },
    applyTheme() {
      if (this.isDarkMode) {
        document.documentElement.setAttribute('data-theme', 'dark')
      } else {
        document.documentElement.setAttribute('data-theme', 'light')
      }
    },
    initTheme() {
      // Check localStorage, default to dark mode
      const savedTheme = localStorage.getItem('theme')
      if (savedTheme === 'light') {
        this.isDarkMode = false
      } else {
        this.isDarkMode = true  // Default to dark mode
      }
      this.applyTheme()
    }
  },
  async mounted() {
    this.initTheme()
    await this.checkUser()
    // Listen for auth state changes
    SupabaseService.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        this.checkUser()
        // Redirect to intended page if there was a redirect query param
        const redirect = this.$route.query.redirect
        if (redirect) {
          this.$router.push(redirect)
        } else if (this.$route.name === 'Login') {
          this.$router.push('/')
        }
      } else if (event === 'SIGNED_OUT') {
        this.user = null
        // Redirect to login if on a protected page
        if (this.$route.meta.requiresAuth) {
          this.$router.push('/login')
        }
      }
    })
  }
}
</script>

<style>
/* CSS Variables for Dark Mode (default) */
:root {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --bg-tertiary: #3d3d3d;
  --text-primary: #e0e0e0;
  --text-secondary: #b0b0b0;
  --text-tertiary: #888;
  --border-color: #444;
  --accent-color: #42b983;
  --accent-hover: #35a372;
  --link-color: #42b983;
  --link-active: #35a372;
  --error-color: #ff6b6b;
  --error-bg: #3d2525;
  --success-color: #51cf66;
  --success-bg: #253d2a;
  --warning-color: #ffd43b;
  --card-bg: #2d2d2d;
  --card-border: #444;
  --input-bg: #2d2d2d;
  --input-border: #444;
  --button-primary: #007bff;
  --button-primary-hover: #0056b3;
  --button-danger: #dc3545;
  --button-danger-hover: #c82333;
  --shadow: rgba(0, 0, 0, 0.3);
  --token-hover-bg: #2d4a5e;
  --token-clicked-bg: #3d5a6e;
  --token-added-bg: #2d4a2d;
  --token-added-border: #4caf50;
  --spinner-border: #444;
  --spinner-top: #007bff;
  --audio-controls-bg: #2d2d2d;
  --audio-progress-bg: #444;
  --audio-progress-hover: #555;
  --warning-bg: #4d3d1d;
  --warning-text: #ffd43b;
}

/* CSS Variables for Light Mode */
[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --bg-tertiary: #f0f0f0;
  --text-primary: #2c3e50;
  --text-secondary: #555;
  --text-tertiary: #666;
  --border-color: #ddd;
  --accent-color: #42b983;
  --accent-hover: #35a372;
  --link-color: #2c3e50;
  --link-active: #42b983;
  --error-color: #c00;
  --error-bg: #ffe0e0;
  --success-color: #155724;
  --success-bg: #d4edda;
  --warning-color: #ffc107;
  --card-bg: #ffffff;
  --card-border: #ccc;
  --input-bg: #ffffff;
  --input-border: #ccc;
  --button-primary: #007bff;
  --button-primary-hover: #0056b3;
  --button-danger: #dc3545;
  --button-danger-hover: #c82333;
  --shadow: rgba(0, 0, 0, 0.1);
  --token-hover-bg: #e3f2fd;
  --token-clicked-bg: #bbdefb;
  --token-added-bg: #c8e6c9;
  --token-added-border: #4caf50;
  --spinner-border: #f3f3f3;
  --spinner-top: #007bff;
  --audio-controls-bg: #f5f5f5;
  --audio-progress-bg: #ddd;
  --audio-progress-hover: #ccc;
  --warning-bg: #fff3cd;
  --warning-text: #856404;
}

/* Apply background to body and html */
html, body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  min-height: 100vh;
  transition: background-color 0.3s ease, color 0.3s ease;
}

nav {
  padding: 30px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

nav a {
  font-weight: bold;
  color: var(--link-color);
  text-decoration: none;
  transition: color 0.2s ease;
}

nav a:hover {
  color: var(--accent-hover);
}

nav a.router-link-exact-active {
  color: var(--accent-color);
}

.greeting {
  background-color: var(--bg-secondary);
  padding: 15px;
  text-align: center;
  font-size: 1.2em;
  font-weight: bold;
  color: var(--text-primary);
  border-bottom: 2px solid var(--accent-color);
}

.user-info {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.theme-toggle-btn {
  padding: 5px 10px;
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2em;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.theme-toggle-btn:hover {
  background-color: var(--bg-secondary);
  border-color: var(--accent-color);
}

.logout-btn {
  padding: 5px 10px;
  background-color: var(--button-danger);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.2s ease;
}

.logout-btn:hover {
  background-color: var(--button-danger-hover);
}
</style>
