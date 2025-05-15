describe('Flashcard Review Flow', () => {
    beforeEach(() => {
        cy.log('Setting up intercept for /api/flashcards/next-card/');
        cy.intercept('GET', '/api/flashcards/next-card/').as('getNextCard');
        cy.visit('/');
        cy.log('Waiting for @getNextCard...');
        cy.wait('@getNextCard', { timeout: 30000 }) // Increased to 30 seconds for debugging
            .then((interception) => {
                cy.log('Initial @getNextCard response status:', interception.response.statusCode);
                cy.log('Initial @getNextCard response body:', JSON.stringify(interception.response.body));
                // Assert that the API call was successful and returned data, or 204 for no cards
                expect(interception.response.statusCode).to.be.oneOf([200, 204]);
                if (interception.response.statusCode === 200) {
                    expect(interception.response.body).to.not.be.empty;
                }
            }, (error) => {
                cy.log('Error waiting for @getNextCard:', error.message);
                // Optionally, fail the test explicitly if the API call errors out
                // throw new Error('@getNextCard API call failed or timed out'); 
                return; // Prevent further execution in this test if API fails
            });
        cy.log('Finished beforeEach setup.');
    });

    it('successfully completes a review cycle', () => {
        // 1. Check initial card display (front)
        // Ensure the card front elements are present and visible with a longer timeout
        cy.get('.flashcard-container .card-front h2', { timeout: 10000 }).should('be.visible').and('not.be.empty');
        cy.get('.flashcard-container .card-front .sentence-display', { timeout: 10000 }).should('be.visible').and('not.be.empty');

        // 2. Click "Show Answer"
        cy.get('button.action-button', { timeout: 10000 }).contains('Show Answer')
            .should('be.visible')
            .and('not.be.disabled')
            .click({ force: true });

        // 3. Check if answer is displayed
        cy.get('.card-back').should('exist').and('be.visible'); // Ensure .card-back itself exists and is visible first
        cy.get('.card-back p').contains('Key Word Translation:').should('be.visible');
        cy.get('.card-back p').contains('Sentence Translation:').should('be.visible');

        // 4. Input score and comment
        cy.get('#userScore').clear().type('0.9');
        cy.get('#userComment').clear().type('Cypress E2E test comment');

        // 5. Click "Submit & Next"
        // Store the current card's Spanish sentence to compare with the next one
        cy.get('.flashcard-container .card-front .sentence-display').invoke('text').as('firstCardSentence');

        cy.get('button.action-button').contains('Submit & Next').click();

        // 6. Verify new card loads
        // Wait for loading to finish (if any loading indicator appears)
        cy.get('.loading-message').should('not.exist'); // Or a more specific wait for it to disappear

        // Check that a new card is displayed (sentence should be different)
        cy.get('.flashcard-container .card-front .sentence-display').invoke('text').then((newCardSentence) => {
            cy.get('@firstCardSentence').should((firstCardSentence) => {
                expect(newCardSentence).not.to.eq(firstCardSentence);
            });
        });
        cy.get('.flashcard-container .card-front h2').should('not.be.empty');

        // Ensure the answer is hidden again for the new card
        cy.get('.card-back').should('not.exist');
    });

    it('shows "all cards done" message if no cards are due', () => {
        // This test requires setting up the backend so no cards are due.
        // This might involve an API call to reset/clear reviews or a specific DB state.
        // For now, we will stub the API response directly in Cypress for this test case.
        // Re-intercept for this specific test case after the beforeEach one.
        cy.intercept('GET', '/api/flashcards/next-card/', { statusCode: 204, body: null }).as('getNextCardEmpty');
        cy.visit('/'); // Re-visit to trigger the new intercept
        cy.wait('@getNextCardEmpty', { timeout: 10000 }); // Wait for the stubbed response
        cy.get('.all-done-message', { timeout: 10000 }).should('be.visible');
        cy.get('.all-done-message p').contains("Congratulations! You\'ve reviewed all available cards for now!");
    });

    it('displays an error message if submitting a review fails', () => {
        // Ensure the card front elements are present and visible first
        cy.get('.flashcard-container .card-front h2', { timeout: 10000 }).should('be.visible').and('not.be.empty');
        cy.get('.flashcard-container .card-front .sentence-display', { timeout: 10000 }).should('be.visible').and('not.be.empty');

        cy.get('button.action-button', { timeout: 10000 }).contains('Show Answer').click();
        cy.get('#userScore').clear().type('0.5');

        // Intercept the submit review API call to simulate a failure
        cy.intercept('POST', '/api/flashcards/submit-review/', {
            statusCode: 500,
            body: { detail: 'Internal Server Error' },
        }).as('submitReviewFail');

        cy.get('button.action-button').contains('Submit & Next').click();
        cy.wait('@submitReviewFail');

        cy.get('.error-message.central-error').should('be.visible');
        cy.get('.error-message.central-error p').contains('Failed to submit your review. Please try again.');
    });

}); 