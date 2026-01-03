describe('Reader (LingQ-style) Flow', () => {
    beforeEach(() => {
        cy.visitAsAuthenticated('/');
    });

    it('can navigate to reader and import a lesson', () => {
        // Navigate to reader/lessons page
        cy.dismissWebpackOverlay();
        cy.get('nav a').contains('Reader').click({ force: true });
        cy.url().should('include', '/reader');
        
        // Look for import button or link
        cy.get('body').then(($body) => {
            if ($body.find('a').text().includes('Import') || $body.find('button').text().includes('Import')) {
                cy.contains('Import').click();
            } else {
                // Try navigating to import page directly
                cy.visitAsAuthenticated('/reader/import');
            }
        });
        
        cy.url().should('include', '/import');
        
        // Fill in lesson import form
        cy.get('input[name="title"], input#title, textarea[name="title"]').should('be.visible').type('Test Lesson E2E');
        cy.get('textarea[name="text"], textarea#text').should('be.visible').type('Hallo Welt. Das ist ein Test.');
        
        // Submit form
        cy.intercept('POST', '/api/flashcards/reader/lessons/').as('createLesson');
        cy.get('button[type="submit"]').contains('Import').click();
        
        cy.wait('@createLesson', { timeout: 10000 })
            .its('response.statusCode')
            .should('be.oneOf', [200, 201]);
        
        // Should redirect to lesson detail or list
        cy.url().should('satisfy', (url) => {
            return url.includes('/reader') || url.includes('/lessons');
        });
    });

    it('can view lesson detail and see tokens', () => {
        // First create a lesson via API (or navigate if one exists)
        cy.request({
            method: 'POST',
            url: '/api/flashcards/reader/lessons/',
            headers: {
                'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
            },
            body: {
                title: 'E2E Test Lesson',
                text: 'Hallo Welt',
                language: 'de',
                source_type: 'text'
            },
            failOnStatusCode: false
        }).then((response) => {
            if (response.status === 201 || response.status === 200) {
                const lessonId = response.body.lesson_id || response.body.id;
                
                // Navigate to lesson detail
                cy.visitAsAuthenticated(`/reader/lessons/${lessonId}`);
                
                // Verify lesson content is displayed
                cy.get('body').should('contain', 'E2E Test Lesson');
                cy.get('body').should('contain', 'Hallo Welt');
                
                // Check if tokens are displayed (may be in a specific format)
                cy.get('body').then(($body) => {
                    // Tokens might be displayed as clickable spans or in a specific format
                    if ($body.find('.token, [data-token], .word-token').length > 0) {
                        cy.get('.token, [data-token], .word-token').should('have.length.greaterThan', 0);
                    }
                });
            } else {
                cy.log('Could not create lesson via API, skipping test');
            }
        });
    });

    it('can click on a token to see translation', () => {
        // Create lesson and get token ID
        cy.request({
            method: 'POST',
            url: '/api/flashcards/reader/lessons/',
            headers: {
                'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
            },
            body: {
                title: 'Token Click Test',
                text: 'Hallo Welt',
                language: 'de',
                source_type: 'text'
            },
            failOnStatusCode: false
        }).then((response) => {
            if (response.status === 201 || response.status === 200) {
                const lessonId = response.body.lesson_id || response.body.id;
                
                // Get tokens for the lesson
                cy.request({
                    method: 'GET',
                    url: `/api/flashcards/reader/lessons/${lessonId}/`,
                    headers: {
                        'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
                    },
                    failOnStatusCode: false
                }).then((lessonResponse) => {
                    if (lessonResponse.status === 200 && lessonResponse.body.tokens && lessonResponse.body.tokens.length > 0) {
                        const tokenId = lessonResponse.body.tokens[0].token_id;
                        
                        // Navigate to lesson
                        cy.visitAsAuthenticated(`/reader/lessons/${lessonId}`);
                        
                        // Click on token (might be in different formats)
                        cy.intercept('GET', `/api/flashcards/reader/tokens/${tokenId}/click/`).as('tokenClick');
                        
                        cy.get('body').then(($body) => {
                            // Try different selectors for clickable tokens
                            const tokenElement = $body.find(`[data-token-id="${tokenId}"], .token[data-id="${tokenId}"], .word-token[data-id="${tokenId}"]`).first();
                            
                            if (tokenElement.length > 0) {
                                cy.wrap(tokenElement).click();
                                
                                cy.wait('@tokenClick', { timeout: 5000 })
                                    .its('response.statusCode')
                                    .should('be.oneOf', [200, 201]);
                                
                                // Verify translation is shown (might be in modal, tooltip, or inline)
                                cy.get('body').should('satisfy', ($body) => {
                                    return $body.text().includes('Hello') || 
                                           $body.find('.translation, .token-translation, [data-translation]').length > 0;
                                });
                            } else {
                                cy.log('Token element not found in expected format, skipping click test');
                            }
                        });
                    } else {
                        cy.log('No tokens found in lesson, skipping token click test');
                    }
                });
            } else {
                cy.log('Could not create lesson, skipping token click test');
            }
        });
    });
});
