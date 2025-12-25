const { defineConfig } = require("cypress");

module.exports = defineConfig({
  defaultCommandTimeout: 10000, // Increased timeout for CI
  e2e: {
    baseUrl: 'http://localhost:8080',
    specPattern: 'cypress/e2e/*.cy.js',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    env: {
      // Provide mock Supabase env vars for Cypress tests
      VUE_APP_SUPABASE_URL: process.env.VUE_APP_SUPABASE_URL || 'https://mock.supabase.co',
      VUE_APP_SUPABASE_ANON_KEY: process.env.VUE_APP_SUPABASE_ANON_KEY || 'mock-anon-key-for-testing',
    },
  },
});
