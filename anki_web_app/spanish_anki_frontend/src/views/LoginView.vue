<template>
  <div class="login-view">
    <div class="login-container">
      <h1>Login</h1>
      
      <div v-if="errorMessage" class="error-message">
        <p>{{ errorMessage }}</p>
      </div>
      
      <div v-if="successMessage" class="success-message">
        <p>{{ successMessage }}</p>
      </div>

      <form @submit.prevent="handleSubmit" v-if="!isSignUp">
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" v-model="email" required />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input type="password" id="password" v-model="password" required />
        </div>
        
        <button type="submit" :disabled="isLoading" class="btn btn-primary">
          {{ isLoading ? 'Logging in...' : 'Login' }}
        </button>
        
        <p class="switch-mode">
          Don't have an account? 
          <a href="#" @click.prevent="isSignUp = true">Sign up</a>
        </p>
      </form>

      <form @submit.prevent="handleSignUp" v-if="isSignUp">
        <div class="form-group">
          <label for="signup-email">Email</label>
          <input type="email" id="signup-email" v-model="email" required />
        </div>
        
        <div class="form-group">
          <label for="signup-password">Password</label>
          <input type="password" id="signup-password" v-model="password" required minlength="6" />
          <small>Password must be at least 6 characters</small>
        </div>
        
        <button type="submit" :disabled="isLoading" class="btn btn-primary">
          {{ isLoading ? 'Signing up...' : 'Sign Up' }}
        </button>
        
        <p class="switch-mode">
          Already have an account? 
          <a href="#" @click.prevent="isSignUp = false">Login</a>
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import SupabaseService from '@/services/SupabaseService';

export default {
  name: 'LoginView',
  data() {
    return {
      email: '',
      password: '',
      isLoading: false,
      errorMessage: '',
      successMessage: '',
      isSignUp: false
    };
  },
  methods: {
    async handleSubmit() {
      this.isLoading = true;
      this.errorMessage = '';
      this.successMessage = '';
      
      try {
        await SupabaseService.signIn(this.email, this.password);
        this.successMessage = 'Login successful! Redirecting...';
        // Wait a bit longer to ensure session is fully established
        // and trigger auth state change
        await new Promise(resolve => setTimeout(resolve, 500));
        // Redirect to intended page or home after successful login
        const redirect = this.$route.query.redirect || '/';
        this.$router.push(redirect);
      } catch (error) {
        this.errorMessage = error.message || 'Failed to login. Please check your credentials.';
      } finally {
        this.isLoading = false;
      }
    },
    async handleSignUp() {
      this.isLoading = true;
      this.errorMessage = '';
      this.successMessage = '';
      
      try {
        await SupabaseService.signUp(this.email, this.password);
        this.successMessage = 'Sign up successful! Please check your email to verify your account, then login.';
        // Switch back to login form after a delay
        setTimeout(() => {
          this.isSignUp = false;
        }, 3000);
      } catch (error) {
        this.errorMessage = error.message || 'Failed to sign up. Please try again.';
      } finally {
        this.isLoading = false;
      }
    }
  }
};
</script>

<style scoped>
.login-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 20px;
}

.login-container {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 40px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 2px 4px var(--shadow);
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: var(--text-primary);
}

input[type="email"],
input[type="password"] {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 4px;
  font-size: 1em;
  box-sizing: border-box;
  background-color: var(--input-bg);
  color: var(--text-primary);
}

small {
  display: block;
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 0.85em;
}

.btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-size: 1em;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: var(--button-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--button-primary-hover);
}

.btn-primary:disabled {
  background-color: var(--bg-tertiary);
  cursor: not-allowed;
}

.switch-mode {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
}

.switch-mode a {
  color: var(--link-color);
  text-decoration: none;
}

.switch-mode a:hover {
  text-decoration: underline;
}

.error-message,
.success-message {
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  text-align: center;
}

.error-message {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.success-message {
  background-color: var(--success-bg);
  color: var(--success-color);
}
</style>
