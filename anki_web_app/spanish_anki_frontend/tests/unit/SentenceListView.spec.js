import { mount, RouterLinkStub } from '@vue/test-utils';
import SentenceListView from '@/views/SentenceListView.vue';
import ApiService from '@/services/ApiService';

jest.mock('@/services/ApiService');

describe('SentenceListView.vue', () => {
    let wrapper;
    const mockSentencesPage1 = {
        count: 2, // Actually 2 S2E and 2 E2S = 4 total items if we consider directions
        total_pages: 1,
        results: [
            {
                sentence_id: 1,
                csv_number: 101,
                translation_direction: 'S2E',
                key_spanish_word: 'Hola',
                spanish_sentence_example: 'Hola Mundo',
                key_word_english_translation: 'Hello',
                english_sentence_example: 'Hello World',
                is_learning: true,
                next_review_date: '2024-01-15T10:00:00Z',
            },
            {
                sentence_id: 2,
                csv_number: 101, // Same CSV number, different direction
                translation_direction: 'E2S',
                key_spanish_word: 'Hola', // Spanish answer
                spanish_sentence_example: 'Hola Mundo', // Spanish answer sentence
                key_word_english_translation: 'Hello', // English prompt
                english_sentence_example: 'Hello World', // English prompt sentence
                is_learning: false,
                next_review_date: '2024-02-20T12:30:00Z',
            },
        ],
    };

    const mockSentencesPage2 = { // This mock might need more items for a robust pagination test
        count: 2, // if count refers to unique concepts, or 4 if total items
        total_pages: 1,
        results: [
            {
                sentence_id: 3, csv_number: 103, translation_direction: 'S2E',
                key_spanish_word: 'Gracias', spanish_sentence_example: 'Muchas gracias',
                key_word_english_translation: 'Thank you', english_sentence_example: 'Thank you very much',
                is_learning: true, next_review_date: '2024-03-10T08:00:00Z'
            },
            {
                sentence_id: 4, csv_number: 103, translation_direction: 'E2S',
                key_spanish_word: 'Gracias', key_word_english_translation: 'Thank you',
                spanish_sentence_example: 'Muchas gracias', english_sentence_example: 'Thank you very much',
                is_learning: false, next_review_date: '2024-03-15T09:00:00Z'
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

        const rows = wrapper.findAll('tbody tr');
        expect(rows.length).toBe(mockSentencesPage1.results.length);

        // Test S2E row (first row)
        const firstRowCells = rows.at(0).findAll('td');
        const firstSentence = mockSentencesPage1.results[0]; // S2E

        expect(firstRowCells.at(0).text()).toBe(firstSentence.csv_number.toString());
        expect(firstRowCells.at(1).find('span').text()).toBe('S2E');
        expect(firstRowCells.at(1).find('span').classes()).toContain('badge-s2e');
        expect(firstRowCells.at(2).text()).toBe(firstSentence.key_spanish_word); // Prompt Key Word for S2E
        expect(firstRowCells.at(3).text()).toBe(firstSentence.spanish_sentence_example); // Prompt Sentence for S2E
        expect(firstRowCells.at(4).text()).toBe(firstSentence.english_sentence_example); // Answer Sentence for S2E
        expect(firstRowCells.at(5).text()).toBe(firstSentence.is_learning ? 'Learning' : 'Review');
        expect(firstRowCells.at(6).text()).toBe(wrapper.vm.formatDate(firstSentence.next_review_date));

        const routerLink1 = firstRowCells.at(7).findComponent(RouterLinkStub);
        expect(routerLink1.props().to).toEqual({ name: 'SentenceDetailView', params: { id: firstSentence.sentence_id } });

        // Test E2S row (second row)
        const secondRowCells = rows.at(1).findAll('td');
        const secondSentence = mockSentencesPage1.results[1]; // E2S

        expect(secondRowCells.at(0).text()).toBe(secondSentence.csv_number.toString());
        expect(secondRowCells.at(1).find('span').text()).toBe('E2S');
        expect(secondRowCells.at(1).find('span').classes()).toContain('badge-e2s');
        expect(secondRowCells.at(2).text()).toBe(secondSentence.key_word_english_translation); // Prompt Key Word for E2S
        expect(secondRowCells.at(3).text()).toBe(secondSentence.english_sentence_example); // Prompt Sentence for E2S
        expect(secondRowCells.at(4).text()).toBe(secondSentence.spanish_sentence_example); // Answer Sentence for E2S
        expect(secondRowCells.at(5).text()).toBe(secondSentence.is_learning ? 'Learning' : 'Review');
        expect(secondRowCells.at(6).text()).toBe(wrapper.vm.formatDate(secondSentence.next_review_date));

        const routerLink2 = secondRowCells.at(7).findComponent(RouterLinkStub);
        expect(routerLink2.props().to).toEqual({ name: 'SentenceDetailView', params: { id: secondSentence.sentence_id } });
    });


    it('handles pagination: fetches next page when "Next" is clicked', async () => {
        // Adjust mock data to have a clear distinction for pagination
        const page1Data = {
            count: 4, // Total items across all pages
            total_pages: 2,
            results: [
                { sentence_id: 1, csv_number: 101, translation_direction: 'S2E', key_spanish_word: 'S2E_1', spanish_sentence_example: 'Spanish S2E_1', key_word_english_translation: 'English S2E_1', english_sentence_example: 'English S2E_1' },
                { sentence_id: 2, csv_number: 101, translation_direction: 'E2S', key_word_english_translation: 'E2S_1_Prompt', english_sentence_example: 'English E2S_1_Prompt', key_spanish_word: 'Spanish E2S_1_Ans', spanish_sentence_example: 'Spanish E2S_1_Ans' }
            ]
        };
        const page2Data = {
            count: 4,
            total_pages: 2,
            results: [
                { sentence_id: 3, csv_number: 102, translation_direction: 'S2E', key_spanish_word: 'S2E_2', spanish_sentence_example: 'Spanish S2E_2', key_word_english_translation: 'English S2E_2', english_sentence_example: 'English S2E_2' },
                { sentence_id: 4, csv_number: 102, translation_direction: 'E2S', key_word_english_translation: 'E2S_2_Prompt', english_sentence_example: 'English E2S_2_Prompt', key_spanish_word: 'Spanish E2S_2_Ans', spanish_sentence_example: 'Spanish E2S_2_Ans' }
            ]
        };

        ApiService.getAllSentences
            .mockResolvedValueOnce({ status: 200, data: page1Data })
            .mockResolvedValueOnce({ status: 200, data: page2Data });

        wrapper = mount(SentenceListView, { global: { stubs: { RouterLink: RouterLinkStub } } });

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.vm.currentPage).toBe(1);
        expect(wrapper.vm.totalPages).toBe(2);
        expect(wrapper.findAll('tbody tr').length).toBe(page1Data.results.length);

        const nextButton = wrapper.findAll('.pagination-controls button').filter(b => b.text() === 'Next').at(0);
        await nextButton.trigger('click');

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getAllSentences).toHaveBeenCalledTimes(2);
        expect(ApiService.getAllSentences).toHaveBeenLastCalledWith(2);
        expect(wrapper.vm.currentPage).toBe(2);
        expect(wrapper.findAll('tbody tr').length).toBe(page2Data.results.length);
        // Check content of the first row on page 2
        const firstRowPage2Cells = wrapper.findAll('tbody tr').at(0).findAll('td');
        const firstSentencePage2 = page2Data.results[0];
        expect(firstRowPage2Cells.at(0).text()).toBe(firstSentencePage2.csv_number.toString());
        expect(firstRowPage2Cells.at(2).text()).toBe(firstSentencePage2.key_spanish_word); // S2E prompt
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