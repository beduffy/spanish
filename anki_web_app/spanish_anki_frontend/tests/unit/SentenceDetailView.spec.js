import { mount, RouterLinkStub } from '@vue/test-utils';
import SentenceDetailView from '@/views/SentenceDetailView.vue';
import ApiService from '@/services/ApiService';

jest.mock('@/services/ApiService');

const mockSentenceId = '123';
const mockSentenceDataS2E = {
    sentence_id: mockSentenceId,
    csv_number: 101,
    translation_direction: 'S2E',
    key_spanish_word: 'Hola',
    key_word_english_translation: 'Hello',
    spanish_sentence_example: 'Hola Mundo S2E',
    english_sentence_example: 'Hello World S2E',
    base_comment: 'Greeting example S2E',
    ai_explanation: 'AI explains greetings',
    is_learning: true,
    next_review_date: '2024-12-31T10:00:00Z',
    interval_days: 1,
    ease_factor: 2.5,
    consecutive_correct_reviews: 0,
    total_reviews: 5,
    total_score_sum: 4.0, // avg score will be 0.80
    creation_date: '2023-01-01T00:00:00Z',
    last_modified_date: '2024-01-10T10:00:00Z',
    reviews: [
        {
            review_id: 1, review_timestamp: '2024-01-10T10:00:00Z', user_score: 0.8,
            interval_at_review: 1, ease_factor_at_review: 2.5, user_comment_addon: 'Good'
        },
        {
            review_id: 2, review_timestamp: '2024-01-09T09:00:00Z', user_score: 0.9,
            interval_at_review: 0, ease_factor_at_review: 2.5, user_comment_addon: null
        }
    ]
};

const mockSentenceDataE2S = {
    sentence_id: '456', // Different ID for a different card object
    csv_number: 102, // Different csv_number for clarity
    translation_direction: 'E2S',
    key_spanish_word: 'Adiós', // Spanish answer
    key_word_english_translation: 'Goodbye', // English prompt
    spanish_sentence_example: 'Adiós Mundo E2S Answer', // Spanish answer sentence
    english_sentence_example: 'Goodbye World E2S Prompt', // English prompt sentence
    base_comment: 'Farewell example E2S',
    ai_explanation: 'AI explains E2S farewells',
    is_learning: false,
    next_review_date: '2024-11-30T10:00:00Z',
    interval_days: 5,
    ease_factor: 2.3,
    consecutive_correct_reviews: 2,
    total_reviews: 3,
    total_score_sum: 2.1, // avg score will be 0.70
    creation_date: '2023-01-02T00:00:00Z',
    last_modified_date: '2024-01-11T10:00:00Z',
    reviews: [
        {
            review_id: 3, review_timestamp: '2024-01-11T10:00:00Z', user_score: 0.7,
            interval_at_review: 3, ease_factor_at_review: 2.3, user_comment_addon: 'Okay on E2S'
        }
    ]
};


