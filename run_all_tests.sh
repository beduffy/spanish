#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Starting all tests..."

# Navigate to the workspace root, assuming the script is run from there.
# If not, this needs adjustment or the script should be placed in the root.
# For now, we assume it's in /home/ben/all_projects/spanish/ and paths are relative to that.

echo ""
echo "------------------------------------"
echo " Phase 1: Backend Django tests      "
echo "------------------------------------"
echo "Running backend Django tests from anki_web_app/..."
(cd anki_web_app && python manage.py test)
echo "Backend Django tests completed."

echo ""
echo "----------------------------------------"
echo " Phase 2: Frontend Unit tests (Jest)  "
echo "----------------------------------------"
echo "Running frontend unit tests (Jest) from anki_web_app/spanish_anki_frontend/..."
(cd anki_web_app/spanish_anki_frontend && npm run test:unit)
echo "Frontend unit tests completed."

echo ""
echo "-----------------------------------------"
echo " Phase 3: Frontend E2E tests (Cypress) "
echo "-----------------------------------------"
echo "Running frontend E2E tests (Cypress) from anki_web_app/spanish_anki_frontend/..."
(cd anki_web_app/spanish_anki_frontend && npx cypress run)
echo "Frontend E2E tests completed."

echo ""
echo "------------------------------------"
echo " All test suites executed.          "
echo "------------------------------------" 