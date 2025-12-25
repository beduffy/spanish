# Phase Status Report

## ✅ Phase 0: Stabilize dev workflow
**Status**: COMPLETE
- Docker Compose setup working
- Backend runs on :8000
- Frontend dev server runs on :8080
- Tests passing (64 backend, 37 frontend unit)

## ✅ Phase 1: Data model refactor: Sentence -> Card
**Status**: COMPLETE
- ✅ Card model created with front/back
- ✅ CardReview model with typed_input support
- ✅ pair_id and linked_card for bidirectional pairs
- ✅ SRS fields migrated to Card model
- ✅ Auto-creates reverse cards on creation
- ✅ Tests passing

## ✅ Phase 2: Supabase Auth integration
**Status**: COMPLETE (code ready, needs env vars for production)
- ✅ Frontend: LoginView.vue with Supabase client
- ✅ Backend: JWT verification backend + middleware
- ✅ User scoping: All views filter by authenticated user
- ✅ API interceptors: Auto-add auth tokens
- ⚠️ **Needs**: Set SUPABASE_URL, SUPABASE_JWT_SECRET env vars for production

## ✅ Phase 3: Import + CRUD UI
**Status**: COMPLETE
- ✅ ImportCardsView: CSV/TSV upload with preview + column mapping
- ✅ CardEditorView: Create and edit cards
- ✅ CardListView: List cards with pagination
- ✅ All API endpoints tested (64 tests passing)

## ✅ Phase 4: Review UX (including typing input)
**Status**: COMPLETE
- ✅ CardFlashcardView exists at `/cards/review`
- ✅ Shows front, reveals back
- ✅ Typed input box (saved with review)
- ✅ Score shortcuts [0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0]
- ✅ Comment field
- ✅ Submit & next functionality
- ✅ Uses CardNextCardAPIView and CardSubmitReviewAPIView
- ✅ Typed input stored in CardReview.typed_input

## ✅ Phase 5: KPIs + time tracking
**Status**: COMPLETE
- ✅ Basic statistics exist (CardStatisticsAPIView)
- ✅ Study session endpoints created:
  - `/api/flashcards/sessions/start/` - Start session endpoint
  - `/api/flashcards/sessions/heartbeat/` - Heartbeat/activity ping endpoint
  - `/api/flashcards/sessions/end/` - End session endpoint
- ✅ AFK threshold logic (90s default) implemented
- ✅ Active minutes calculation (`calculate_active_minutes()`)
- ✅ StudySession and SessionActivity models
- ✅ Models registered in admin

## ✅ Phase 6: Hetzner deployment
**Status**: COMPLETE
- ✅ Production docker-compose.prod.yml created with all services
- ✅ Nginx reverse proxy configuration with SSL/TLS support
- ✅ Certbot container for Let's Encrypt certificate management
- ✅ Production environment variables template (env.prod.example)
- ✅ Deployment documentation (DEPLOYMENT.md)
- ✅ Settings.py updated for production configuration
- ✅ Gunicorn added to requirements.txt
- ✅ Static files collection configured for production
- ✅ Auto-renewal of SSL certificates configured

## Next Steps

### Phase 7: Cleanup + rename
- Remove duplicate/legacy folders (there's an extra top-level `spanish_anki_frontend/`)
- Rename repo to `personal_anki_cards` (GitHub + local)

### Production Deployment:
1. Set up Supabase project and get credentials
2. Configure `.env.prod` with production values
3. Deploy to Hetzner server following DEPLOYMENT.md
4. Obtain Let's Encrypt certificates
5. Test production deployment end-to-end
