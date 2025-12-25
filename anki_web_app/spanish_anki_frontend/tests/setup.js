// Jest setup file - runs before all tests
// Set mock Supabase environment variables for tests
process.env.VUE_APP_SUPABASE_URL = process.env.VUE_APP_SUPABASE_URL || 'https://mock.supabase.co'
process.env.VUE_APP_SUPABASE_ANON_KEY = process.env.VUE_APP_SUPABASE_ANON_KEY || 'mock-anon-key-for-testing'
