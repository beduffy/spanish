# Product Requirements Document: Anki-Style Spanish Learning App

## Original prompt:
Here is my latest csv. Could you build me a Plan document for a HTML app that will test with anki cards on each sentence from Spanish to english and Spanish to german (but also mention the spanish and english word). Maybe initially I will just say/think the translation (actually this requires less typing which is best) e.g.

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

This document outlines the requirements for a web application designed to help the user learn Spanish sentences and vocabulary through an Anki-style flashcard system. The primary goal is to facilitate the memorization and understanding of approximately 2000 Spanish sentences, with translations to English and German, and to track progress effectively.

## 2. Goals

*   Efficiently learn and retain ~2000 Spanish sentences.
*   Practice translation from Spanish to English.
*   Practice translation from Spanish to German (while also seeing the English translation and Spanish word).
*   Track subjective understanding and recall for each sentence.
*   Implement a spaced repetition system (SRS) to optimize learning.
*   Provide clear metrics on learning progress.
*   Create a simple, fast, and intuitive user experience.

## 3. User Stories

*   **As a user, I want to be shown a Spanish sentence so I can practice translating it in my head.**
*   **As a user, after thinking of the translation, I want to click a button to reveal the correct English and German translations, along with the original Spanish sentence and a key Spanish word with its English translation.**
*   **As a user, I want to be able to add a timestamped comment to my review of a sentence, noting any difficulties or insights (e.g., "forgot to say 'city'").**
*   **As a user, I want to give myself a subjective score (e.g., 0.0 to 1.0) for each sentence translation attempt to track my understanding.**
*   **As a user, I want to submit my comment and score and immediately move to the next sentence/card.**
*   **As a user, I want to see statistics about my learning, including:**
    *   Number of cards reviewed today, this week, and overall.
    *   Overall average score.
    *   Number of unique sentences seen out of the total.
    *   My average score on these seen sentences.
*   **As a user, I want the app to tell me when I last reviewed a specific sentence.**
*   **As a user, I want a dedicated page where I can see all sentences, their individual statistics, how easy I find each one, and a history of my scores for each (e.g., a mini-graph showing score progression).**
*   **As a user, I want the app to use a spaced repetition algorithm so that sentences I find easy are shown less frequently, and new or difficult sentences are shown more often.**

## 4. Core Features

### 4.1. Learning Flow (Flashcard Interface)

*   **Card Display (Front - "Input"):**
    *   Show the Spanish sentence (e.g., "De: Él es de la ciudad de Nueva York").
*   **User Action: Think/Say Translation.**
*   **User Action: Click "Show Answer".**
*   **Card Display (Back - "Answer"):**
    *   Original Spanish sentence.
    *   Key Spanish word and its English translation (e.g., "De = From").
    *   English translation (e.g., "He is from New York City.").
    *   German translation (e.g., "Er kommt aus New York City.")
    *   Existing comments, including any previously user-added timestamped notes.
*   **User Input Fields:**
    *   Text area for new comment.
    *   Input for subjective score (0.0 - 1.0).
*   **User Action: Click "Submit & Next".**

### 4.2. Scoring and Comments

*   Users can assign a numerical score (float between 0.0 and 1.0) to each review attempt.
*   Users can add free-text comments.
*   Comments will be appended to a running log for that specific sentence, with a timestamp (e.g., "15:31 May 15th: ahhhh I forgot to say city").

### 4.3. Spaced Repetition System (SRS)

*   The system will decide which card to show next based on an SRS algorithm (e.g., a simplified version of Anki's SM2 algorithm or similar).
*   Factors influencing card scheduling:
    *   User's score on previous reviews of the card.
    *   Time since the card was last reviewed.
    *   Overall learning progress.
*   New cards will be introduced gradually.
*   Cards mastered will appear less frequently.

### 4.4. Progress Tracking & Statistics

*   **Dashboard/Overview Page:**
    *   Cards reviewed today.
    *   Cards reviewed this week.
    *   Total cards reviewed.
    *   Overall average score.
    *   Number of unique sentences mastered (e.g., consistently scoring >0.9).
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
    *   Potentially filter/sort sentences (e.g., by difficulty, last reviewed).

## 5. Data Model (High-Level - SQL Database)

*   **Sentences Table:**
    *   `sentence_id` (Primary Key)
    *   `spanish_sentence` (TEXT)
    *   `english_translation` (TEXT)
    *   `german_translation` (TEXT)
    *   `key_spanish_word` (TEXT, optional, if a specific word from the sentence is highlighted)
    *   `key_word_english_translation` (TEXT, optional)
    *   `base_comment` (TEXT, e.g., "Literal translation: He is from the city of New York")
    *   `creation_date` (TIMESTAMP)
    *   `last_modified_date` (TIMESTAMP)
    *   *(SRS-related fields like `ease_factor`, `interval`, `next_review_date` will be stored here or in a linked table)*

*   **Reviews Table:**
    *   `review_id` (Primary Key)
    *   `sentence_id` (Foreign Key to Sentences Table)
    *   `review_timestamp` (TIMESTAMP)
    *   `user_score` (FLOAT, 0.0-1.0)
    *   `user_comment` (TEXT, optional)

*   **Initial Data Source:**
    *   A CSV file containing the ~2000 sentences and their translations. A script will be needed to import this into the `Sentences` table.

## 6. Non-Functional Requirements

*   **Data Storage:** SQL database (e.g., SQLite for simplicity to start, potentially PostgreSQL or MySQL for more robust deployment).
*   **User Interface:** Simple, clean, and fast. Minimal distractions.
*   **Accessibility:** Basic web accessibility considerations.

## 7. Future Considerations/Ideas (Optional V2+)

*   Audio playback for Spanish sentences.
*   Reverse translation (English/German to Spanish).
*   More sophisticated SRS algorithm tuning.
*   User accounts if multiple users were to use it (currently scoped for single user).
*   Gamification elements (streaks, points beyond scores).
*   Tagging sentences.

## 8. Open Questions & Clarifications

*   **CSV Structure:** What is the exact structure of the input CSV? (Number of columns, headers, delimiter).
*   **Key Spanish Word:** Is the "key Spanish word" always a single word from the sentence, or can it be a phrase? How is this determined? Is it always "De" as in the example, or does it vary per sentence?
*   **German Translations:** Are German translations readily available for all sentences in the CSV?
*   **Initial SRS State:** How should new cards be prioritized initially?
*   **"Mastery" Definition:** How do we define when a sentence is "mastered" for statistical purposes (e.g., N successful reviews in a row, average score above X)?

---

This initial draft should provide a good foundation. We can iterate on this as we discuss further.
