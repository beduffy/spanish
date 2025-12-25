<template>
  <nav>
    <router-link to="/">Review Cards</router-link> | 
    <router-link to="/cards">All Cards</router-link> |
    <router-link to="/dashboard">Dashboard</router-link> |
    <router-link to="/calendar">Calendar</router-link>
    <span v-if="user" class="user-info">
      | Logged in as {{ user.email }}
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
      user: null
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
        this.$router.push('/')
      } catch (error) {
        console.error('Logout error:', error)
      }
    }
  },
  async mounted() {
    await this.checkUser()
    // Listen for auth state changes
    SupabaseService.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        this.checkUser()
      } else if (event === 'SIGNED_OUT') {
        this.user = null
      }
    })
  }
}
</script>

<style>
#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}

.user-info {
  margin-left: auto;
}

.logout-btn {
  margin-left: 10px;
  padding: 5px 10px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.logout-btn:hover {
  background-color: #c82333;
}
</style>
