from flashcards.models import Sentence
from django.utils import timezone

print(f"Total sentences in DB: {Sentence.objects.count()}")
today = timezone.now().date()
print(f"Today's date (according to Django): {today}")

new_available_cards = Sentence.objects.filter(
    next_review_date__lte=today,
    is_learning=True
).order_by('next_review_date', 'csv_number')

print(f"Number of new/learning cards due today or earlier: {new_available_cards.count()}")

if new_available_cards.exists():
    first_card = new_available_cards.first()
    print(f"First available new/learning card: CSV {first_card.csv_number}, Next Review: {first_card.next_review_date}, Is Learning: {first_card.is_learning}, Interval: {first_card.interval_days}")
else:
    print("No new/learning cards seem to be available based on the criteria in NextCardAPIView.")

# Also check for review cards just in case
review_available_cards = Sentence.objects.filter(
    next_review_date__lte=today,
    is_learning=False
).order_by('next_review_date', 'csv_number')
print(f"Number of review cards due today or earlier: {review_available_cards.count()}")
if review_available_cards.exists():
    first_review_card = review_available_cards.first()
    print(f"First available review card: CSV {first_review_card.csv_number}, Next Review: {first_review_card.next_review_date}, Is Learning: {first_review_card.is_learning}, Interval: {first_review_card.interval_days}")

print("\n-- Checking a few sample sentences explicitly --")
# Check first 5 sentences by csv_number to see their state
for i in range(1, 6):
    try:
        s = Sentence.objects.get(csv_number=i)
        print(f"CSV {s.csv_number}: Next Review={s.next_review_date}, Learning={s.is_learning}, Interval={s.interval_days}")
    except Sentence.DoesNotExist:
        print(f"Sentence with CSV number {i} not found.")