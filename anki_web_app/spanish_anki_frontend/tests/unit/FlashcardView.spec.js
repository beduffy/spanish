import { mount } from '@vue/test-utils';
import FlashcardView from '@/views/FlashcardView.vue';
import ApiService from '@/services/ApiService';

jest.mock('@/services/ApiService');

describe('FlashcardView.vue', () => {
    let wrapper;
    const mockCard1 = {
        sentence_id: 1,
        key_spanish_word: 'Hola',
        spanish_sentence_example: 'Hola Mundo',
        key_word_english_translation: 'Hello',
        english_sentence_example: 'Hello World',
        base_comment: 'A greeting',
        ai_explanation: 'AI says hi',
        last_reviewed_date: null
    };
    const mockCard2 = {
        sentence_id: 2,
        key_spanish_word: 'Adiós',
        spanish_sentence_example: 'Adiós Amigo',
        key_word_english_translation: 'Goodbye',
        english_sentence_example: 'Goodbye Friend',
        base_comment: null,
        ai_explanation: null,
        last_reviewed_date: '2023-01-01T10:00:00Z'
    };

    beforeEach(() => {
        jest.clearAllMocks();
        ApiService.getNextCard = jest.fn();
        ApiService.submitReview = jest.fn();
    });

    it('renders loading message initially and fetches first card', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCard1 });
        wrapper = mount(FlashcardView);
        expect(wrapper.find('.loading-message').exists()).toBe(true);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(ApiService.getNextCard).toHaveBeenCalledTimes(1);
        expect(wrapper.find('.loading-message').exists()).toBe(false);
        expect(wrapper.find('.card-front h2').text()).toBe(mockCard1.key_spanish_word);
    });

    it('displays no cards message if API returns 204 on initial load', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 204, data: null });
        wrapper = mount(FlashcardView);

        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.all-done-message').exists()).toBe(true);
        expect(wrapper.find('.all-done-message p').text()).toContain('Congratulations! You\'ve reviewed all available cards for now!');
    });

    it('shows answer when "Show Answer" button is clicked', async () => {
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCard1 });
        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        expect(wrapper.find('.card-back').exists()).toBe(false);
        await wrapper.find('button.action-button').trigger('click'); // Show Answer button

        expect(wrapper.vm.showAnswer).toBe(true);
        expect(wrapper.find('.card-back').exists()).toBe(true);
        const paragraphs = wrapper.findAll('.card-back > p');
        expect(paragraphs.at(0).text()).toBe(`Key Word Translation: ${mockCard1.key_word_english_translation}`);
    });

    it('submits review and fetches next card', async () => {
        ApiService.getNextCard.mockResolvedValueOnce({ status: 200, data: mockCard1 })
            .mockResolvedValueOnce({ status: 200, data: mockCard2 });
        ApiService.submitReview.mockResolvedValue({ status: 200, data: {} }); // Mock successful submit

        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve)); // Initial load of mockCard1
        await wrapper.vm.$nextTick();

        await wrapper.find('button.action-button').trigger('click'); // Show Answer

        wrapper.vm.userScore = 0.9;
        wrapper.vm.userComment = 'Test comment';

        const submitButton = wrapper.findAll('button.action-button').find(b => b.text().includes('Submit & Next'));
        await submitButton.trigger('click');

        expect(ApiService.submitReview).toHaveBeenCalledWith(mockCard1.sentence_id, 0.9, 'Test comment');

        await new Promise(resolve => process.nextTick(resolve)); // submitReview promise
        await wrapper.vm.$nextTick();
        await new Promise(resolve => process.nextTick(resolve)); // fetchNextCard promise for mockCard2
        await wrapper.vm.$nextTick();

        expect(ApiService.getNextCard).toHaveBeenCalledTimes(2);
        expect(wrapper.find('.card-front h2').text()).toBe(mockCard2.key_spanish_word); // Check if new card is displayed
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
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCard1 });
        ApiService.submitReview.mockRejectedValue(new Error('Submit Error'));
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });

        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        await wrapper.find('button.action-button').trigger('click'); // Show Answer
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
        ApiService.getNextCard.mockResolvedValue({ status: 200, data: mockCard1 });
        wrapper = mount(FlashcardView);
        await new Promise(resolve => process.nextTick(resolve));
        await wrapper.vm.$nextTick();

        await wrapper.find('button.action-button').trigger('click'); // Show Answer

        wrapper.vm.userScore = 1.1; // Invalid score
        const submitButton = wrapper.findAll('button.action-button').find(b => b.text().includes('Submit & Next'));
        await submitButton.trigger('click');

        expect(ApiService.submitReview).not.toHaveBeenCalled();
        expect(wrapper.find('.error-message').exists()).toBe(true);
        expect(wrapper.find('.error-message p').text()).toContain('Please enter a score between 0.0 and 1.0');
    });

}); 