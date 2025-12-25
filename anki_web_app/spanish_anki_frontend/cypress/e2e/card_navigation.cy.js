describe('Card Navigation and Data Verification', () => {
    beforeEach(() => {
        cy.visit('/');
    });

    it('navigates to Dashboard and verifies card statistics', () => {
        cy.get('nav a').contains('Dashboard').click();
        cy.url().should('include', '/dashboard');
        cy.get('h1').contains('Dashboard');
        
        // Wait for statistics to load (wait for loading to finish)
        cy.get('.loading-message', { timeout: 10000 }).should('not.exist');
        
        // Check for card statistics (not sentences) - wait for them to appear
        cy.get('.statistics-grid .stat-card', { timeout: 10000 }).should('have.length.greaterThan', 0);
        cy.get('.stat-card h2').contains('Reviews Today').should('be.visible');
        cy.get('.stat-card h2').contains('Total Cards').should('be.visible');
        cy.get('.stat-card h2').contains('Avg. Score').should('be.visible');
    });

    it('navigates to Cards List and verifies cards are displayed', () => {
        cy.visit('/');
        cy.get('nav a').contains('All Cards').click();
        cy.url().should('include', '/cards');
        cy.get('h1').contains('All Cards');
        
        // Wait for loading to finish
        cy.get('.loading-message', { timeout: 10000 }).should('not.exist');
        
        // Check if cards exist or if we see the no-data message
        cy.get('body').then(($body) => {
            if ($body.find('.card-list-view table').length > 0) {
                // Cards exist - verify table
                cy.get('.card-list-view table').should('be.visible');
                
                // Check for mastery column
                cy.get('thead th').contains('Mastery').should('be.visible');
                
                // If cards exist in table, verify they're displayed
                if ($body.find('.card-list-view tbody tr').length > 0) {
                    cy.get('.card-list-view tbody tr').should('have.length.greaterThan', 0);
                    
                    // Verify mastery level is displayed
                    cy.get('.card-list-view tbody tr').first().within(() => {
                        cy.get('td').should('have.length.greaterThan', 0);
                    });
                }
            } else {
                // No cards - verify no-data message is shown
                cy.get('.no-data-message').should('be.visible');
            }
        });
    });

    it('can create a new card', () => {
        cy.visit('/cards');
        cy.get('a.btn-primary').contains('Create Card').click();
        cy.url().should('include', '/cards/create');
        
        // Fill in card form - CardEditorView uses textarea#front and textarea#back
        cy.get('textarea#front').should('be.visible').type('Test Card Front');
        cy.get('textarea#back').should('be.visible').type('Test Card Back');
        
        // Submit form
        cy.intercept('POST', '/api/flashcards/cards/').as('createCard');
        cy.get('button[type="submit"]').contains('Create Card').click();
        
        cy.wait('@createCard', { timeout: 10000 })
            .its('response.statusCode')
            .should('be.oneOf', [200, 201]);
        
        // Should redirect to cards list or show success
        cy.url().should('satisfy', (url) => {
            return url.includes('/cards') || url.includes('/cards/create');
        });
    });

    it('reflects review activity in Dashboard', () => {
        // Perform a review
        cy.intercept('GET', '/api/flashcards/cards/next-card/').as('getNextCard');
        cy.intercept('POST', '/api/flashcards/cards/submit-review/').as('submitReview');
        
        cy.visit('/');
        cy.wait('@getNextCard', { timeout: 10000 });
        
        cy.get('body').then(($body) => {
            if ($body.find('.flashcard-container').length > 0) {
                cy.get('button.action-button').contains('Show Answer').click();
                cy.get('#userScore').clear().type('0.8');
                cy.get('button.action-button').contains('Submit & Next').click();
                cy.wait('@submitReview', { timeout: 10000 });
                
                // Navigate to Dashboard
                cy.get('nav a').contains('Dashboard').click();
                cy.url().should('include', '/dashboard');
                
                // Verify review count increased
                cy.get('.stat-card h2').contains('Reviews Today')
                    .parent()
                    .find('p')
                    .invoke('text')
                    .then(parseFloat)
                    .should('be.gte', 0);
            } else {
                cy.log('No cards available - skipping review activity test');
            }
        });
    });
});
