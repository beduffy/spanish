#!/bin/bash
# Quick test script for TokenStatus feature

set -e

echo "=== Testing TokenStatus Feature ==="
echo ""

cd anki_web_app

echo "1. Checking migration file exists..."
if [ -f "flashcards/migrations/0011_add_token_status.py" ]; then
    echo "   ✓ Migration file exists"
else
    echo "   ✗ Migration file missing!"
    exit 1
fi

echo ""
echo "2. Checking TokenStatus model is imported..."
if grep -q "TokenStatus" flashcards/models.py; then
    echo "   ✓ TokenStatus model found in models.py"
else
    echo "   ✗ TokenStatus model not found!"
    exit 1
fi

echo ""
echo "3. Checking TokenStatusAPIView exists..."
if grep -q "class TokenStatusAPIView" flashcards/views.py; then
    echo "   ✓ TokenStatusAPIView found"
else
    echo "   ✗ TokenStatusAPIView not found!"
    exit 1
fi

echo ""
echo "4. Checking URL pattern..."
if grep -q "token_status_api" flashcards/urls.py; then
    echo "   ✓ URL pattern registered"
else
    echo "   ✗ URL pattern missing!"
    exit 1
fi

echo ""
echo "5. Checking TokenSerializer includes status..."
if grep -q "status = serializers.SerializerMethodField" flashcards/serializers.py; then
    echo "   ✓ TokenSerializer has status field"
else
    echo "   ✗ TokenSerializer missing status field!"
    exit 1
fi

echo ""
echo "6. Checking tests exist..."
if grep -q "class TokenStatus" flashcards/tests_reader.py; then
    echo "   ✓ TokenStatus tests found"
else
    echo "   ✗ TokenStatus tests missing!"
    exit 1
fi

echo ""
echo "7. Checking frontend API service..."
if grep -q "updateTokenStatus" spanish_anki_frontend/src/services/ApiService.js; then
    echo "   ✓ Frontend API method exists"
else
    echo "   ✗ Frontend API method missing!"
    exit 1
fi

echo ""
echo "8. Checking frontend Vue component methods..."
if grep -q "markTokenAsKnown" spanish_anki_frontend/src/views/ReaderView.vue; then
    echo "   ✓ Frontend Vue methods exist"
else
    echo "   ✗ Frontend Vue methods missing!"
    exit 1
fi

echo ""
echo "=== All checks passed! ==="
echo ""
echo "To run tests:"
echo "  python manage.py test flashcards.tests_reader.TokenStatusModelTests"
echo "  python manage.py test flashcards.tests_reader.TokenStatusAPITests"
