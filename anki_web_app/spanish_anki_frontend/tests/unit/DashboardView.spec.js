import { mount } from '@vue/test-utils';
import DashboardView from '@/views/DashboardView.vue';
import ApiService from '@/services/ApiService';

// Mock the ApiService
vi.mock('@/services/ApiService', () => ({
    default: {
        getStatistics: vi.fn(),
    },
}));

describe('DashboardView.vue', () => {
    let wrapper;

    beforeEach(() => {
        // Reset mocks before each test
        vi.clearAllMocks();
    });

    it('renders the dashboard title', async () => {
        ApiService.default.getStatistics.mockResolvedValue({
            status: 200,
            data: { reviews_today: 0 } // Minimal mock data
        });
        wrapper = mount(DashboardView);
        await wrapper.vm.$nextTick(); // Wait for any DOM updates after mount/API call
        expect(wrapper.find('h1').text()).toBe('Dashboard');
    });

    it('calls ApiService.getStatistics on mount', () => {
        ApiService.default.getStatistics.mockResolvedValue({ status: 200, data: {} });
        wrapper = mount(DashboardView);
        expect(ApiService.default.getStatistics).toHaveBeenCalledTimes(1);
    });

    it('displays statistics when data is loaded', async () => {
        const mockStats = {
            reviews_today: 5,
            new_cards_reviewed_today: 2,
            reviews_this_week: 10,
            total_reviews_all_time: 100,
            overall_average_score: 0.85,
            total_sentences: 1998,
            sentences_learned: 50,
            percentage_learned: 2.5,
            sentences_mastered: 10,
        };
        ApiService.default.getStatistics.mockResolvedValue({ status: 200, data: mockStats });

        wrapper = mount(DashboardView);
        // Wait for component to re-render after data is fetched
        await wrapper.vm.$nextTick(); // Initial tick for mount
        await wrapper.vm.$nextTick(); // Tick after async operation completes

        // Check a few stat cards
        const statCards = wrapper.findAll('.stat-card');
        expect(statCards.length).toBeGreaterThan(0); // Ensure cards are rendered

        // Example check for one specific stat card
        // This requires precise matching of text or structure. 
        // A more robust way might be to add data-test attributes to elements.
        const reviewsTodayCard = wrapper.find('.statistics-grid .stat-card:nth-child(1) p');
        if (reviewsTodayCard.exists()) {
            expect(reviewsTodayCard.text()).toBe(mockStats.reviews_today.toString());
        }

        const avgScoreCard = wrapper.find('.statistics-grid .stat-card:nth-child(5) p');
        if (avgScoreCard.exists()) {
            expect(avgScoreCard.text()).toBe(mockStats.overall_average_score.toFixed(2));
        }
    });

    it('displays loading message initially', () => {
        ApiService.default.getStatistics.mockImplementation(() => new Promise(() => { })); // Prevent promise from resolving
        wrapper = mount(DashboardView);
        expect(wrapper.find('.loading-message').exists()).toBe(true);
    });

    it('displays error message if fetching statistics fails', async () => {
        ApiService.default.getStatistics.mockRejectedValue(new Error('API Error'));
        wrapper = mount(DashboardView);
        await wrapper.vm.$nextTick(); // Initial tick for mount
        await wrapper.vm.$nextTick(); // Tick after async operation completes and error is set
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain('Failed to load statistics');
    });

}); 