import { mount } from '@vue/test-utils';
import DashboardView from '@/views/DashboardView.vue';
import ApiService from '@/services/ApiService';

// Mock the entire ApiService module
// This will replace the actual ApiService with a mock version where all its exports are mock functions.
jest.mock('@/services/ApiService');

describe('DashboardView.vue', () => {
    let wrapper;

    const mockStatistics = {
        reviews_today: 10,
        new_cards_reviewed_today: 5,
        reviews_this_week: 50,
        total_reviews_all_time: 500,
        overall_average_score: 0.85,
        total_sentences: 2000,
        sentences_learned: 200,
        percentage_learned: 10, // Assuming backend sends this as a whole number
        sentences_mastered: 50,
    };

    beforeEach(() => {
        // Reset all mocks before each test
        jest.clearAllMocks();

        // Since ApiService is a default export (an object with methods),
        // and we've auto-mocked the module, we need to ensure the functions on that default export are jest.fn()
        // OR specifically provide implementations for them. If ApiService itself (the default export)
        // is not being correctly assigned as a mock object, this might still be tricky.
        // A common pattern is that jest.mock effectively does this:
        // ApiService = { getStatistics: jest.fn(), otherMethod: jest.fn(), ... }
        // So, when DashboardView imports ApiService, it gets this mocked object.

        // Let's ensure the getStatistics function on the (now mocked) ApiService object is a fresh jest.fn for each test run,
        // and we can control its return value per test.
        // Note: If ApiService was a class, mocking would be different.
        // If the auto-mock is sufficient, we might not need this line, but it adds explicitness.
        ApiService.getStatistics = jest.fn();
    });

    it('renders the dashboard title', async () => {
        ApiService.getStatistics.mockResolvedValue({
            status: 200,
            data: { reviews_today: 0 } // Minimal mock data
        });
        wrapper = mount(DashboardView);
        // Let promise resolve and Vue update
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        expect(wrapper.find('h1').text()).toBe('Dashboard');
    });

    it('calls ApiService.getStatistics on mount', async () => { // Made async to allow for promise resolution if needed by mount
        ApiService.getStatistics.mockResolvedValue({ status: 200, data: {} });
        wrapper = mount(DashboardView);
        // Allow mounted hook to complete if it has async parts before the expect()
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        expect(ApiService.getStatistics).toHaveBeenCalledTimes(1);
    });

    it('renders loading message initially and fetches statistics', async () => {
        ApiService.getStatistics.mockResolvedValue({ status: 200, data: mockStatistics });
        wrapper = mount(DashboardView);

        expect(wrapper.find('.loading-message').exists()).toBe(true);
        expect(wrapper.find('.loading-message p').text()).toBe('Loading statistics...');

        // Wait for promises to resolve and DOM to update
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getStatistics).toHaveBeenCalledTimes(1);
        expect(wrapper.find('.loading-message').exists()).toBe(false);
        expect(wrapper.find('.statistics-grid').exists()).toBe(true);
    });

    it('displays statistics correctly after successful fetch', async () => {
        ApiService.getStatistics.mockResolvedValue({ status: 200, data: mockStatistics });
        wrapper = mount(DashboardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        const statCards = wrapper.findAll('.stat-card');
        expect(statCards.length).toBe(8); // Ensure all 8 stat cards are rendered

        expect(statCards.at(0).find('h2').text()).toBe('Reviews Today');
        expect(statCards.at(0).find('p').text()).toBe(mockStatistics.reviews_today.toString());

        expect(statCards.at(1).find('h2').text()).toBe('New Cards Today');
        expect(statCards.at(1).find('p').text()).toBe(mockStatistics.new_cards_reviewed_today.toString());

        expect(statCards.at(4).find('h2').text()).toBe('Avg. Score');
        expect(statCards.at(4).find('p').text()).toBe('0.85'); // From formatScore

        expect(statCards.at(6).find('h2').text()).toBe('Sentences Learned');
        expect(statCards.at(6).find('p').text()).toBe(`${mockStatistics.sentences_learned} (${mockStatistics.percentage_learned}%)`);
    });

    it('displays error message if fetching statistics fails', async () => {
        ApiService.getStatistics.mockRejectedValue(new Error('Network Error'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        wrapper = mount(DashboardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe('Failed to load statistics. Please check your connection or try again later.');
        expect(wrapper.find('.statistics-grid').exists()).toBe(false);
        expect(consoleErrorSpy).toHaveBeenCalledWith("Error fetching statistics:", expect.any(Error));
        consoleErrorSpy.mockRestore();
    });

    it('displays specific error message if API returns non-200 or no data', async () => {
        ApiService.getStatistics.mockResolvedValue({ status: 201, data: null }); // Example of unexpected response
        wrapper = mount(DashboardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe("Could not load statistics. The server didn't return valid data.");
    });

    it('displays no data message if statistics are null and no error', async () => {
        ApiService.getStatistics.mockResolvedValue({ status: 200, data: null });
        wrapper = mount(DashboardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.no-data-message').exists()).toBe(true);
        expect(wrapper.find('.no-data-message p').text()).toBe('No statistics data available yet. Start reviewing some cards!');
        expect(wrapper.find('.statistics-grid').exists()).toBe(false);
        expect(wrapper.find('.error-message').exists()).toBe(false);
    });

    describe('formatScore method', () => {
        // Mount a temporary wrapper to access component methods
        beforeEach(() => {
            ApiService.getStatistics.mockResolvedValue({ status: 200, data: mockStatistics }); // Prevent mount error
            wrapper = mount(DashboardView);
        });

        it('formats score correctly to two decimal places', () => {
            expect(wrapper.vm.formatScore(0.85123)).toBe('0.85');
            expect(wrapper.vm.formatScore(0.7)).toBe('0.70');
            expect(wrapper.vm.formatScore(1)).toBe('1.00');
        });

        it('returns "N/A" for null or undefined score', () => {
            expect(wrapper.vm.formatScore(null)).toBe('N/A');
            expect(wrapper.vm.formatScore(undefined)).toBe('N/A');
        });
    });
}); 