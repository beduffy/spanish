import axios from 'axios';
import SupabaseService from './SupabaseService';

// API URL: Use environment variable or detect based on current host
const getApiUrl = () => {
  // If explicitly set, use it
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL;
  }
  // In production (deployed), use relative URL which will be proxied by nginx
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return '/api/flashcards';
  }
  // Development: use localhost
  return 'http://localhost:8000/api/flashcards';
};

const API_URL = getApiUrl();

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
            // Try to get token with a small retry mechanism
            let token = await SupabaseService.getAccessToken();
            if (!token) {
                // Wait a bit and try once more (for cases where session is still being established)
                await new Promise(resolve => setTimeout(resolve, 100));
                token = await SupabaseService.getAccessToken();
            }
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
                console.log('[API] Added Authorization header to request:', config.url);
                console.log('[API] Token preview:', token.substring(0, 20) + '...');
            } else {
                console.error('[API] No access token available for request:', config.url);
                console.error('[API] Session check:', await SupabaseService.getSession());
            }
        } catch (error) {
            console.error('[API] Failed to get access token:', error);
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

    getCurrentUser() {
        return apiClient.get('/current-user/');
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

    // Reader API methods
    reader: {
        // Lessons
        getLessons(page = 1) {
            if (!page || page < 1) page = 1
            return apiClient.get(`/reader/lessons/?page=${page}`).catch(error => {
                console.error('Error fetching lessons:', error)
                throw error
            })
        },
        
        createLesson(lessonData) {
            if (!lessonData || !lessonData.title || !lessonData.text) {
                return Promise.reject(new Error('Lesson data is required'))
            }
            return apiClient.post('/reader/lessons/', lessonData).catch(error => {
                console.error('Error creating lesson:', error)
                throw error
            })
        },
        
        getLesson(lessonId) {
            if (!lessonId) {
                return Promise.reject(new Error('Lesson ID is required'))
            }
            return apiClient.get(`/reader/lessons/${lessonId}/`).catch(error => {
                console.error('Error fetching lesson:', error)
                throw error
            })
        },
        
        updateLesson(lessonId, lessonData) {
            if (!lessonId) {
                return Promise.reject(new Error('Lesson ID is required'))
            }
            if (!lessonData) {
                return Promise.reject(new Error('Lesson data is required'))
            }
            return apiClient.put(`/reader/lessons/${lessonId}/update/`, lessonData).catch(error => {
                console.error('Error updating lesson:', error)
                throw error
            })
        },
        
        deleteLesson(lessonId) {
            if (!lessonId) {
                return Promise.reject(new Error('Lesson ID is required'))
            }
            return apiClient.delete(`/reader/lessons/${lessonId}/delete/`).catch(error => {
                console.error('Error deleting lesson:', error)
                throw error
            })
        },
        
        // Translation
        translateText(text, sourceLang = 'de', targetLang = 'en') {
            if (!text) {
                return Promise.reject(new Error('Text is required'))
            }
            return apiClient.post('/reader/translate/', {
                text,
                source_lang: sourceLang,
                target_lang: targetLang,
            }).catch(error => {
                console.error('Error translating text:', error)
                throw error
            })
        },
        
        // Token interaction
        clickToken(tokenId) {
            if (!tokenId) {
                return Promise.reject(new Error('Token ID is required'))
            }
            return apiClient.get(`/reader/tokens/${tokenId}/click/`).catch(error => {
                console.error('Error clicking token:', error)
                throw error
            })
        },
        
        // Phrase creation
        createPhrase(lessonId, startOffset, endOffset) {
            if (!lessonId || startOffset === undefined || endOffset === undefined) {
                return Promise.reject(new Error('Lesson ID, start offset, and end offset are required'))
            }
            return apiClient.post('/reader/phrases/create/', {
                lesson_id: lessonId,
                start_offset: startOffset,
                end_offset: endOffset
            }).catch(error => {
                console.error('Error creating phrase:', error)
                throw error
            })
        },
        
        // Add to flashcards
        addToFlashcards(data) {
            if (!data || (!data.token_id && !data.phrase_id) || !data.front || !data.lesson_id) {
                return Promise.reject(new Error('Invalid flashcard data'))
            }
            return apiClient.post('/reader/add-to-flashcards/', data).catch(error => {
                console.error('Error adding to flashcards:', error)
                throw error
            })
        },
        
        // TTS
        generateTTS(lessonId, text = null, languageCode = 'de-DE') {
            if (!lessonId && !text) {
                return Promise.reject(new Error('Lesson ID or text is required'))
            }
            return apiClient.post('/reader/generate-tts/', {
                lesson_id: lessonId,
                text,
                language_code: languageCode,
            }).catch(error => {
                console.error('Error generating TTS:', error)
                throw error
            })
        },
        
        // Listening time tracking
        updateListeningTime(lessonId, secondsListened) {
            if (!lessonId || secondsListened === undefined) {
                return Promise.reject(new Error('Lesson ID and seconds listened are required'))
            }
            return apiClient.post(`/reader/lessons/${lessonId}/listening-time/`, {
                lesson_id: lessonId,
                seconds_listened: secondsListened,
            }).catch(error => {
                console.error('Error updating listening time:', error)
                throw error
            })
        },
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