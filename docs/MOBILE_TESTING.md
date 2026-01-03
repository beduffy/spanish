# Mobile Testing Guide

This document describes how to test the Reader feature on mobile devices, specifically focusing on touch-based phrase selection.

## Overview

The Reader feature supports touch-based phrase selection on mobile devices. Users can:
- **Tap** a single word to see its translation
- **Long-press and drag** to select multiple words and create a phrase

## Touch Selection Behavior

### Single Word Tap
- **Action**: Quick tap on a word
- **Behavior**: Shows translation popover (same as desktop click)
- **Timeout**: 200ms delay to distinguish from drag

### Multi-Word Selection
- **Action**: Long-press (200ms+) then drag across multiple words
- **Behavior**: 
  1. After 200ms, enters selection mode
  2. Visual selection appears as you drag
  3. On release, creates a phrase if 2+ words selected
  4. Shows phrase popover with translation

## Testing on Real Devices

### iOS (iPhone/iPad)

1. **Connect device** via USB
2. **Enable Web Inspector**:
   - Settings → Safari → Advanced → Web Inspector
3. **Open Safari on Mac**:
   - Develop → [Your Device] → [Your App]
4. **Test touch selection**:
   - Tap words to see translations
   - Long-press and drag to select phrases

### Android

1. **Enable USB Debugging**:
   - Settings → Developer Options → USB Debugging
2. **Connect device** via USB
3. **Open Chrome DevTools**:
   - `chrome://inspect` → Select your device
4. **Test touch selection**:
   - Tap words to see translations
   - Long-press and drag to select phrases

## Testing with Cypress

### Running Mobile Tests

```bash
# Run all mobile tests
cd anki_web_app/spanish_anki_frontend
npx cypress run --spec "cypress/e2e/reader_mobile.cy.js"

# Run in interactive mode
npx cypress open
# Then select reader_mobile.cy.js
```

### Test Coverage

The mobile test suite (`cypress/e2e/reader_mobile.cy.js`) includes:

1. **Multi-word phrase selection** - Tests touch drag selection across multiple tokens
2. **Single token tap** - Tests quick tap to show translation
3. **Scroll prevention** - Verifies selection doesn't cause unwanted scrolling
4. **Multiple viewports** - Tests on iPhone 12, Samsung Galaxy S20, iPad

### Viewports Tested

- iPhone 12 (390x844)
- iPhone 12 Pro (390x844)
- Samsung Galaxy S20 (360x800)
- iPad (768x1024)
- Samsung Galaxy Z Fold 5 Unfolded (1768x2208)

## Manual Testing Checklist

### Desktop/Laptop
- [ ] Click single word → translation popover appears
- [ ] Drag-select multiple words → phrase popover appears
- [ ] Selection works with mouse

### Mobile Device
- [ ] Tap single word → translation popover appears
- [ ] Long-press word (200ms+) → enters selection mode
- [ ] Drag across multiple words → visual selection appears
- [ ] Release → phrase popover appears
- [ ] Selection doesn't cause page scrolling
- [ ] Popover is positioned correctly on mobile screen
- [ ] Touch targets are large enough (min 44x44px)

### Tablet
- [ ] All mobile tests pass
- [ ] Selection works in both portrait and landscape
- [ ] Popover positioning adapts to orientation

## Known Issues & Limitations

1. **Text Selection API**: Some browsers have limited support for programmatic text selection
   - **Workaround**: Uses fallback methods when `document.caretRangeFromPoint` is unavailable

2. **Touch Event Timing**: Distinguishing tap vs drag requires timing
   - **Current**: 200ms delay before entering selection mode
   - **Trade-off**: Slight delay before selection starts

3. **Scroll Prevention**: `preventDefault()` on touchmove may interfere with native scrolling
   - **Current**: Only prevents scrolling when actively selecting
   - **Future**: Could add gesture detection to better distinguish selection from scroll

## Debugging Touch Events

### Enable Touch Event Logging

Add to `ReaderView.vue` methods:

```javascript
handleTouchStart(event) {
  console.log('Touch Start:', {
    touches: event.touches.length,
    clientX: event.touches[0]?.clientX,
    clientY: event.touches[0]?.clientY
  })
  // ... rest of method
}
```

### Chrome DevTools

1. Open DevTools (F12)
2. Go to **Console**
3. Enable **Touch emulation**:
   - Toggle device toolbar (Ctrl+Shift+M)
   - Select device preset
4. Monitor touch events in console

### Safari Web Inspector

1. Connect iOS device
2. Open Safari → Develop → [Device]
3. Use **Timeline** tab to see touch events
4. Use **Console** to see logs

## Performance Considerations

- **Touch Event Frequency**: Touch events fire frequently during drag
- **Optimization**: Debounce selection updates if needed
- **Memory**: Clear touch state on unmount to prevent leaks

## Future Improvements

1. **Gesture Recognition**: Use libraries like Hammer.js for better gesture detection
2. **Visual Feedback**: Add selection highlight during drag
3. **Accessibility**: Add ARIA labels for touch interactions
4. **Haptic Feedback**: Add vibration on phrase creation (mobile APIs)

## Related Documentation

- [LINGQ_READER_IMPLEMENTATION.md](./LINGQ_READER_IMPLEMENTATION.md) - Reader feature overview
- [LINGQ_READER_PLAN.md](./LINGQ_READER_PLAN.md) - Reader feature plan
- [agents.md](./agents.md) - Project overview
