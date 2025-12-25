// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

// Mock Supabase authentication for E2E tests
// Set a flag that the router can check
Cypress.Commands.add('login', () => {
  // Set a flag in window that indicates we're in test mode
  // This needs to be set before the app loads
  cy.window().then((win) => {
    win.__CYPRESS_TEST_MODE__ = true;
    win.__CYPRESS_MOCK_SESSION__ = {
      access_token: 'mock-access-token-for-e2e-tests',
      refresh_token: 'mock-refresh-token',
      expires_in: 3600,
      expires_at: Date.now() / 1000 + 3600,
      token_type: 'bearer',
      user: {
        id: 'mock-user-id',
        email: 'test@example.com',
        user_metadata: {},
        app_metadata: {},
      }
    };
  });
});

// Visit a page and ensure we're logged in
Cypress.Commands.add('visitAsAuthenticated', (url) => {
  cy.visit(url, {
    onBeforeLoad(win) {
      // Ensure flag is set before page loads and router initializes
      win.__CYPRESS_TEST_MODE__ = true;
    }
  });
  // Wait for page to load and route guard to process
  cy.wait(500);
});