# Product Requirements Document: Anki-Style Spanish Learning App

## Original prompt:
Here is my latest csv. Could you build me a Plan document for a HTML app that will test with anki cards on each sentence from Spanish to english... Maybe initially I will just say/think the translation (actually this requires less typing which is best) e.g.

Input to me:
De:
Él es de la ciudad de Nueva York

Then I think:
[De: from, He is from New York]

Then I click "show me answer" and see:
[De = From, 
Translation (while still showing spanish): He is from New York City.
Comment: "Easy, yay. Literal translation: He is from the city of New York"
]

And I think and write into app:
"ahhhh I forgot to say city" which gets added to the below comment with datetime that I said it e.g.

"Easy, yay. Literal translation: He is from the city of New York
15:31 May 15th: "ahhhh I forgot to say city" 

I need subjective scores (e.g. give myself 1 or 0 or maybe even a float score subjective e.g. for above missing of city, I'll get 0.8) to track how good I get at the sentences. But my goal would be to get good at all 2000 sentences forwards and backwards translations (and of course the words, but that is less important). So that is kinda 4000 but the pairs are linked of course. 

So the full flow is:
- Show english/spanish word sentence. 
- I translate in my head or out loud
- I click show answer, i see both original sentence + word and their translations
- I write a quick comment that gets appended to the original comment with a datetime
- I write my subjective score between 0 and 1
- I click submit and next input

Other UX:
- I get to see how many input output pairs I've done today, altogether, in a week, and of course my score out of all of them, e.g. also maybe a good measure is how many sentences I've seen full stop out of 2000/4000. AND my score on these. So many metrics we can calculate.
- and maybe other things related to the forgetting curve e.g. "last time you saw this sentence: May 13th 13:10"
- sentence page to see all sentences and statistics per sentence, how easy I find each sentence, scores on each attempt (e.g. seen 7 times, score: 3/7 but a mini graph showing that I began at 0 and then get to 1.0 score)

I want it to be simple so I can just fly through these 2000 words but also we need anki style forgetting curve so as I get perfect at some they show less as we introduce more. Then I would like to see individual scores for each sentence so I get happy/rewarded for getting closer to understand all 2000 sentences. 

don't code yet. Let's just plan this out in more depth.

Could we store this all is csv or SQL or something? Yes SQL is best. What do you recommend? I want to be able to do it. Let's form all the requirements into this document @product_requirements_doc.md And keep updating as we go along. Ask clarifying questions. 

## 1. Introduction/Overview

This document outlines the requirements for a web application designed to help the user learn Spanish sentences and vocabulary through an Anki-style flashcard system. The primary goal is to facilitate the memorization and understanding of approximately 2000 Spanish sentences, with translations to English, and to track progress effectively.

## 2. Goals

*   Efficiently learn and retain ~2000 Spanish sentences.
*   Practice translation from Spanish to English.
*   Track subjective understanding and recall for each sentence.
*   Implement a spaced repetition system (SRS) to optimize learning based on established forgetting curve principles.
*   Provide clear metrics on learning progress.
*   Create a simple, fast, and intuitive user experience.

## 3. User Stories

*   **As a user, I want to be shown a Spanish sentence so I can practice translating it in my head.**
*   **As a user, after thinking of the translation, I want to click a button to reveal the correct English translation, along with the original Spanish sentence and a key Spanish word with its English translation.**
*   **As a user, I want to be able to add a timestamped comment to my review of a sentence, noting any difficulties or insights (e.g., "forgot to say 'city'").**
*   **As a user, I want to give myself a subjective score (e.g., 0.0 to 1.0) for each sentence translation attempt to track my understanding.**
*   **As a user, I want to submit my comment and score and immediately move to the next sentence/card.**
*   **As a user, I want to see statistics about my learning, including:**
    *   Number of cards (new and review) reviewed today, this week, and overall.
    *   Number of new cards specifically reviewed today.
    *   Overall average score.
    *   Number of unique sentences seen out of the total.
    *   My average score on these seen sentences.
*   **As a user, I want the app to tell me when I last reviewed a specific sentence.**
*   **As a user, I want a dedicated page where I can see all sentences, their individual statistics, how easy I find each one, and a history of my scores for each (e.g., a mini-graph showing score progression).**
*   **As a user, I want the app to use a spaced repetition algorithm so that sentences I find easy are shown less frequently, and new or difficult sentences are shown more often.**

## 4. Core Features

### 4.1. Learning Flow (Flashcard Interface)

*   **Card Display (Front - "Input"):**
    *   Show `[Key Spanish Word]: [Spanish Example Sentence]` (e.g., "De: Él es de la ciudad de Nueva York"). The `Key Spanish Word` is from the CSV "Spanish Word" field, and `Spanish Example Sentence` is from the CSV "Spanish Example" field.
*   **User Action: Think/Say Translation.**
*   **User Action: Click "Show Answer".**
*   **Card Display (Back - "Answer"):**
    *   Original Spanish sentence (from CSV "Spanish Example" field).
    *   Key Spanish word (from CSV "Spanish Word" field) and its English translation (from CSV "English Translation" field for that word) (e.g., "De = From").
    *   English translation of the sentence (from CSV "English Example" field) (e.g., "He is from New York City.").
    *   Existing comments, including any previously user-added timestamped notes (from CSV "Comment" field, appended with user's dynamic notes).
*   **User Input Fields:**
    *   Text area for new comment (to be appended to existing comments for the sentence).
    *   Input for subjective score (0.0 - 1.0).
*   **User Action: Click "Submit & Next".**

### 4.2. Scoring and Comments

*   Users can assign a numerical score (float between 0.0 and 1.0) to each review attempt.
*   Users can add free-text comments.
*   Comments will be appended to a running log for that specific sentence, with a timestamp (e.g., "15:31 May 15th: ahhhh I forgot to say city"). The initial comment may come from the CSV's "Comment" field.

### 4.3. Spaced Repetition System (SRS)

*   The system will decide which card to show next based on an SRS algorithm. Research will be conducted to select/implement a suitable algorithm based on established forgetting curve literature (e.g., a variant of SM2, Leitner system principles, etc.).
*   Factors influencing card scheduling:
    *   User's score on previous reviews of the card.
    *   Time since the card was last reviewed.
    *   Calculated ease factor or similar SRS parameter for the card.
*   **New Card Introduction:** New cards will be introduced sequentially, starting from `Number` 1 in the CSV. The user can decide how many new cards to study in any given session. The system will track the number of new cards reviewed daily.
*   **Card Gradation/Mastery:** Cards considered "mastered" (e.g., consistently achieving a score > 0.8 for the last 3-5 reviews AND current interval > 21 days) will have their review intervals significantly increased.
*   Cards mastered will appear less frequently.

### 4.4. Progress Tracking & Statistics

*   **Dashboard/Overview Page:**
    *   Cards (new and reviews) reviewed today.
    *   New cards reviewed today.
    *   Cards reviewed this week.
    *   Total cards reviewed.
    *   Overall average score.
    *   Number of unique sentences mastered (see definition in SRS section).
    *   Number of unique sentences learned/seen.
    *   Percentage of total sentences learned/seen.
*   **Per-Sentence Statistics:**
    *   Date last seen.
    *   Number of times reviewed.
    *   Average score for that sentence.
    *   History of scores (potentially visualized as a mini-graph).
    *   All comments associated with the sentence.

### 4.5. Sentence Management

*   **Sentence Page:**
    *   A view to list all ~2000 sentences.
    *   Ability to see key statistics for each sentence at a glance.
    *   Potentially filter/sort sentences (e.g., by difficulty, last reviewed, score).

## 5. Data Model (High-Level - SQL Database)

*   **Sentences Table:**
    *   `sentence_id` (Primary Key, Auto-incrementing Integer)
    *   `csv_number` (Integer, from 'Number' column in CSV for reference, unique)
    *   `key_spanish_word` (TEXT, from 'Spanish Word' column in CSV)
    *   `key_word_english_translation` (TEXT, from 'English Translation' column in CSV)
    *   `spanish_sentence_example` (TEXT, from 'Spanish Example' column in CSV)
    *   `english_sentence_example` (TEXT, from 'English Example' column in CSV)
    *   `base_comment` (TEXT, from 'Comment' column in CSV, can be appended to by user)
    *   `ai_explanation` (TEXT, Nullable, from 'Chat GPTs explanation' or 'Gemini explanation' columns in CSV)
    *   `creation_date` (TIMESTAMP, when record was first imported)
    *   `last_modified_date` (TIMESTAMP, when record or its SRS data was last updated)
    *   `ease_factor` (FLOAT, SRS parameter, e.g., initial value 2.5)
    *   `interval_days` (INTEGER, SRS parameter, days until next review, 0 for new/learning)
    *   `next_review_date` (DATE, SRS parameter)
    *   `is_learning` (BOOLEAN, flag for cards currently in learning phase vs. review phase, default True for new cards)
    *   `consecutive_correct_reviews` (INTEGER, tracks successive good scores for graduation, reset if score is low)

*   **Reviews Table:**
    *   `review_id` (Primary Key, Auto-incrementing Integer)
    *   `sentence_id` (Foreign Key to Sentences Table)
    *   `review_timestamp` (TIMESTAMP)
    *   `user_score` (FLOAT, 0.0-1.0)
    *   `user_comment_addon` (TEXT, optional, new comment part added by user during this review)
    *   `interval_at_review` (INTEGER, interval before this review)
    *   `ease_factor_at_review` (FLOAT, ease factor before this review)

*   **Initial Data Source:**
    *   A CSV file (e.g., `data/Spanish - 2000 words in context_may_15th_2025.csv`). A script will be needed to parse and import this into the `Sentences` table.

## 6. Non-Functional Requirements

*   **Data Storage:** SQLite database. The database file should be stored within the application directory (e.g., `anki_web_app/database/app.db`).
*   **User Interface:** Simple, clean, and fast. Minimal distractions. Optimized for quick review cycles.
*   **Accessibility:** Basic web accessibility considerations (e.g., keyboard navigation, sufficient contrast).
*   **Security (for single-user self-hosted):** If deployed to a publicly accessible server, implement basic HTTP authentication (e.g., via Nginx) to restrict access. For local-only use, this is a lower priority.
*   **Performance:** App should load quickly and card transitions should be snappy.

### 6.1. Technology Stack

*   **Backend Framework:** Python with Django.
*   **Frontend Framework:** Vue.js.
*   **Database:** SQLite.
*   **Web Server/Reverse Proxy (for deployment):** Nginx.

## 7. Future Considerations/Ideas (Optional V2+)

*   Audio playback for Spanish sentences.
*   Reverse translation (English to Spanish).
*   More sophisticated SRS algorithm tuning and user-adjustable parameters.
*   User accounts if multiple users were to use it (currently scoped for single user).
*   Gamification elements (streaks, points beyond scores, daily goals).
*   Tagging sentences (e.g., by topic, difficulty, grammar point).
*   Backup and restore functionality for the database.

## 8. Open Questions & Clarifications

*   **CSV Structure (Answered):** The delimiter is comma. Encoding needs to be UTF-8 to support special Spanish characters (e.g., ñ, á, é, í, ó, ú, ü). Headers include: `Number`, `Spanish Word`, `English Translation`, `Spanish Example`, `English Example`, `Comment`, `Chat GPTs explanation`, `Gemini explanation`. We will use `Number`, `Spanish Word`, `English Translation` (for key word), `Spanish Example`, `English Example`, `Comment` (as base), and the AI explanation columns.
*   **Key Spanish Word (Answered):** This will be the content of the `Spanish Word` column from the CSV. The associated translation will be from the `English Translation` column.
*   **Initial SRS State (Answered):** New cards are introduced sequentially from the CSV (starting at `Number` 1). The user determines the number of new cards per session. Daily counts of new cards reviewed will be tracked.
*   **"Mastery" Definition (Answered):** A sentence is considered "mastered" for statistical and scheduling purposes when it has been reviewed with a score > 0.8 for the last 3-5 consecutive reviews, AND its current review interval is greater than a significant period (e.g., 21 days). The API currently uses `is_learning=False`, `interval_days >= GRADUATING_INTERVAL_DAYS`, and `consecutive_correct_reviews >= 3`.
*   **Display of Key Spanish Word on Front of Card (Answered):** The front of the card will always show `[Key Spanish Word]: [Spanish Example Sentence]`.
*   **Handling of `Chat GPTs explanation` and `Gemini explanation` columns (Answered):** These will be imported into a single `ai_explanation` field in the `Sentences` table. Initially, this field can be NULL or empty if the CSV columns are blank. We can decide later if we need to merge them if both are present or prefer one.
*   **Bidirectional Learning (Clarification for V2+):** The current (Phase 1) implementation focuses on Spanish to English translation. Each `Sentence` object has one set of SRS parameters. True bidirectional learning (English to Spanish) with independent SRS tracking for each direction for the same conceptual sentence is a V2+ consideration. This might involve treating forward and backward translations as separate "cards" with their own SRS schedules (e.g., by creating two `Sentence` objects per original CSV row or a more complex linked model).

## Phases

**Phase 1: Backend Core (Django) - COMPLETE**

*   **Project Setup & Models (COMPLETE):**
    *   Set up Django project (`spanish_anki_project`) and app (`flashcards`).
    *   Defined `Sentence` and `Review` models in `flashcards/models.py`.
    *   Created and ran initial database migrations.
*   **CSV Data Import (COMPLETE):**
    *   Created `import_csv` Django management command.
    *   Populated `Sentence` table, setting initial SRS parameters.
*   **Spaced Repetition System (SRS) Logic (COMPLETE):**
    *   Implemented SRS algorithm logic in `Sentence.process_review()`.
    *   Handles learning steps, graduation, and lapses.
    *   Updates `ease_factor`, `interval_days`, `next_review_date`, etc.
*   **Django APIs (COMPLETE):**
    *   `GET /api/flashcards/next-card/`: Fetches the next sentence for review.
    *   `POST /api/flashcards/submit-review/`: Accepts review, updates SRS, and comments.
    *   `GET /api/flashcards/statistics/`: Provides dashboard statistics.
    *   `GET /api/flashcards/sentences/`: Provides a paginated list of all sentences with key stats.
    *   `GET /api/flashcards/sentences/<id>/`: Provides detailed history for a specific sentence.

**Phase 2: Frontend (Vue.js) - NEXT**

*   **Vue.js Project Setup & Basic Structure:**
    *   Set up a new Vue.js project (e.g., using Vue CLI).
    *   Organize components (e.g., FlashcardView, DashboardView, SentenceListView).
    *   Set up Vue Router for navigation.
    *   Create services/helpers (e.g., using Axios) to communicate with the Django backend APIs.
    *   Flashcard Interface:
        *   Develop the main flashcard component:
            *   Display front of the card ([Key Spanish Word]: [Spanish Example Sentence]).
            *   Button to "Show Answer".
            *   Display back of the card (translations, original Spanish, comments).
            *   Input fields for score and new comment.
            *   Button to "Submit & Next", which calls the backend API.
    *   Statistics & Dashboard:
        *   Create Vue components to display the statistics fetched from the /api/statistics/ endpoint.
    *   Sentence Management Page:
        *   Create Vue components to display the list of all sentences and their individual statistics/history fetched from /api/sentences/ and /api/sentences/<id>/.
        *   Implement filtering/sorting if desired.
*   **Backup and restore functionality for the database.**


Testing Plan
We'll approach this in phases, building up from backend tests to frontend and E2E tests.
Phase 1: Strengthen Backend API/Integration Tests (Django)
You already have a foundation for API tests with NextCardAPITests. We need to ensure these are complete and then add tests for the other API endpoints. These tests verify that different parts of your Django application (models, views, serializers) work together correctly when an API endpoint is hit.
Location: anki_web_app/flashcards/tests.py
Tool: Django's test client (django.test.Client or rest_framework.test.APIClient).
NextCardAPITests (Review & Enhance):
Ensure existing tests (test_get_next_card_review_card_due, test_get_next_card_new_card_available, etc.) pass reliably now that data import is working.
Add tests for edge cases: What happens if a card's next_review_date is far in the future?
SubmitReviewAPITests (New):
Test successful submission:
Correctly updates Sentence SRS fields (next_review_date, interval_days, ease_factor, is_learning, consecutive_correct_reviews, total_reviews, total_score_sum).
Creates a Review record with correct data.
Appends user_comment_addon to Sentence.base_comment with a timestamp.
Test submission for a new card, a learning card, and a graduated card (to see different SRS transitions).
Test different scores and their impact on SRS parameters.
Test invalid input: non-existent sentence_id, invalid score (e.g., > 1.0).
Test submission without a user_comment_addon.
StatisticsAPITests (New):
Test with an empty database (initial state).
Test after one review.
Test after multiple reviews, including new and review cards.
Test with some cards "learned" and some "mastered" (ensure criteria match PRD).
Verify all fields in the statistics payload are correct (reviews_today, new_cards_reviewed_today, overall_average_score, etc.).
SentenceListAPITests (New):
Test basic retrieval of sentences.
Test pagination:
Correct number of items per page (you mentioned 100).
count, next, previous fields in the response.
Requesting a specific page.
Test default ordering (e.g., by csv_number).
SentenceDetailAPITests (New):
Test retrieval of a specific sentence.
Ensure all required fields (including ease_factor, creation_date, last_modified_date, total_score_sum, consecutive_correct_reviews) are present in the response.
Ensure nested reviews data is correct and complete.
Test for a non-existent sentence ID (should return 404).
Phase 2: Backend Unit Tests (Django)
These tests focus on individual functions or methods in isolation. Your existing 42 tests likely include many of these. We should ensure comprehensive coverage.
Location: anki_web_app/flashcards/tests.py (can be in the same file or separate files for organization).
Models (Sentence, Review):
Sentence.process_review(): Thoroughly test all logic paths for SRS updates based on score and current card state (new, learning steps, graduated, lapse). This is critical.
Sentence._get_quality_from_score(): Test all score ranges.
Test default values on model creation.
Serializers (flashcards/serializers.py):
Test SentenceSerializer.get_average_score() and get_last_reviewed_date() methods.
Test validation logic in ReviewInputSerializer.
Management Commands (import_csv.py):
Test successful import of a few rows.
Test skipping of duplicate csv_number.
Test handling of malformed rows or missing required CSV columns.
Test error if CSV file not found.
Phase 3: Frontend Unit Tests (Vue.js)
These test individual Vue components in isolation.
Location: anki_web_app/spanish_anki_frontend/src/views/*.spec.js (or in a tests/unit directory).
Tool: Vue Test Utils with Jest or Vitest. (We'll need to set this up).
General Approach:
Mock ApiService calls to avoid actual network requests.
Test component rendering based on different props and data.
Test component methods and computed properties.
Components to Test:
FlashcardView.vue:
Initial rendering (shows loading, then card front).
"Show Answer" button functionality.
Correct display of card back information.
Input fields for score and comment.
submitReviewHandler calls ApiService.submitReview (mocked) with correct data and then fetchNextCard.
Handling of 204 "No Content" for next card.
DashboardView.vue:
Calls ApiService.getStatistics (mocked) on mount.
Correctly renders statistics data.
Displays loading/error states.
SentenceListView.vue:
Calls ApiService.getAllSentences (mocked) on mount.
Renders sentences in a table.
Pagination logic (calling fetchSentences with new page number).
SentenceDetailView.vue:
Fetches sentence ID from route params.
Calls ApiService.getSentenceDetails (mocked).
Renders sentence details and review history.
averageScore computed property.
Phase 4: Frontend E2E (End-to-End) Tests (Vue.js)
These tests simulate real user interactions in a browser, testing the entire application stack (frontend + backend).
Location: anki_web_app/spanish_anki_frontend/tests/e2e/specs/ (typical for Cypress).
Tool: Cypress or Playwright. (We'll need to set this up).
Key User Flows to Test:
Full Review Cycle:
Open app, see first card.
Click "Show Answer".
Enter score and comment, click "Submit & Next".
Verify new card loads.
Dashboard Verification:
Perform a few reviews.
Navigate to Dashboard.
Verify statistics reflect the reviews performed.
Sentence List and Detail:
Navigate to Sentences page.
Verify sentences are listed.
Use pagination.
Click "View Details" for a sentence.
Verify sentence details page loads with correct data, including review history matching actions from flow #1.
No Cards Scenario: Test what happens if the API initially returns no cards.
Handling API Errors (Optional but good): If possible, mock API errors at the network level to see how the frontend responds.

---

This document outlines the core requirements for the Anki-Style Spanish Learning App. It should serve as a guide for development.


