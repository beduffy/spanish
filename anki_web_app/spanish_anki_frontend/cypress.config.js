const { defineConfig } = require("cypress");

module.exports = defineConfig({
  defaultCommandTimeout: 10000, // Increased timeout for CI
  e2e: {
    baseUrl: 'http://localhost:8080',
    specPattern: 'cypress/e2e/*.cy.js',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
