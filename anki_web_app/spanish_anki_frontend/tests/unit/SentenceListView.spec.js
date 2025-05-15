import { mount, RouterLinkStub } from '@vue/test-utils';
import SentenceListView from '@/views/SentenceListView.vue';
import ApiService from '@/services/ApiService';

jest.mock('@/services/ApiService');

describe('SentenceListView.vue', () => {
    let wrapper;
    const mockSentencesPage1 = {
        count: 2,
        total_pages: 1,
        results: [
            {
                sentence_id: 1,
                csv_number: 101,
                key_spanish_word: 'Hola',
                spanish_sentence_example: 'Hola Mundo',
                english_sentence_example: 'Hello World',
                is_learning: true,
                next_review_date: '2024-01-15T10:00:00Z',
            },
            {
                sentence_id: 2,
                csv_number: 102,
                key_spanish_word: 'Adiós',
                spanish_sentence_example: 'Adiós Amigo',
                english_sentence_example: 'Goodbye Friend',
                is_learning: false,
                next_review_date: '2024-02-20T12:30:00Z',
            },
        ],
    };

    const mockSentencesPage2 = {
        count: 2,
        total_pages: 1, // Assuming total 2 pages for pagination test
        results: [
            {
                sentence_id: 3, csv_number: 103, key_spanish_word: 'Gracias',
                spanish_sentence_example: 'Muchas gracias', english_sentence_example: 'Thank you very much',
                is_learning: true, next_review_date: '2024-03-10T08:00:00Z'
            }
        ]
    };

    // Helper to mount with stubs and initial props if needed
    const mountComponent = (apiMockImplementation) => {
        ApiService.getAllSentences.mockImplementation(apiMockImplementation);
        return mount(SentenceListView, {
            global: {
                stubs: {
                    RouterLink: RouterLinkStub, // Stub router-link for tests
                },
            },
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });


    it('renders loading message initially and fetches first page of sentences', async () => {
        wrapper = mountComponent(() => Promise.resolve({ status: 200, data: mockSentencesPage1 }));

        expect(wrapper.find('.loading-message').exists()).toBe(true);
        expect(wrapper.find('.loading-message p').text()).toBe('Loading sentences...');

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getAllSentences).toHaveBeenCalledWith(1);
        expect(wrapper.find('.loading-message').exists()).toBe(false);
        expect(wrapper.findAll('tbody tr').length).toBe(mockSentencesPage1.results.length);
    });


    it('displays sentences correctly in the table', async () => {
        wrapper = mountComponent(() => Promise.resolve({ status: 200, data: mockSentencesPage1 }));
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        const firstRowCells = wrapper.findAll('tbody tr').at(0).findAll('td');
        const firstSentence = mockSentencesPage1.results[0];

        expect(firstRowCells.at(0).text()).toBe(firstSentence.csv_number.toString());
        expect(firstRowCells.at(1).text()).toBe(firstSentence.key_spanish_word);
        expect(firstRowCells.at(2).text()).toBe(firstSentence.spanish_sentence_example);
        expect(firstRowCells.at(3).text()).toBe(firstSentence.english_sentence_example);
        expect(firstRowCells.at(4).text()).toBe(firstSentence.is_learning ? 'Learning' : 'Review');
        expect(firstRowCells.at(5).text()).toBe(wrapper.vm.formatDate(firstSentence.next_review_date));

        // Check router link
        const routerLink = firstRowCells.at(6).findComponent(RouterLinkStub);
        expect(routerLink.props().to).toEqual({ name: 'SentenceDetailView', params: { id: firstSentence.sentence_id } });
    });


    it('handles pagination: fetches next page when "Next" is clicked', async () => {
        const twoPageResponse = { ...mockSentencesPage1, total_pages: 2 };
        ApiService.getAllSentences
            .mockResolvedValueOnce({ status: 200, data: twoPageResponse })
            .mockResolvedValueOnce({ status: 200, data: { ...mockSentencesPage2, total_pages: 2, count: 3 } }); // Assuming 1 item on page 2

        wrapper = mount(SentenceListView, { global: { stubs: { RouterLink: RouterLinkStub } } });

        await new Promise(resolve => process.nextTick(resolve)); // Initial load page 1
        await wrapper.vm.$nextTick();

        expect(wrapper.vm.currentPage).toBe(1);
        expect(wrapper.vm.totalPages).toBe(2);
        expect(wrapper.findAll('tbody tr').length).toBe(mockSentencesPage1.results.length);

        const nextButton = wrapper.findAll('.pagination-controls button').filter(b => b.text() === 'Next').at(0);
        await nextButton.trigger('click');

        await new Promise(resolve => process.nextTick(resolve)); // Fetch page 2
        await wrapper.vm.$nextTick();
        await new Promise(resolve => process.nextTick(resolve)); // DOM update for page 2
        await wrapper.vm.$nextTick();

        expect(ApiService.getAllSentences).toHaveBeenCalledTimes(2);
        expect(ApiService.getAllSentences).toHaveBeenLastCalledWith(2);
        expect(wrapper.vm.currentPage).toBe(2);
        expect(wrapper.findAll('tbody tr').length).toBe(mockSentencesPage2.results.length);
        expect(wrapper.findAll('tbody tr').at(0).findAll('td').at(0).text()).toBe(mockSentencesPage2.results[0].csv_number.toString());
    });


    it('disables pagination buttons correctly', async () => {
        wrapper = mountComponent(() => Promise.resolve({ status: 200, data: mockSentencesPage1 })); // total_pages: 1
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        const prevButton = wrapper.findAll('.pagination-controls button').filter(b => b.text() === 'Previous').at(0);
        const nextButton = wrapper.findAll('.pagination-controls button').filter(b => b.text() === 'Next').at(0);

        expect(prevButton.attributes('disabled')).toBeDefined();
        expect(nextButton.attributes('disabled')).toBeDefined(); // Since totalPages is 1
    });


    it('displays error message if fetching sentences fails', async () => {
        ApiService.getAllSentences.mockRejectedValue(new Error('API Down'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        wrapper = mount(SentenceListView, { global: { stubs: { RouterLink: RouterLinkStub } } });

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toBe('Failed to load sentences. Please check your connection or try again later.');
        expect(consoleErrorSpy).toHaveBeenCalledWith('Error fetching sentences (page 1):', expect.any(Error));
        consoleErrorSpy.mockRestore();
    });


    it('displays no sentences message if API returns empty results', async () => {
        wrapper = mountComponent(() => Promise.resolve({ status: 200, data: { results: [], count: 0, total_pages: 0 } }));
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.no-data-message').exists()).toBe(true);
        expect(wrapper.find('.no-data-message p').text()).toBe('No sentences found in the database. Try importing your CSV.');
        expect(wrapper.findAll('tbody tr').length).toBe(0);
    });


    describe('formatDate method', () => {
        beforeEach(() => {
            wrapper = mountComponent(() => Promise.resolve({ status: 200, data: mockSentencesPage1 }));
        });

        it('formats date string correctly', () => {
            expect(wrapper.vm.formatDate('2024-01-15T10:00:00Z')).toBe('Jan 15, 2024');
            // This test is locale-dependent, if it fails, adjust expected output or make it more robust.
        });

        it('returns "N/A" for null or undefined date', () => {
            expect(wrapper.vm.formatDate(null)).toBe('N/A');
            expect(wrapper.vm.formatDate(undefined)).toBe('N/A');
        });
    });
}); 