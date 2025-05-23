describe('Flashcard Review Flow', () => {
    beforeEach(() => {
        cy.log('flashcard_flow.cy.js: beforeEach - Start');
        cy.log('flashcard_flow.cy.js: Setting up intercept for /api/flashcards/next-card/');
        // Temporarily remove failOnStatusCode: false to see default Cypress error on bad status
        cy.intercept('GET', '/api/flashcards/next-card/').as('getNextCard');

        cy.log('flashcard_flow.cy.js: Visiting / - Start');
        cy.visit('/');
        cy.log('flashcard_flow.cy.js: Visiting / - End');

        cy.log('flashcard_flow.cy.js: Waiting for @getNextCard (timeout 30s)...');
        cy.wait('@getNextCard', { timeout: 30000 })
            .then((interception) => {
                cy.log('flashcard_flow.cy.js: @getNextCard - Interception received.');

                if (!interception) {
                    cy.log('flashcard_flow.cy.js: @getNextCard - CRITICAL: Interception object IS NULL or undefined.');
                    throw new Error('@getNextCard interception object was null or undefined unexpectedly.');
                }

                cy.log('flashcard_flow.cy.js: @getNextCard - Interception object is present.');

                if (interception.request) {
                    cy.log('flashcard_flow.cy.js: @getNextCard - Request URL:', interception.request.url);
                    cy.log('flashcard_flow.cy.js: @getNextCard - Request Headers:', JSON.stringify(interception.request.headers));
                } else {
                    cy.log('flashcard_flow.cy.js: @getNextCard - CRITICAL: NO interception.request object.');
                    throw new Error('@getNextCard interception has no request object.');
                }

                if (interception.response) {
                    cy.log('flashcard_flow.cy.js: @getNextCard - Response status:', interception.response.statusCode);
                    cy.log('flashcard_flow.cy.js: @getNextCard - Response Headers:', JSON.stringify(interception.response.headers));
                    let responseBodyString = 'N/A';
                    try {
                        // Only attempt to stringify if body exists and is not excessively large for logging
                        if (interception.response.body && typeof interception.response.body === 'object') {
                            responseBodyString = JSON.stringify(interception.response.body).substring(0, 500); // Log a snippet
                        } else if (interception.response.body) {
                            responseBodyString = String(interception.response.body).substring(0, 500);
                        }
                    } catch (e) {
                        responseBodyString = `Error stringifying response body: ${e.message}`;
                    }
                    cy.log('flashcard_flow.cy.js: @getNextCard - Response body (stringified snippet):', responseBodyString);

                    // Assert basic validity of the response
                    expect(interception.response, 'Interception response object').to.exist;
                    expect(interception.response.statusCode, 'API response status code').to.be.oneOf([200, 204]);

                } else {
                    cy.log('flashcard_flow.cy.js: @getNextCard - CRITICAL: NO interception.response object.');
                    throw new Error('@getNextCard interception received, but no interception.response object found.');
                }
            });
        // Removed the previous .should('exist')

        cy.log('flashcard_flow.cy.js: beforeEach - End, after .wait().then() chain.');
    });

    it('successfully completes a review cycle', () => {
        cy.log('flashcard_flow.cy.js: Test - successfully completes a review cycle - Start');
        // 1. Check initial card display (front)
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
        cy.log('flashcard_flow.cy.js: Test - shows all cards done - Start');
        // This test requires setting up the backend so no cards are due.
        // Re-intercept for this specific test case after the beforeEach one.
        cy.intercept('GET', '/api/flashcards/next-card/', { statusCode: 204, body: null, failOnStatusCode: false }).as('getNextCardEmpty');
        cy.log('flashcard_flow.cy.js: Test - shows all cards done - Visiting / again');
        cy.visit('/'); // Re-visit to trigger the new intercept
        cy.log('flashcard_flow.cy.js: Test - shows all cards done - Waiting for @getNextCardEmpty');
        cy.wait('@getNextCardEmpty', { timeout: 10000 }); // Wait for the stubbed response
        cy.get('.all-done-message', { timeout: 10000 }).should('be.visible');
        cy.get('.all-done-message p').contains("Congratulations! You\'ve reviewed all available cards for now!");
    });

    it('displays an error message if submitting a review fails', () => {
        cy.log('flashcard_flow.cy.js: Test - displays error on submit fail - Start');
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