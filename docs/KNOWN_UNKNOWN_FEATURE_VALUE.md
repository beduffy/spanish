# Known/Unknown Feature: Current Value & Future Potential

## What It Does Right Now

**Current Implementation:**
- ✅ Mark words as "known" (green highlight) or "unknown" (red highlight) while reading
- ✅ Status persists across sessions
- ✅ Visual feedback helps you see your comprehension level at a glance

**Current Value:**
- **Visual feedback**: Quick visual indicator of what you know vs don't know
- **Personal tracking**: Your vocabulary status is saved per word
- **Reading comprehension**: See at a glance which words you're struggling with

## The Problem: Limited Current Utility

Right now, this feature is **mostly cosmetic**. It's nice to have visual feedback, but it doesn't actively help you learn better. It's like having a highlighter but no way to use those highlights.

## What Would Make It Actually Useful

### 1. **Smart Flashcard Creation** (High Value)
Instead of manually clicking "Add to Flashcards" for every word:
- **Auto-create flashcards only for "unknown" words**
- Skip words you've marked as "known"
- Focus your study time on what you actually need to learn

**Example:**
```
You read a 500-word article
- 400 words marked as "known" → Skip these
- 100 words marked as "unknown" → Auto-create flashcards for these
Result: You study 100 cards instead of 500
```

### 2. **Lesson Difficulty Filtering** (Medium Value)
- Filter lessons by "% known words"
- Find lessons at your level (e.g., "Show me lessons where I know 60-80% of words")
- Avoid lessons that are too easy (95% known) or too hard (20% known)

### 3. **Vocabulary Statistics Dashboard** (Medium Value)
- Track vocabulary growth over time
- See: "You've learned 200 new words this month"
- Visualize progress: "You know 1,500 Spanish words"
- Motivation through numbers

### 4. **Personalized Learning Paths** (High Value)
- System suggests lessons based on your known vocabulary
- "You know these 50 words, here's a lesson that uses them"
- Gradually introduce new vocabulary in context

### 5. **Export & Analysis** (Low-Medium Value)
- Export "unknown words" list to study separately
- Generate vocabulary reports
- Share progress with teachers/tutors

## The LingQ Model

This feature is inspired by **LingQ**, where known/unknown status is central to their learning system:

1. **Reading**: Words you know are highlighted differently
2. **Learning**: System tracks your vocabulary size
3. **Content Discovery**: Shows lessons at your level
4. **Progress**: Visualizes vocabulary growth over time

## Recommendation

**If you want this feature to be useful, prioritize:**

1. **Auto-flashcard creation for unknown words** (biggest time saver)
2. **Lesson difficulty filtering** (helps find appropriate content)
3. **Vocabulary statistics** (motivation & tracking)

**If you don't plan to build these features:**
- The feature is nice-to-have but not essential
- Consider removing it to reduce complexity
- Or keep it simple as a visual aid

## Current Status

Right now, it's a **foundation** for future features. The data is being collected, but it's not being used to actively improve your learning experience yet.

**Bottom line**: It's useful if you build features on top of it. Otherwise, it's just a fancy highlighter.
