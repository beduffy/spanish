import { mount } from '@vue/test-utils';
import FlashcardView from '@/views/FlashcardView.vue';
import ApiService from '@/services/ApiService';

jest.mock('@/services/ApiService');

describe('FlashcardView.vue', () => {
    let wrapper;
    const mockCardS2E = {
        sentence_id: 1,
        key_spanish_word: 'Hola',
        spanish_sentence_example: 'Hola Mundo',
        key_word_english_translation: 'Hello',
        english_sentence_example: 'Hello World',
        base_comment: 'A greeting',
        ai_explanation: 'AI says hi',
        last_reviewed_date: null,
        translation_direction: 'S2E',
        csv_number: 101
    };
    const mockCardE2S = {
        sentence_id: 2,
        key_spanish_word: 'Adiós',
        spanish_sentence_example: 'Adiós Amigo',
        key_word_english_translation: 'Goodbye',
        english_sentence_example: 'Goodbye Friend',
        base_comment: null,
        ai_explanation: null,
        last_reviewed_date: '2023-01-01T10:00:00Z',
        translation_direction: 'E2S',
        csv_number: 102
    };

    beforeEach(() => {
        jest.clearAllMocks();
        ApiService.getNextCard = jest.fn();
        ApiService.submitReview = jest.fn();
    });

    it('renders loading message initially and fetches first S2E card', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCardS2E });
        wrapper = mount(FlashcardView);
        expect(wrapper.find('.loading-message').exists()).toBe(true);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getNextCard).toHaveBeenCalledTimes(1);
        expect(wrapper.find('.loading-message').exists()).toBe(false);
        expect(wrapper.find('.card-front h2').text()).toBe(mockCardS2E.key_spanish_word);
        expect(wrapper.find('.sentence-display').text()).toBe(mockCardS2E.spanish_sentence_example);
        expect(wrapper.find('.card-type-badge').text()).toBe('Spanish to English');
        expect(wrapper.find('.card-csv-number').text()).toBe(`#${mockCardS2E.csv_number}`);
    });

    it('displays no cards message if API returns 204 on initial load', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 204, data: null });
        wrapper = mount(FlashcardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.all-done-message').exists()).toBe(true);
        expect(wrapper.find('.all-done-message p').text()).toContain('Congratulations! You\'ve reviewed all available cards for now!');
    });

    it('shows answer for S2E card when "Show Answer" button is clicked', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCardS2E });
        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.card-back').exists()).toBe(false);
        await wrapper.find('button.action-button').trigger('click');

        expect(wrapper.vm.showAnswer).toBe(true);
        expect(wrapper.find('.card-back').exists()).toBe(true);
        const paragraphs = wrapper.findAll('.card-back > p');
        expect(paragraphs.at(0).text()).toBe(`Key Word Translation: ${mockCardS2E.key_word_english_translation}`);
        expect(paragraphs.at(1).text()).toBe(`Sentence Translation: ${mockCardS2E.english_sentence_example}`);
    });

    it('submits review and fetches next card (E2S)', async () => {
        ApiService.getNextCard.mockResolvedValueOnce({ status: 200, data: mockCardS2E })
            .mockResolvedValueOnce({ status: 200, data: mockCardE2S });
        ApiService.submitReview.mockResolvedValue({ status: 200, data: {} });

        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        await wrapper.find('button.action-button').trigger('click');

        wrapper.vm.userScore = 0.9;
        wrapper.vm.userComment = 'Test comment S2E';

        const submitButton = wrapper.findAll('button.action-button').find(b => b.text().includes('Submit & Next'));
        await submitButton.trigger('click');

        expect(ApiService.submitReview).toHaveBeenCalledWith(mockCardS2E.sentence_id, 0.9, 'Test comment S2E');

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getNextCard).toHaveBeenCalledTimes(2);
        expect(wrapper.find('.card-front h2').text()).toBe(mockCardE2S.key_word_english_translation);
        expect(wrapper.find('.sentence-display').text()).toBe(mockCardE2S.english_sentence_example);
        expect(wrapper.find('.card-type-badge').text()).toBe('English to Spanish');
        expect(wrapper.find('.card-csv-number').text()).toBe(`#${mockCardE2S.csv_number}`);
    });

    it('displays error message if fetching next card fails', async () => {
        ApiService.getNextCard.mockRejectedValue(new Error('Fetch Error'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        wrapper = mount(FlashcardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain('Failed to load the next card');
        consoleErrorSpy.mockRestore();
    });

    it('displays error message if submitting review fails', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCardS2E });
        ApiService.submitReview.mockRejectedValue(new Error('Submit Error'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });

        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        await wrapper.find('button.action-button').trigger('click');
        wrapper.vm.userScore = 0.8;
        const submitButton = wrapper.findAll('button.action-button').find(b => b.text().includes('Submit & Next'));
        await submitButton.trigger('click');

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain('Failed to submit your review');
        consoleErrorSpy.mockRestore();
    });

    it('validates score before submitting', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCardS2E });
        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        await wrapper.find('button.action-button').trigger('click');

        wrapper.vm.userScore = 1.1;
        const submitButton = wrapper.findAll('button.action-button').find(b => b.text().includes('Submit & Next'));
        await submitButton.trigger('click');

        expect(ApiService.submitReview).not.toHaveBeenCalled();
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain('Please enter a score between 0.0 and 1.0');
    });

    it('correctly displays prompt and answer for an E2S card', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCardE2S });
        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        // Check front of E2S card (should be English)
        expect(wrapper.find('.card-front h2').text()).toBe(mockCardE2S.key_word_english_translation);
        expect(wrapper.find('.sentence-display').text()).toBe(mockCardE2S.english_sentence_example);
        expect(wrapper.find('.card-type-badge').text()).toBe('English to Spanish');
        expect(wrapper.find('.card-csv-number').text()).toBe(`#${mockCardE2S.csv_number}`);

        // Show answer
        await wrapper.find('button.action-button').trigger('click');

        // Check back of E2S card (should be Spanish)
        const paragraphs = wrapper.findAll('.card-back > p');
        expect(paragraphs.at(0).text()).toBe(`Key Word Translation: ${mockCardE2S.key_spanish_word}`);
        expect(paragraphs.at(1).text()).toBe(`Sentence Translation: ${mockCardE2S.spanish_sentence_example}`);
    });

}); 