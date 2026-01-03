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
Cypress.Commands.add('visitAsAuthenticated', (url, options = {}) => {
  // Set up mock session before visiting
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
  
  cy.visit(url, {
    ...options,
    onBeforeLoad(win) {
      // Ensure flag and mock session are set before page loads
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
      if (options.onBeforeLoad) {
        options.onBeforeLoad(win);
      }
    }
  });
  // Wait for page to load and route guard to process
  cy.wait(500);
  
  // Hide webpack dev server overlay if present
  cy.get('body').then(($body) => {
    const overlay = $body.find('#webpack-dev-server-client-overlay');
    if (overlay.length > 0) {
      cy.window().then((win) => {
        const overlayEl = win.document.getElementById('webpack-dev-server-client-overlay');
        if (overlayEl) {
          overlayEl.style.display = 'none';
        }
      });
    }
  });
});

// Command to dismiss webpack overlay
Cypress.Commands.add('dismissWebpackOverlay', () => {
  cy.get('body').then(($body) => {
    const overlay = $body.find('#webpack-dev-server-client-overlay');
    if (overlay.length > 0) {
      cy.window().then((win) => {
        const overlayEl = win.document.getElementById('webpack-dev-server-client-overlay');
        if (overlayEl) {
          overlayEl.style.display = 'none';
        }
      });
    }
  });
});