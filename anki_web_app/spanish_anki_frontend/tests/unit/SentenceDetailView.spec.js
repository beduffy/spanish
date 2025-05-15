import { mount, RouterLinkStub } from '@vue/test-utils';
import SentenceDetailView from '@/views/SentenceDetailView.vue';
import ApiService from '@/services/ApiService';

jest.mock('@/services/ApiService');

const mockSentenceId = '123';
const mockSentenceData = {
    sentence_id: mockSentenceId,
    csv_number: 101,
    key_spanish_word: 'Hola',
    key_word_english_translation: 'Hello',
    spanish_sentence_example: 'Hola Mundo',
    english_sentence_example: 'Hello World',
    base_comment: 'Greeting example',
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


describe('SentenceDetailView.vue', () => {
    let wrapper;

    const mountComponent = (routeParams = { id: mockSentenceId }, apiMock) => {
        ApiService.getSentenceDetails = apiMock || jest.fn().mockResolvedValue({ status: 200, data: mockSentenceData });
        return mount(SentenceDetailView, {
            global: {
                mocks: {
                    $route: {
                        params: routeParams,
                    },
                },
                stubs: {
                    RouterLink: RouterLinkStub,
                },
            },
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });


    it('renders loading message initially and fetches sentence details', async () => {
        wrapper = mountComponent();
        expect(wrapper.find('.loading-message').exists()).toBe(true);
        expect(wrapper.find('.loading-message p').text()).toBe('Loading sentence details...');

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getSentenceDetails).toHaveBeenCalledWith(mockSentenceId);
        expect(wrapper.find('.loading-message').exists()).toBe(false);
        expect(wrapper.find('.sentence-content').exists()).toBe(true);
        expect(wrapper.find('h1').text()).toContain(`Sentence Detail (#${mockSentenceData.csv_number})`);
    });


    it('displays sentence details correctly', async () => {
        wrapper = mountComponent();
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        const mainDetails = wrapper.find('.main-details');
        expect(mainDetails.text()).toContain(mockSentenceData.key_spanish_word);
        expect(mainDetails.text()).toContain(mockSentenceData.spanish_sentence_example);
        expect(mainDetails.text()).toContain(mockSentenceData.base_comment);

        const srsDetails = wrapper.find('.srs-details');
        expect(srsDetails.text()).toContain(`Status: ${mockSentenceData.is_learning ? 'Learning' : 'Review'}`);
        expect(srsDetails.text()).toContain(`Interval: ${mockSentenceData.interval_days} days`);
        expect(srsDetails.text()).toContain(`Ease Factor: ${mockSentenceData.ease_factor.toFixed(2)}`);
        expect(srsDetails.text()).toContain(`Avg. Score: 0.80`); // Calculated by averageScore computed property
    });


    it('computes and displays averageScore correctly', async () => {
        wrapper = mountComponent();
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        expect(wrapper.vm.averageScore).toBe('0.80');

        // Test with no reviews
        const noReviewsData = { ...mockSentenceData, total_reviews: 0, total_score_sum: 0, reviews: [] };
        wrapper = mountComponent(
            { id: '456' },
            jest.fn().mockResolvedValue({ status: 200, data: noReviewsData })
        );
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        expect(wrapper.vm.averageScore).toBe('N/A');
    });


    it('displays review history correctly', async () => {
        wrapper = mountComponent();
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        const reviewRows = wrapper.findAll('.review-history tbody tr');
        expect(reviewRows.length).toBe(mockSentenceData.reviews.length);
        const firstReviewRowCells = reviewRows.at(0).findAll('td');
        expect(firstReviewRowCells.at(0).text()).toBe(wrapper.vm.formatDateTime(mockSentenceData.reviews[0].review_timestamp));
        expect(firstReviewRowCells.at(1).text()).toBe(mockSentenceData.reviews[0].user_score.toFixed(1));
        expect(firstReviewRowCells.at(3).text()).toBe(mockSentenceData.reviews[0].ease_factor_at_review.toFixed(2));
        expect(firstReviewRowCells.at(4).find('pre').text()).toBe(mockSentenceData.reviews[0].user_comment_addon);
    });


    it('displays "no reviews" message if review history is empty', async () => {
        const noReviewsData = { ...mockSentenceData, reviews: [] };
        wrapper = mountComponent({ id: mockSentenceId }, jest.fn().mockResolvedValue({ status: 200, data: noReviewsData }));
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.review-history p').exists()).toBe(true);
        expect(wrapper.find('.review-history p').text()).toBe('No reviews recorded for this sentence yet.');
    });


    it('displays error message if fetching details fails with 404', async () => {
        const sentenceIdNotFound = '999';
        const specificMock = jest.fn().mockRejectedValue({ response: { status: 404 } });
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        wrapper = mountComponent({ id: sentenceIdNotFound }, specificMock);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe(`Sentence with ID ${sentenceIdNotFound} not found.`);
        consoleErrorSpy.mockRestore();
    });


    it('displays generic error message if fetching details fails with other error', async () => {
        const specificMock = jest.fn().mockRejectedValue(new Error('Network Error'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        wrapper = mountComponent(undefined, specificMock);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain(`Failed to load details for sentence ID ${mockSentenceId}`);
        consoleErrorSpy.mockRestore();
    });


    it('displays error if no sentence ID is provided in route', async () => {
        wrapper = mountComponent({ id: null }); // No ID in route params

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getSentenceDetails).not.toHaveBeenCalled();
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe('No sentence ID provided in the route.');
    });


    describe('formatDate and formatDateTime methods', () => {
        beforeEach(() => {
            // Mount with any valid setup just to access vm methods
            wrapper = mountComponent();
        });

        it('formatDate correctly', () => {
            expect(wrapper.vm.formatDate('2024-01-15T10:00:00Z')).toBe('Jan 15, 2024');
            expect(wrapper.vm.formatDate(null)).toBe('N/A');
        });

        it('formatDateTime correctly', () => {
            // Note: specific time output can be locale-dependent.
            // This checks for parts of the date and time rather than an exact match if needed.
            const formatted = wrapper.vm.formatDateTime('2024-01-15T10:30:00Z');
            expect(formatted).toContain('Jan 15, 2024');
            expect(formatted).toMatch(/\d{1,2}:\d{2}\s*(AM|PM)?/i); // Checks for H:MM AM/PM or HH:MM
            expect(wrapper.vm.formatDateTime(null)).toBe('N/A');
        });
    });
}); 