import axios from 'axios';

const API_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000/api/flashcards';

// Helper function to handle API requests
const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    getNextCard() {
        return apiClient.get('/next-card/');
    },

    submitReview(sentenceId, score, userCommentAddon) {
        // The backend expects sentence_id in the URL for this specific endpoint
        // or as part of the payload. Based on typical REST patterns for submitting
        // data related to a specific resource, it might be part of the payload
        // or the endpoint might be /submit-review/<sentence_id>/.
        // The PRD says POST /api/flashcards/submit-review/
        // Let's assume sentence_id is part of the payload.
        return apiClient.post('/submit-review/', {
            sentence_id: sentenceId,
            user_score: score,
            user_comment_addon: userCommentAddon,
        });
    },

    getStatistics() {
        return apiClient.get('/statistics/');
    },

    getAllSentences(page = 1) {
        return apiClient.get(`/sentences/?page=${page}`);
    },

    getSentenceDetails(sentenceId) {
        return apiClient.get(`/sentences/${sentenceId}/`);
    },

    // Example of how to handle potential Django CSRF if not using Django Rest Framework's session auth
    // async getCsrfToken() {
    //   try {
    //     await axios.get('http://localhost:8000/api/csrf/', { withCredentials: true }); // Endpoint that sets CSRF cookie
    //   } catch (error) {
    //     console.error('Error fetching CSRF token:', error);
    //   }
    // },

    // // Call this before making POST/PUT/DELETE requests if CSRF is needed
    // async ensureCsrfHeader() {
    //   if (!apiClient.defaults.headers.common['X-CSRFToken']) {
    //     const cookies = document.cookie.split(';');
    //     for (let cookie of cookies) {
    //       const [name, value] = cookie.split('=').map(c => c.trim());
    //       if (name === 'csrftoken') {
    //         apiClient.defaults.headers.common['X-CSRFToken'] = value;
    //         break;
    //       }
    //     }
    //   }
    //   // If still not found, maybe fetch it
    //   if (!apiClient.defaults.headers.common['X-CSRFToken']) {
    //       // This would require a Django endpoint that returns the CSRF token or sets it as a cookie
    //       // For now, assuming DRF's default session/cookie auth handles CSRF for AJAX if logged in,
    //       // or token authentication is used.
    //   }
    // }
}; 