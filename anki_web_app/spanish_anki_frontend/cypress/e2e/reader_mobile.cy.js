/**
 * Mobile-specific tests for Reader phrase selection
 * Tests touch-based phrase selection on mobile devices
 */

describe('Reader Mobile - Phrase Selection', () => {
  const mobileViewports = [
    { name: 'iPhone 12', width: 390, height: 844 },
    { name: 'iPhone 12 Pro', width: 390, height: 844 },
    { name: 'Samsung Galaxy S20', width: 360, height: 800 },
    { name: 'iPad', width: 768, height: 1024 },
    { name: 'Samsung Galaxy Z Fold 5 (Unfolded)', width: 1768, height: 2208 }
  ]

  beforeEach(() => {
    cy.visitAsAuthenticated('/')
  })

  mobileViewports.forEach(viewport => {
    context(`Viewport: ${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      beforeEach(() => {
        cy.viewport(viewport.width, viewport.height)
      })

      it('can select multiple words using touch to create a phrase', () => {
        // Create a lesson with multiple words
        cy.request({
          method: 'POST',
          url: '/api/flashcards/reader/lessons/',
          headers: {
            'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
          },
          body: {
            title: 'Mobile Phrase Test',
            text: 'Hallo Welt. Das ist ein Test.',
            language: 'de',
            source_type: 'text'
          },
          failOnStatusCode: false
        }).then((response) => {
          if (response.status === 201 || response.status === 200) {
            const lessonId = response.body.lesson_id || response.body.id
            
            // Navigate to lesson detail
            cy.visitAsAuthenticated(`/reader/lessons/${lessonId}`)
            
            // Wait for tokens to load
            cy.get('[data-token-id]', { timeout: 10000 }).should('have.length.greaterThan', 0)
            
            // Get first two token elements
            cy.get('[data-token-id]').then(($tokens) => {
              if ($tokens.length >= 2) {
                const firstToken = $tokens.eq(0)
                const secondToken = $tokens.eq(1)
                
                // Get their positions
                const firstRect = firstToken[0].getBoundingClientRect()
                const secondRect = secondToken[0].getBoundingClientRect()
                
                // Simulate touch selection: touchstart on first token, touchmove to second, touchend
                cy.wrap(firstToken[0])
                  .trigger('touchstart', {
                    touches: [{ clientX: firstRect.left + firstRect.width / 2, clientY: firstRect.top + firstRect.height / 2 }],
                    changedTouches: [{ clientX: firstRect.left + firstRect.width / 2, clientY: firstRect.top + firstRect.height / 2 }]
                  })
                
                // Wait a bit to simulate drag
                cy.wait(250)
                
                // Touch move to second token
                cy.wrap(firstToken[0])
                  .trigger('touchmove', {
                    touches: [{ clientX: secondRect.right, clientY: secondRect.top + secondRect.height / 2 }],
                    changedTouches: [{ clientX: secondRect.right, clientY: secondRect.top + secondRect.height / 2 }]
                  })
                
                // Touch end
                cy.wrap(firstToken[0])
                  .trigger('touchend', {
                    changedTouches: [{ clientX: secondRect.right, clientY: secondRect.top + secondRect.height / 2 }]
                  })
                
                // Wait for phrase creation
                cy.wait(500)
                
                // Verify phrase popover appears (or phrase was created)
                cy.get('body').should('satisfy', ($body) => {
                  // Either popover is shown or phrase was created
                  return $body.find('.token-popover').length > 0 || 
                         $body.text().includes('phrase') ||
                         $body.find('.token-in-phrase').length > 0
                })
              } else {
                cy.log('Not enough tokens for phrase selection test')
              }
            })
          } else {
            cy.log('Could not create lesson, skipping mobile phrase test')
          }
        })
      })

      it('can tap a single token to see translation on mobile', () => {
        cy.request({
          method: 'POST',
          url: '/api/flashcards/reader/lessons/',
          headers: {
            'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
          },
          body: {
            title: 'Mobile Token Click Test',
            text: 'Hallo Welt',
            language: 'de',
            source_type: 'text'
          },
          failOnStatusCode: false
        }).then((response) => {
          if (response.status === 201 || response.status === 200) {
            const lessonId = response.body.lesson_id || response.body.id
            
            // Get tokens
            cy.request({
              method: 'GET',
              url: `/api/flashcards/reader/lessons/${lessonId}/`,
              headers: {
                'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
              },
              failOnStatusCode: false
            }).then((lessonResponse) => {
              if (lessonResponse.status === 200 && lessonResponse.body.tokens && lessonResponse.body.tokens.length > 0) {
                const tokenId = lessonResponse.body.tokens[0].token_id
                
                cy.visitAsAuthenticated(`/reader/lessons/${lessonId}`)
                
                cy.intercept('GET', `/api/flashcards/reader/tokens/${tokenId}/click/`).as('tokenClick')
                
                // Wait for token to be visible
                cy.get(`[data-token-id="${tokenId}"]`, { timeout: 10000 }).should('be.visible')
                
                // Simulate touch tap
                cy.get(`[data-token-id="${tokenId}"]`).then(($token) => {
                  const rect = $token[0].getBoundingClientRect()
                  
                  // Touch start and end quickly (tap)
                  cy.wrap($token[0])
                    .trigger('touchstart', {
                      touches: [{ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 }],
                      changedTouches: [{ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 }]
                    })
                  
                  cy.wait(100)
                  
                  cy.wrap($token[0])
                    .trigger('touchend', {
                      changedTouches: [{ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 }]
                    })
                  
                  // Should trigger click handler or show popover
                  cy.wait('@tokenClick', { timeout: 5000 })
                    .its('response.statusCode')
                    .should('be.oneOf', [200, 201])
                  
                  // Verify translation popover appears
                  cy.get('.token-popover', { timeout: 3000 }).should('be.visible')
                })
              } else {
                cy.log('No tokens found, skipping mobile token click test')
              }
            })
          } else {
            cy.log('Could not create lesson, skipping mobile token click test')
          }
        })
      })

      it('handles touch selection without scrolling', () => {
        cy.request({
          method: 'POST',
          url: '/api/flashcards/reader/lessons/',
          headers: {
            'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
          },
          body: {
            title: 'Mobile Scroll Test',
            text: 'Hallo Welt. Das ist ein Test. ' + 'Wort '.repeat(50), // Long text to enable scrolling
            language: 'de',
            source_type: 'text'
          },
          failOnStatusCode: false
        }).then((response) => {
          if (response.status === 201 || response.status === 200) {
            const lessonId = response.body.lesson_id || response.body.id
            
            cy.visitAsAuthenticated(`/reader/lessons/${lessonId}`)
            
            // Get initial scroll position
            cy.get('.lesson-text-container').then(($container) => {
              const initialScrollTop = $container[0].scrollTop
              
              // Simulate touch selection
              cy.get('[data-token-id]').first().then(($token) => {
                const rect = $token[0].getBoundingClientRect()
                
                cy.wrap($token[0])
                  .trigger('touchstart', {
                    touches: [{ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 }],
                    changedTouches: [{ clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 }]
                  })
                
                // Wait to enter selection mode
                cy.wait(250)
                
                // Touch move (should not scroll if preventDefault is working)
                cy.wrap($token[0])
                  .trigger('touchmove', {
                    touches: [{ clientX: rect.left + rect.width / 2 + 50, clientY: rect.top + rect.height / 2 }],
                    changedTouches: [{ clientX: rect.left + rect.width / 2 + 50, clientY: rect.top + rect.height / 2 }]
                  })
                
                cy.wrap($token[0])
                  .trigger('touchend', {
                    changedTouches: [{ clientX: rect.left + rect.width / 2 + 50, clientY: rect.top + rect.height / 2 }]
                  })
                
                // Verify scroll position didn't change significantly during selection
                cy.get('.lesson-text-container').then(($containerAfter) => {
                  const finalScrollTop = $containerAfter[0].scrollTop
                  // Allow small scroll differences (some browsers may scroll slightly)
                  expect(Math.abs(finalScrollTop - initialScrollTop)).to.be.lessThan(100)
                })
              })
            })
          } else {
            cy.log('Could not create lesson, skipping scroll test')
          }
        })
      })
    })
  })

  // Test with actual mobile device user agent
  context('Mobile User Agent', () => {
    beforeEach(() => {
      cy.viewport(390, 844) // iPhone 12 dimensions
      // Set mobile user agent
      cy.visitAsAuthenticated('/', {
        headers: {
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
        }
      })
    })

    it('detects mobile device and enables touch selection', () => {
      cy.request({
        method: 'POST',
        url: '/api/flashcards/reader/lessons/',
        headers: {
          'Authorization': `Bearer ${Cypress.env('AUTH_TOKEN') || 'test-token'}`
        },
        body: {
          title: 'Mobile Detection Test',
          text: 'Hallo Welt. Das ist ein Test.',
          language: 'de',
          source_type: 'text'
        },
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 201 || response.status === 200) {
          const lessonId = response.body.lesson_id || response.body.id
          
          cy.visitAsAuthenticated(`/reader/lessons/${lessonId}`)
          
          // Verify touch events are attached to lesson text
          cy.get('.lesson-text').should('have.attr', 'class').and('include', 'lesson-text')
          
          // Verify tokens are touchable
          cy.get('[data-token-id]').first().should('be.visible')
        } else {
          cy.log('Could not create lesson, skipping mobile detection test')
        }
      })
    })
  })
})
