import { createClient } from '@supabase/supabase-js'

// Supabase configuration - reads from root .env file
// Vue CLI requires VUE_APP_ prefix, but vue.config.js maps SUPABASE_* to VUE_APP_SUPABASE_*
const supabaseUrl = process.env.VUE_APP_SUPABASE_URL || ''
const supabaseAnonKey = process.env.VUE_APP_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase URL or Anon Key not configured. Set VUE_APP_SUPABASE_URL and VUE_APP_SUPABASE_ANON_KEY in .env')
}

// For tests/Cypress: provide mock values if env vars are not set
const finalSupabaseUrl = supabaseUrl || 'https://mock.supabase.co'
const finalSupabaseAnonKey = supabaseAnonKey || 'mock-anon-key-for-testing'

export const supabase = createClient(finalSupabaseUrl, finalSupabaseAnonKey)

export default {
  async signIn(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
    return data
  },

  async signUp(email, password) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    if (error) throw error
    return data
  },

  async signOut() {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  },

  async getSession() {
    // Check for Cypress mock session in test mode
    if (typeof window !== 'undefined' && window.__CYPRESS_MOCK_SESSION__) {
      return window.__CYPRESS_MOCK_SESSION__
    }
    const { data: { session }, error } = await supabase.auth.getSession()
    if (error) throw error
    return session
  },

  async getUser() {
    // Check for Cypress mock session in test mode
    if (typeof window !== 'undefined' && window.__CYPRESS_MOCK_SESSION__) {
      return window.__CYPRESS_MOCK_SESSION__.user
    }
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error) throw error
    return user
  },

  onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(callback)
  },

  async getAccessToken() {
    // Get current session and return access token
    // Use getSession() which gets the current session synchronously from memory
    // If that fails, try getUser() which forces a refresh
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) {
        return session.access_token
      }
      // If no session, try getUser which may trigger a refresh
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        const { data: { session: refreshedSession } } = await supabase.auth.getSession()
        return refreshedSession?.access_token || null
      }
      return null
    } catch (error) {
      console.warn('Error getting access token:', error)
      return null
    }
  }
}
