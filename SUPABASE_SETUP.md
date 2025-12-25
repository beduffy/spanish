# Supabase Setup Guide

## Phase 2: Supabase Authentication Integration

This project uses Supabase for authentication. Follow these steps to set up:

### 1. Create a Supabase Project

1. Go to https://app.supabase.com
2. Create a new project (or use an existing one)
3. Note your project URL and API keys

### 2. Get Your Supabase Credentials

From your Supabase project dashboard:

1. **Project URL**:
   - Go to **Settings** (gear icon in left sidebar)
   - Click **API** under "Project Settings"
   - Find **Project URL** (e.g., `https://xxxxx.supabase.co`)

2. **Anon Key**:
   - Same page: **Settings > API**
   - Under **Project API keys**, find the `anon` `public` key
   - Click the eye icon to reveal it, or click "Reveal" button

3. **JWT Secret** (for backend):
   - Go to **Settings > API**
   - Scroll down to **JWT Settings** section
   - Find **JWT Secret** field
   - Click the eye icon or "Reveal" button to show it
   - **Important**: This is a long string (usually starts with something like `your-super-secret-jwt-token-with-at-least-32-characters-long`)
   - **Note**: The JWT Secret is the same as the "JWT Secret" shown in the JWT Settings. It's used to verify tokens issued by Supabase.

### 3. Configure Environment Variables (Single .env File)

**Both backend and frontend use the same `.env` file at the project root!**

1. Copy `.env.example` to `.env` in the **project root** (`/home/ben/all_projects/spanish/`):
   ```bash
   cd /home/ben/all_projects/spanish
   cp .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_JWT_SECRET=your-jwt-secret-here
   SUPABASE_ANON_KEY=your-anon-key-here
   ```

3. **That's it!** Both Django and Vue.js will automatically read from this same file:
   - Django reads: `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_ANON_KEY`
   - Vue.js reads: Same variables (automatically mapped to `VUE_APP_SUPABASE_*`)

4. Restart both services for env changes to take effect:
   ```bash
   docker-compose restart
   ```

### 5. Run Database Migrations

After setting up Supabase, run migrations to add user fields to Card and Sentence models:

```bash
docker-compose run --rm backend python manage.py migrate
```

### 6. Create Test Users

You can create users via:
- Supabase Dashboard > Authentication > Users > Add User
- Or use the sign-up form in the frontend (`/login`)

### 7. Test Authentication

1. Start the app: `docker-compose up`
2. Navigate to `http://localhost:8080/login`
3. Sign up or sign in with a test account
4. Verify that cards/sentences are scoped to your user

## Notes

- **Single .env File**: Both Django backend and Vue.js frontend read from the same `.env` file at the project root (`/home/ben/all_projects/spanish/.env`). No need for multiple .env files!
- **Variable Names**: Use the same variable names (`SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_ANON_KEY`) in your `.env` file. Vue.js automatically maps them to `VUE_APP_*` format internally.
- **Backward Compatibility**: During migration, the system allows anonymous access (returns all cards) if no user is authenticated. Once all data is migrated, you can remove this fallback.
- **User Assignment**: New cards created via API or import are automatically assigned to the authenticated user.
- **JWT Verification**: The backend verifies Supabase JWT tokens on each request using the JWT secret.

## Finding the JWT Secret - Step by Step

1. Log into your Supabase project: https://app.supabase.com
2. Select your project from the dashboard
3. Click **Settings** (gear icon) in the left sidebar
4. Click **API** under "Project Settings"
5. Scroll down to the **JWT Settings** section
6. You'll see:
   - **JWT Secret**: This is what you need for the backend
   - **JWT URL**: Usually `https://your-project.supabase.co/.well-known/jwks.json`
7. Click the **eye icon** or **"Reveal"** button next to "JWT Secret" to show it
8. Copy the entire secret (it's a long string)

**Important Notes:**
- The JWT Secret is **not** the same as the anon key
- The JWT Secret is used by your backend to **verify** tokens that Supabase issues
- Keep it secret! Don't commit it to version control
- If you can't find it, make sure you have the right permissions (project owner/admin)

## Troubleshooting

- **401 Unauthorized**: 
  - Check that your Supabase credentials are correct
  - Verify the JWT secret matches what's in Supabase dashboard
  - Make sure you're using the **JWT Secret** (not the anon key) in backend settings
- **Can't find JWT Secret**: 
  - Make sure you're looking in **Settings > API > JWT Settings** (scroll down)
  - Check that you have project owner/admin permissions
  - Try refreshing the page
- **CORS Errors**: Ensure `CORS_ALLOWED_ORIGINS` in Django settings includes your frontend URL
- **Token Not Sent**: Check browser console for errors in `SupabaseService.js` or `ApiService.js`
