describe('Navigation and Data Verification', () => {
    beforeEach(() => {
        // Potentially seed database or ensure a known state before each test.
        // For now, we assume the backend has data and is running.
        // We also assume the frontend dev server is running.
    });

    it('navigates to Dashboard and verifies some basic stats exist', () => {
        cy.visit('/'); // Start at homepage (FlashcardView)
        cy.get('nav a').contains('Dashboard').click();
        cy.url().should('include', '/dashboard');
        cy.get('h1').contains('Dashboard');

        // Check for the presence of stat cards (don't need to check values yet, just that they render)
        cy.get('.statistics-grid .stat-card').should('have.length.greaterThan', 0);
        cy.get('.stat-card h2').contains('Reviews Today').should('be.visible');
        cy.get('.stat-card h2').contains('Avg. Score').should('be.visible');
    });

    it('navigates to Sentence List, verifies pagination, and navigates to Sentence Detail', () => {
        cy.visit('/');
        cy.get('nav a').contains('Sentences').click();
        cy.url().should('include', '/sentences');
        cy.get('h1').contains('All Sentences');

        // Verify table and some sentences are listed
        cy.get('.sentence-list-view table').should('be.visible');
        cy.get('.sentence-list-view tbody tr').should('have.length.greaterThan', 0);

        // Enhanced pagination check
        cy.get('.pagination-controls span').invoke('text').then((text) => {
            const match = text.match(/Page (\d+) of (\d+)/);
            // Expect a match, meaning totalPages is a number and rendered.
            expect(match, `Expected pagination text '${text}' to match Page X of Y`).to.not.be.null;
            if (!match) return; // Exit if match is null to prevent further errors

            const currentPage = parseInt(match[1]);
            const totalPages = parseInt(match[2]);

            if (totalPages > 1) {
                if (currentPage < totalPages) {
                    cy.get('.pagination-controls button').contains('Next').click();
                    cy.get('.pagination-controls span').should('contain', `Page ${currentPage + 1} of ${totalPages}`);
                    cy.get('.pagination-controls button').contains('Previous').click();
                    cy.get('.pagination-controls span').should('contain', `Page ${currentPage} of ${totalPages}`);
                } else {
                    // On the last page of multiple pages
                    cy.get('.pagination-controls button').contains('Previous').click();
                    cy.get('.pagination-controls span').should('contain', `Page ${currentPage - 1} of ${totalPages}`);
                }
            } else {
                cy.log('Skipping Next/Previous click test as there is only one page or totalPages is 0.');
                expect(totalPages).to.be.at.most(1);
            }
        });

        // Navigate to the first sentence's detail view
        cy.get('.sentence-list-view tbody tr:first-child a').contains('View Details').click();

        cy.url().should('match', /\/sentences\/\d+/);
        cy.get('h1').contains('Sentence Detail');

        cy.get('.main-details .detail-item').contains('Prompt Key Word:').should('be.visible');
        cy.get('.srs-details .detail-item').contains('Next Review Date:').should('be.visible');
        cy.get('.review-history').should('be.visible');
    });

    it('reflects review activity in Dashboard and Sentence Detail', () => {
        // 1. Perform a review on the first card presented
        cy.visit('/');
        cy.log('Test: reflects review activity - Visited /');
        // Ensure the card front h2 is loaded and not empty before getting its text
        cy.get('.flashcard-container .card-front h2', { timeout: 15000 })
            .should(($h2) => {
                expect($h2.text().trim()).not.to.be.empty;
            })
            .invoke('text').then((text) => {
                const firstCardKeyWord = text.trim();
                cy.log(`Test: reflects review activity - CI LOG - Captured firstCardKeyWord: ${firstCardKeyWord}`);
                expect(firstCardKeyWord).not.to.be.empty; // Ensure it's not empty

                cy.get('button.action-button', { timeout: 10000 }).contains('Show Answer').click();
                cy.get('#userScore', { timeout: 10000 }).clear().type('0.7');
                cy.get('#userComment', { timeout: 10000 }).clear().type('E2E test - dashboard/detail check');
                cy.log('Test: reflects review activity - Submitting review...');
                cy.intercept('POST', '/api/flashcards/submit-review/').as('submitReview');
                cy.get('button.action-button', { timeout: 10000 }).contains('Submit & Next').click();
                cy.wait('@submitReview', { timeout: 15000 }).its('response.statusCode').should('be.oneOf', [200, 201]);
                cy.log('Test: reflects review activity - Review submitted and API call confirmed.');

                // Explicit wait for potential UI updates or loading messages after submit
                // This is a general wait, adjust if a specific loading indicator exists and is reliable
                cy.wait(1000); // Wait 1 second for UI to settle, adjust as needed
                cy.get('.loading-message', { timeout: 15000 }).should('not.exist');
                cy.log('Test: reflects review activity - Loading message (if any) is gone.');

                // 2. Navigate to Dashboard and check if "Reviews Today" is at least 1
                cy.log('Test: reflects review activity - Navigating to Dashboard.');
                cy.get('nav a', { timeout: 10000 }).contains('Dashboard').click();
                cy.url().should('include', '/dashboard');
                cy.get('.stat-card h2', { timeout: 10000 }).contains('Reviews Today').parent().find('p').invoke('text').then(parseFloat).should('be.gte', 1);
                cy.log('Test: reflects review activity - Dashboard review count verified.');

                // 3. Navigate to Sentence List, find the reviewed sentence
                cy.log('Test: reflects review activity - Navigating to Sentences list.');
                cy.get('nav a', { timeout: 10000 }).contains('Sentences').click();
                cy.url().should('include', '/sentences');

                // Use the captured firstCardKeyWord
                cy.log(`Test: reflects review activity - Searching for sentence with key word: ${firstCardKeyWord}`);
                cy.contains('.sentence-list-view tbody tr td', firstCardKeyWord, { timeout: 15000 })
                    .should('be.visible') // Ensure it's found and visible
                    .parent('tr')
                    .find('a').contains('View Details')
                    .click();
                cy.log('Test: reflects review activity - Navigated to sentence detail.');

                // 4. On Sentence Detail view, verify the review is listed
                cy.url().should('match', /\/sentences\/\d+/);
                cy.get('h1', { timeout: 10000 }).contains('Sentence Detail');
                cy.log('Test: reflects review activity - Verifying review history table.');

                // Verify review history on Sentence Detail page
                cy.log('Test: reflects review activity - Verifying review history table on sentence detail page.');
                cy.get('.review-history table tbody tr', { timeout: 10000 }).should('have.length.above', 0);

                cy.get('.review-history table tbody tr').first().as('firstReviewRow');

                cy.get('@firstReviewRow').then(($row) => {
                    cy.log('CI DEBUG - HTML of first review row:', $row.html());
                });

                cy.get('@firstReviewRow').within(() => {
                    cy.get('td').eq(0).should('not.be.empty'); // Date column
                    cy.get('td').eq(1).should('contain', '0.7'); // Score column
                    cy.get('td').eq(4).should('contain', 'E2E test - dashboard/detail check'); // Comment column (index 4)
                });

                // 5. Navigate to Dashboard and verify updated stats (e.g., reviews_done)
                cy.log('Test: reflects review activity - Navigating to Dashboard.');
                cy.get('nav a', { timeout: 10000 }).contains('Dashboard').click();
                cy.url().should('include', '/dashboard');
                cy.get('.stat-card h2', { timeout: 10000 }).contains('Reviews Today').parent().find('p').invoke('text').then(parseFloat).should('be.gte', 1);
                cy.log('Test: reflects review activity - Dashboard review count verified.');
            });
    });
}); 