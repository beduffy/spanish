import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Initialize theme before app mounts to prevent flash
(function initTheme() {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light')
  } else {
    document.documentElement.setAttribute('data-theme', 'dark')  // Default to dark mode
  }
})()

createApp(App).use(router).mount('#app')
