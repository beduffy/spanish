import axios from 'axios';
import SupabaseService from './SupabaseService';

const API_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000/api/flashcards';

// Helper function to handle API requests
const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add request interceptor to include Authorization header with Supabase token
apiClient.interceptors.request.use(
    async (config) => {
        try {
            const token = await SupabaseService.getAccessToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
                console.debug('Added Authorization header to request:', config.url);
            } else {
                console.warn('No access token available for request:', config.url);
            }
        } catch (error) {
            console.warn('Failed to get access token:', error);
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add response interceptor to handle 401 (unauthorized) and 403 (forbidden) errors
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401 || error.response?.status === 403) {
            // User is not authenticated or lacks permission
            // Only redirect if not already on login page
            if (window.location.pathname !== '/login') {
                // Don't auto-redirect, let the component handle it gracefully
                // This allows components to show a message instead of forcing redirect
                console.warn('Authentication required for:', error.config?.url);
            }
        }
        return Promise.reject(error);
    }
);

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

    getNextCardV2() {
        return apiClient.get('/cards/next-card/');
    },

    submitCardReview(cardId, score, userCommentAddon, typedInput, sessionId = null) {
        const payload = {
            card_id: cardId,
            user_score: score,
            user_comment_addon: userCommentAddon,
            typed_input: typedInput,
        };
        if (sessionId) {
            payload.session_id = sessionId;
        }
        return apiClient.post('/cards/submit-review/', payload);
    },

    getStudySessions() {
        return apiClient.get('/sessions/');
    },

    startStudySession() {
        return apiClient.post('/sessions/start/');
    },

    endStudySession(sessionId) {
        return apiClient.post('/sessions/end/', { session_id: sessionId });
    },

    getCardStatistics() {
        return apiClient.get('/cards/statistics/');
    },

    getAllSentences(page = 1) {
        return apiClient.get(`/sentences/?page=${page}`);
    },

    getSentenceDetails(sentenceId) {
        return apiClient.get(`/sentences/${sentenceId}/`);
    },

    getAllCards(page = 1) {
        return apiClient.get(`/cards/?page=${page}`);
    },

    getCardDetails(cardId) {
        return apiClient.get(`/cards/${cardId}/`);
    },

    createCard(cardData) {
        return apiClient.post('/cards/', cardData);
    },

    updateCard(cardId, cardData) {
        return apiClient.put(`/cards/${cardId}/update/`, cardData);
    },

    deleteCard(cardId) {
        return apiClient.delete(`/cards/${cardId}/delete/`);
    },

    importCards(file, frontColumn, backColumn, language = '', createReverse = true, delimiter = null, previewOnly = false) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('front_column', frontColumn);
        formData.append('back_column', backColumn);
        formData.append('language', language);
        formData.append('create_reverse', createReverse);
        formData.append('preview_only', previewOnly);
        if (delimiter) {
            formData.append('delimiter', delimiter);
        }
        return apiClient.post('/cards/import/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
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