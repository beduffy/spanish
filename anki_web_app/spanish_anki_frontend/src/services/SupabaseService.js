import { createClient } from '@supabase/supabase-js'

// Supabase configuration - reads from root .env file
// Vue CLI requires VUE_APP_ prefix, but vue.config.js maps SUPABASE_* to VUE_APP_SUPABASE_*
const supabaseUrl = process.env.VUE_APP_SUPABASE_URL || ''
const supabaseAnonKey = process.env.VUE_APP_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase URL or Anon Key not configured. Set VUE_APP_SUPABASE_URL and VUE_APP_SUPABASE_ANON_KEY in .env')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

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
    const { data: { session }, error } = await supabase.auth.getSession()
    if (error) throw error
    return session
  },

  async getUser() {
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error) throw error
    return user
  },

  onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(callback)
  },

  getAccessToken() {
    // Get current session and return access token
    return supabase.auth.getSession().then(({ data: { session } }) => {
      return session?.access_token || null
    })
  }
}
