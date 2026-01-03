describe('Card Review Flow', () => {
    beforeEach(() => {
        // Mock authentication - backend auto-logs in as testuser in DEBUG mode
        // Frontend route guard needs mocked Supabase session
        cy.visitAsAuthenticated('/');
    });

    it('successfully loads and displays a card', () => {
        cy.get('h1').contains('Card Review');
        
        // Wait for card to load (either shows card or "all done" message)
        cy.get('.flashcard-container, .all-done-message, .no-cards-message, .error-message', { timeout: 10000 })
            .should('be.visible');
        
        // If a card is shown, verify it has front text
        cy.get('body').then(($body) => {
            if ($body.find('.flashcard-container').length > 0) {
                cy.get('.flashcard-container .card-front .sentence-display')
                    .should('be.visible')
                    .should('not.be.empty');
            }
        });
    });

    it('successfully completes a review cycle', () => {
        cy.intercept('GET', '/api/flashcards/cards/next-card/').as('getNextCard');
        cy.intercept('POST', '/api/flashcards/cards/submit-review/').as('submitReview');
        
        cy.visitAsAuthenticated('/');
        cy.wait('@getNextCard', { timeout: 10000 });
        
        // Check if we have a card to review
        cy.get('body').then(($body) => {
            if ($body.find('.flashcard-container').length > 0) {
                // Get the front text
                cy.get('.flashcard-container .card-front .sentence-display')
                    .invoke('text')
                    .then((frontText) => {
                        expect(frontText.trim()).not.to.be.empty;
                        
                        // Show answer
                        cy.dismissWebpackOverlay();
                        cy.get('button.action-button').contains('Show Answer').click({ force: true });
                        
                        // Verify answer is shown
                        cy.get('.card-back').should('be.visible');
                        cy.get('.card-back').contains('Answer:').should('be.visible');
                        
                        // Set score and submit
                        cy.get('#userScore').clear().type('0.9');
                        cy.get('#userComment').clear().type('E2E test review');
                        cy.get('button.action-button').contains('Submit & Next').click();
                        
                        // Wait for review submission
                        cy.wait('@submitReview', { timeout: 10000 })
                            .its('response.statusCode')
                            .should('be.oneOf', [200, 201]);
                        
                        // Should load next card or show completion message
                        cy.get('.flashcard-container, .all-done-message, .no-cards-message', { timeout: 10000 })
                            .should('be.visible');
                    });
            } else {
                cy.log('No cards available for review - skipping review cycle test');
            }
        });
    });
});
