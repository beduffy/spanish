// ***********************************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

// Set mock Supabase env vars for tests (if not already set)
if (!Cypress.env('VUE_APP_SUPABASE_URL')) {
  Cypress.env('VUE_APP_SUPABASE_URL', 'https://mock.supabase.co')
}
if (!Cypress.env('VUE_APP_SUPABASE_ANON_KEY')) {
  Cypress.env('VUE_APP_SUPABASE_ANON_KEY', 'mock-anon-key-for-testing')
}

// Handle uncaught exceptions from Supabase (for tests without real config)
Cypress.on('uncaught:exception', (err, runnable) => {
  // Ignore Supabase URL errors in test environment
  if (err.message.includes('supabaseUrl is required')) {
    return false
  }
  // Return true to let other errors fail the test
  return true
})