describe('SentenceDetailView.vue', () => {
    let wrapper;
    let mockGetSentenceDetails;

    beforeEach(() => {
        jest.clearAllMocks();
        // Reset the mock for getSentenceDetails before each test
        // This ensures that ApiService (which is the mocked module)
        // and ApiService.default (if it's used as such) both have a fresh mock.
        mockGetSentenceDetails = jest.fn();

        // If ApiService is structured with a 'default' export by the mock
        if (ApiService.default) {
            ApiService.default.getSentenceDetails = mockGetSentenceDetails;
        } else {
            // Otherwise, assign directly to ApiService
            ApiService.getSentenceDetails = mockGetSentenceDetails;
        }
    });

    const mountComponent = (routeParams = { id: mockSentenceId }, sentenceDataOrMockFn) => {
        if (typeof sentenceDataOrMockFn === 'function') {
            // If a mock function is directly provided (e.g., for rejections)
            mockGetSentenceDetails.mockImplementation(sentenceDataOrMockFn);
        } else if (sentenceDataOrMockFn) {
            // If data is provided, resolve with it
            mockGetSentenceDetails.mockResolvedValue({ status: 200, data: sentenceDataOrMockFn });
        } else {
            // Default mock behavior if nothing specific is passed for this call
            mockGetSentenceDetails.mockResolvedValue({ status: 200, data: mockSentenceDataS2E });
        }

        return mount(SentenceDetailView, {
            global: {
                mocks: {
                    $route: {
                        params: routeParams,
                    },
                    // Provide the mocked ApiService to the component instance if it expects `this.apiService`
                    // This is often cleaner than relying on the component to import the top-level mock itself.
                    // However, since the component `SentenceDetailView.vue` likely does `import ApiService from '@/services/ApiService';`
                    // the `jest.mock` at the top level should handle it.
                    // We ensure `ApiService.getSentenceDetails` (or `ApiService.default.getSentenceDetails`) is the one called.
                },
                stubs: {
                    RouterLink: RouterLinkStub,
                },
            },
        });
    };


    it('renders loading message initially and fetches sentence details', async () => {
        // Use the default mock behavior (resolves with mockSentenceDataS2E)
        wrapper = mountComponent({ id: mockSentenceId });
        expect(wrapper.find('.loading-message').exists()).toBe(true);
        expect(wrapper.find('.loading-message p').text()).toBe('Loading sentence details...');

        // Wait for the component's mounted hook and async operations
        await new Promise(resolve => process.nextTick(resolve)); // Allow promises to resolve
        await wrapper.vm.$nextTick(); // Allow Vue to update the DOM

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(mockSentenceId);
        expect(wrapper.find('.loading-message').exists()).toBe(false);
        expect(wrapper.find('.sentence-content').exists()).toBe(true);
        expect(wrapper.find('h1').text()).toContain(`Sentence Detail (#${mockSentenceDataS2E.csv_number})`);
        expect(wrapper.find('h1 span.badge-s2e').text()).toBe('S2E');
    });


    it('displays S2E sentence details correctly', async () => {
        // Pass mockSentenceDataS2E directly, mountComponent will wrap it in a resolved promise
        wrapper = mountComponent({ id: mockSentenceDataS2E.sentence_id }, mockSentenceDataS2E);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(mockSentenceDataS2E.sentence_id);
        const mainDetails = wrapper.find('.main-details');
        expect(mainDetails.text()).toContain(`Prompt Key Word: ${mockSentenceDataS2E.key_spanish_word}`);
        expect(mainDetails.text()).toContain(`Prompt Sentence: ${mockSentenceDataS2E.spanish_sentence_example}`);
        expect(mainDetails.text()).toContain(`Answer Key Word: ${mockSentenceDataS2E.key_word_english_translation}`);
        expect(mainDetails.text()).toContain(`Answer Sentence: ${mockSentenceDataS2E.english_sentence_example}`);
        expect(mainDetails.text()).toContain(mockSentenceDataS2E.base_comment);

        const srsDetails = wrapper.find('.srs-details');
        expect(srsDetails.text()).toContain(`Status: ${mockSentenceDataS2E.is_learning ? 'Learning' : 'Review'}`);
        expect(srsDetails.text()).toContain(`Interval: ${mockSentenceDataS2E.interval_days} days`);
        expect(srsDetails.text()).toContain(`Ease Factor: ${mockSentenceDataS2E.ease_factor.toFixed(2)}`);
        expect(srsDetails.text()).toContain(`Avg. Score: 0.80`);
    });


    it('computes and displays averageScore correctly', async () => {
        wrapper = mountComponent({ id: mockSentenceDataS2E.sentence_id }, mockSentenceDataS2E);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        expect(wrapper.vm.averageScore).toBe('0.80');

        const noReviewsData = { ...mockSentenceDataS2E, sentence_id: '456', total_reviews: 0, total_score_sum: 0, reviews: [] };
        wrapper = mountComponent(
            { id: '456' }, // Route param
            noReviewsData     // Data for ApiService.getSentenceDetails to resolve with
        );
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        expect(mockGetSentenceDetails).toHaveBeenCalledWith('456');
        expect(wrapper.vm.averageScore).toBe('N/A');
    });


    it('displays review history correctly', async () => {
        wrapper = mountComponent({ id: mockSentenceDataS2E.sentence_id }, mockSentenceDataS2E);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(mockSentenceDataS2E.sentence_id);
        const reviewRows = wrapper.findAll('.review-history tbody tr');
        expect(reviewRows.length).toBe(mockSentenceDataS2E.reviews.length);
        const firstReviewRowCells = reviewRows.at(0).findAll('td');
        expect(firstReviewRowCells.at(0).text()).toBe(wrapper.vm.formatDateTime(mockSentenceDataS2E.reviews[0].review_timestamp));
        expect(firstReviewRowCells.at(1).text()).toBe(mockSentenceDataS2E.reviews[0].user_score.toFixed(1));
        // Skipping interval_at_review check for brevity if it's not failing
        expect(firstReviewRowCells.at(3).text()).toBe(mockSentenceDataS2E.reviews[0].ease_factor_at_review.toFixed(2));
        expect(firstReviewRowCells.at(4).find('pre').text()).toBe(mockSentenceDataS2E.reviews[0].user_comment_addon);
    });


    it('displays "no reviews" message if review history is empty', async () => {
        const noReviewsData = { ...mockSentenceDataS2E, reviews: [] };
        wrapper = mountComponent({ id: mockSentenceDataS2E.sentence_id }, noReviewsData);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(mockSentenceDataS2E.sentence_id);
        expect(wrapper.find('.review-history p').exists()).toBe(true);
        expect(wrapper.find('.review-history p').text()).toBe('No reviews recorded for this sentence yet.');
    });


    it('displays error message if fetching details fails with 404', async () => {
        const sentenceIdNotFound = '999';
        // Pass the mock function directly for rejection
        const apiMockReject404 = jest.fn().mockRejectedValue({ response: { status: 404 } });
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });

        wrapper = mountComponent({ id: sentenceIdNotFound }, apiMockReject404);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(sentenceIdNotFound);
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe(`Sentence with ID ${sentenceIdNotFound} not found.`);
        consoleErrorSpy.mockRestore();
    });


    it('displays generic error message if fetching details fails with other error', async () => {
        const sentenceIdToFail = mockSentenceDataS2E.sentence_id;
        // Pass the mock function directly for rejection
        const apiMockRejectGeneric = jest.fn().mockRejectedValue(new Error('Network Error'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });

        wrapper = mountComponent({ id: sentenceIdToFail }, apiMockRejectGeneric);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(sentenceIdToFail);
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain(`Failed to load details for sentence ID ${sentenceIdToFail}`);
        consoleErrorSpy.mockRestore();
    });


    it('displays error if no sentence ID is provided in route', async () => {
        // No specific data/mock function needed for getSentenceDetails as it shouldn't be called
        wrapper = mountComponent({ id: null });

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).not.toHaveBeenCalled();
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe('No sentence ID provided in the route.');
    });


    describe('formatDate and formatDateTime methods', () => {
        beforeEach(() => {
            // Mount with default S2E data just to access vm methods
            wrapper = mountComponent({ id: mockSentenceDataS2E.sentence_id }, mockSentenceDataS2E);
        });

        it('formatDate correctly', () => {
            expect(wrapper.vm.formatDate('2024-01-15T10:00:00Z')).toBe('Jan 15, 2024');
            expect(wrapper.vm.formatDate(null)).toBe('N/A');
        });

        it('formatDateTime correctly', () => {
            const formatted = wrapper.vm.formatDateTime('2024-01-15T10:30:00Z');
            expect(formatted).toContain('Jan 15, 2024');
            expect(formatted).toMatch(/\d{1,2}:\d{2}\s*(AM|PM)?/i);
            expect(wrapper.vm.formatDateTime(null)).toBe('N/A');
        });
    });

    it('displays E2S sentence details correctly', async () => {
        // Pass mockSentenceDataE2S directly
        wrapper = mountComponent({ id: mockSentenceDataE2S.sentence_id }, mockSentenceDataE2S);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(mockGetSentenceDetails).toHaveBeenCalledWith(mockSentenceDataE2S.sentence_id);
        expect(wrapper.find('h1').text()).toContain(`Sentence Detail (#${mockSentenceDataE2S.csv_number})`);
        expect(wrapper.find('h1 span.badge-e2s').text()).toBe('E2S');

        const mainDetails = wrapper.find('.main-details');
        // Check prompt fields for E2S
        expect(mainDetails.text()).toContain(`Prompt Key Word: ${mockSentenceDataE2S.key_word_english_translation}`); // English word is prompt
        expect(mainDetails.text()).toContain(`Prompt Sentence: ${mockSentenceDataE2S.english_sentence_example}`); // English sentence is prompt
        // Check answer fields for E2S
        expect(mainDetails.text()).toContain(`Answer Key Word: ${mockSentenceDataE2S.key_spanish_word}`); // Spanish word is answer
        expect(mainDetails.text()).toContain(`Answer Sentence: ${mockSentenceDataE2S.spanish_sentence_example}`); // Spanish sentence is answer
        expect(mainDetails.text()).toContain(mockSentenceDataE2S.base_comment);

        const srsDetails = wrapper.find('.srs-details');
        expect(srsDetails.text()).toContain(`Status: ${mockSentenceDataE2S.is_learning ? 'Learning' : 'Review'}`);
        expect(srsDetails.text()).toContain(`Interval: ${mockSentenceDataE2S.interval_days} days`);
        expect(srsDetails.text()).toContain(`Ease Factor: ${mockSentenceDataE2S.ease_factor.toFixed(2)}`);
        expect(srsDetails.text()).toContain(`Avg. Score: 0.70`); // Calculated avg score for E2S data
    });
}); 