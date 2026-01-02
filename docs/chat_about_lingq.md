
Du:
Does lingQ count minutes?
ChatGPT:

Nachgedacht für 35s
Yes — LingQ does track time, but it depends what you mean by “minutes.”

For your streak / daily goal: it’s not based on minutes. Your streak is based on hitting your daily LingQ-creation goal (number of new LingQs), not time spent. 
lingq-support.groovehq.com
+1

Time tracking: LingQ tracks Listening hours (time spent listening to lesson audio / playlists). 
lingq-support.groovehq.com

“Study time / time spent learning” stats: these exist, but can be inflated (e.g., if you leave a lesson open) and some users report it effectively counts time the reader is open. 
LingQ Language Forums
+1

Tip: for listening time specifically, some users report it may only reliably save when you exit the lesson (not just close the browser/app). 
LingQ Language Forums

Du:
Where can i see listening hours
ChatGPT:

Nachgedacht für 15s
You’ll find Listening hours in your Statistics.

On the web (desktop)
In the top header, click the small dropdown next to the coins + flame (streak) icons.

In that dropdown you’ll see a weekly stats summary (includes Listening hours).

Click “View all statistics” to open your Profile stats page for the full breakdown (timeframes + graphs). 
LingQ Language Forums
+1

On the mobile app (iOS / Android)
Go to the Library tab.

Tap the button in the top-right (Statistics snapshot).

Scroll down to see Listening hours. 
LingQ Language Forums

Du:
If i wanted to rebuild and vibe code and build all of lingq i could in one week. 
ChatGPT:

Nachgedacht für 29s
If by “build all of LingQ” you mean a feature-complete clone (importer + reader + word/phrase tracking + SRS review modes + stats + playlists + mobile apps + sync + payments + etc.), one week isn’t realistic for a solid, production-grade rebuild.

But if you mean “vibe-code a usable LingQ-style MVP that hits the core loop,” you can ship something surprisingly good in a week—as long as you ruthlessly scope to the essentials:

The “LingQ core loop” you’d want in your MVP
Import a lesson (text + optional audio) and open it in a reader. (LingQ also supports generating timestamps by comparing audio + text.) 
LingQ Language Forums

Click words/phrases → create a saved vocab item (“LingQ”) with a learning status level (1 New → 4 Learned). 
lingq-support.groovehq.com

Review those saved items (SRS-ish) and update status based on success. 
LingQ Language Forums
+1

Track stats like listening hours and streak/goal progress. 
lingq-support.groovehq.com
+1

Everything else (community hints, lots of import sources, polished mobile UX, courses marketplace, coins, etc.) is “week 2+”.

A realistic 7-day build plan (MVP)
Day 1 — Data model + auth

Users, languages

Lessons (text, optional audio URL)

Tokens (per-lesson tokenization)

LingQs (term, status 1–4, hint/translation, created_at)

Day 2 — Lesson import

Paste text / upload file

Optional audio upload

Store lesson, run tokenization

Day 3 — Reader UI (the magic)

Click-to-create LingQ on a token/selection

Highlight unknown/known based on status

Basic “next/prev page” or scrolling

Day 4 — Vocab list + status

Vocab page: filters by status, search

Status bar + quick change (1–4) 
lingq-support.groovehq.com

Day 5 — Review

Simple SRS queue (due items)

“Got it / missed it” updates status (even a simple rule is fine to start; LingQ’s status changes are tied to review performance). 
LingQ Language Forums
+1

Day 6 — Listening + stats

Audio player for lesson/playlist

Track listening hours for lesson audio playback 
lingq-support.groovehq.com

Basic streak tied to daily goal (you can mirror “daily goal/streak” mechanics conceptually) 
LingQ Language Forums
+1

Day 7 — Polish + deploy

Fast indexing/search

Import/export (CSV)

Deploy (Vercel/Fly/Render)

Stack that makes 1 week plausible
Next.js (reader UI + API routes)

Supabase (Auth + Postgres + Storage) or Firebase (if you prefer)

Meilisearch or Postgres full-text for vocab search

Background jobs only if you add fancy stuff (timestamps/alignment, embeddings, etc.)

Two big “gotchas”
Tokenization & languages: doing this well across languages is harder than it looks. For week-1, pick one language family (e.g., Spanish/French/German) or use a library per language.

Audio/text timestamps: LingQ can align audio+text into timestamps when importing 
LingQ Language Forums
 — replicating that robustly is non-trivial. For MVP: skip alignment or accept manually segmented sentences.

If you tell me which target language(s) you care about and whether you want web-only or web + mobile, I can give you a tighter scope + a concrete schema + the minimal reader interaction model that feels most “LingQ-like.”

Du:
Only german, and only two users. Web only
ChatGPT:

Nachgedacht für 14s
Perfect — German only + 2 users + web-only makes a 1-week “LingQ-core” rebuild very doable if you keep scope tight.

Here’s a concrete MVP that will feel like LingQ in the parts that matter (reader → click words/phrases → track learning → review → stats).

What you build (week-1 MVP scope)
1) Lesson import + reader
Paste German text (and optionally attach an audio file or URL)

Reader renders the text as clickable tokens

Clicking a token opens a popover:

create/update “LingQ” entry

set status 1–4 (New → Known)

optional hint/translation + note

2) Phrase LingQs (the “selection” vibe)
Drag to select multiple words → “Create phrase LingQ”

Store the phrase as a single entry

3) Vocab list
Search/filter by status

Sort by “recently seen/created”

4) Review
A simple spaced queue: “Due now”

Buttons: ✅ / ❌ → updates status + schedules next due

5) Listening hours
Audio player on lesson page

Track actual listening time (play time only, not “tab open” time)

6) Streak / daily goal (optional but quick)
Daily goal = “create X new LingQs”

Streak = consecutive days goal hit

Everything else (community hints, many import sources, courses, perfect lemmatization, fancy audio-text alignment) is out.

Stack that makes this fastest (and low-drama)
Next.js (App Router) + Prisma + SQLite

SQLite is totally fine for 2 users.

Deploy on a cheap VPS, Fly.io, Render, etc. (Vercel + SQLite is annoying unless you use Turso/Neon).

Auth for 2 users

Easiest: HTTP basic auth or a tiny “invite code” login.

Or NextAuth with credentials if you want a normal login page.

Database schema (minimal, works)
User

id, email, password_hash

Lesson

id, user_id

title

text

audio_url (nullable)

created_at

Lingq

id, user_id, language (“de” hardcoded)

term (string) — store exact surface form or phrase

norm (string) — lowercased + trimmed punctuation

status (int 1–4)

hint (nullable)

note (nullable)

created_at

updated_at

LingqOccurrence (optional but nice)

id, lingq_id, lesson_id

start_offset, end_offset (char offsets)

created_at

ReviewState

lingq_id (PK)

due_at (datetime)

interval_days (int)

ease (float optional)

ListeningSession

id, user_id, lesson_id

seconds (int)

created_at

Event (optional: powers streak/stats without extra tables)

id, user_id, type (“lingq_created”, “lingq_status_changed”, …)

ts

This schema is enough for the whole MVP.

German tokenization that’s “good enough” in a week
Use Intl.Segmenter (built into modern browsers) for German word segmentation.

It respects punctuation better than a naive regex.

You can preserve whitespace as separate segments so the text renders naturally.

Normalization rule for term matching

norm = lower(term)

strip leading/trailing punctuation like .,;:!?()[]„“"’…

keep umlauts ß as-is

Note on German reality: compounds + cases mean “lemma-perfect” vocab tracking is hard. For week-1, tracking surface forms is fine and still feels LingQ-ish.

Reader UX: how to make it feel right
In the reader:

Render each token as a <span> with:

dataset offsets (start/end)

CSS class based on status:

unknown (no Lingq) = highlighted

status 1–4 = progressively less highlighted

On click:

open popover

show term + existing hint/status

buttons: 1 2 3 4, “save hint”, “delete”

Phrase creation:

Let users select text

Convert selection to token range (by offsets)

Store phrase term + norm

In rendering, you can optionally highlight phrases by checking occurrences table; or skip phrase highlighting week-1 and just store them for review/list (still useful).

Review algorithm (simple, effective)
For each Lingq you want reviewed:

maintain due_at and interval_days

When user presses ✅:

if status < 4: status += 1

interval_days = {1:0, 2:1, 3:3, 4:7}[status]

due_at = now + interval_days

When user presses ❌:

status = max(1, status - 1)

interval_days = 0

due_at = now + 10 minutes (or “now”)

This is not Anki, but it’s enough to feel like progress.

Listening hours tracking (avoid the classic overcount)
In the lesson audio player:

on play: store playStart = performance.now()

on pause / ended / visibilitychange:

if currently playing: add (now - playStart) to accumulated

reset playStart

periodically (or on unload) POST accumulated seconds to server

This tracks real playback time, not tab time.

7-day build plan (with your constraints)
Day 1

Project setup (Next.js + Prisma + SQLite)

Minimal auth (2 users)

DB migrations

Day 2

Lesson create page (paste text, optional audio)

Lesson list page

Day 3

Reader tokenization + clickable tokens + popover

Create/update Lingq (status + hint)

Day 4

Vocab list page (search/filter/status)

“Seen in lessons” list (optional occurrences)

Day 5

Review page (due queue + ✅/❌ scheduling)

Day 6

Audio player + listening time tracking + stats page

Day 7

Streak/daily goal (optional)

Polish UX (keyboard shortcuts: space=play/pause, 1–4=status)

Deploy + backups

If you want the fastest path
Tell me which you prefer:

“Ship fastest”: SQLite + simple password login + deploy to one VPS

“More modern hosting”: Supabase Postgres + storage + auth

Either way, I can give you:

a ready Prisma schema

the exact tokenization/rendering approach (including offsets)

the popover + selection-to-phrase logic

the listening tracker snippet

If you pick (1) or (2), I’ll tailor the scaffolding to that choice.

Du:
How difficult to get translation popups right relative to that sentences context? How expensive?

Similar with audio generation. Any free cloud solutions? How much would elevenlabs cost for thousands of minutes or on demand or for 100 minutes? I could run on CPU of my hetzner server
ChatGPT:

Nachgedacht für 1m 22s
1) Context-aware translation popups (word/phrase in this sentence)
Difficulty: medium → hard, depending on what “right” means.

What’s easy (and feels good):

Sentence translation (one call per sentence, cached).

Token/phrase lookup with a dictionary-style gloss (lemma + 1–3 meanings).

Show both in the popup: (a) “this sentence means…” + (b) “this word usually means…”

What’s hard (what people really mean by “right”):

Picking the correct sense for a single word in context (polysemy), plus German-specific stuff:

separable verbs (“stellt … vor”),

case/declension changing surface forms,

compounds,

idioms and multiword expressions.

If you want the popup to say exactly “X means Y here” reliably, you typically need either:

Word alignment between German sentence and its translation (non-trivial to get robust), or

a contextual “gloss” model (LLM-style) that answers “translate this token/phrase as used here.”

Best pragmatic MVP approach (works great for 2 users):

On import (or first open), translate the whole sentence and cache it.

In the popup, show:

the sentence translation,

a short gloss for the selected token/phrase (cheap dictionary/lemma),

optionally a “More like this meaning” button that triggers a contextual gloss call only when needed.

Cost (translation):

DeepL API Free: up to 500,000 characters/month free. 
support.deepl.com

DeepL paid usage is commonly quoted as $25 per 1,000,000 characters (plus plan/base fees depending on plan). 
deepl.com
+1

For two users, if you translate only sentences you actually open + cache, it’s often surprisingly small.

2) Audio generation (TTS): how hard + what it costs
Difficulty:

Generating audio is easy.

Generating audio that’s pleasant, consistent across lessons, and supports German well is the real work (voice choice, speed, pronunciation quirks, caching, chunking long texts).

Free / low-cost cloud options (good enough for MVP)
Google Cloud Text-to-Speech free tier: 1M characters/month free for WaveNet and 4M characters/month free for Standard voices. 
Google Cloud
+1

Amazon Polly free tier (first 12 months): 5M characters/month for Standard voices (plus smaller free tiers for neural/other voice types). 
Amazon Web Services, Inc.
+1

Azure has always-free tiers for some services (Translator is 2M characters free tier, and Azure also lists free neural character amounts for speech in its free-services overview). 
Microsoft Azure

Rule of thumb to convert characters → minutes: ~900–1,100 characters per minute of speech (varies with speaking rate). So “millions of characters” can be tens of hours of audio per month.

ElevenLabs costs (100 minutes, thousands of minutes, on-demand)
ElevenLabs conveniently shows minutes included per plan:

From their pricing:

Starter: $5/mo, ~60 minutes 
ElevenLabs
+1

Creator: $11/mo, ~200 minutes, extra around ~$0.15/min 
ElevenLabs
+1

Pro: $99/mo, ~1,000 minutes, extra around ~$0.12/min 
ElevenLabs
+1

Scale: $330/mo, ~4,000 minutes, extra around ~$0.09/min 
ElevenLabs
+1

Business: $1,320/mo, ~22,000 minutes, extra around ~$0.06/min (and they also mention very low-latency TTS as low as ~5c/min). 
ElevenLabs
+1

So:

~100 minutes: the Creator ($11) tier covers it (and gives headroom). 
ElevenLabs

Thousands of minutes/month: Pro (~1,000) or Scale (~4,000) depending on volume. 
ElevenLabs

On-demand: it’s essentially “minutes included + per-minute overage,” and they also explain billing via credits/characters (model-dependent). 
ElevenLabs
+1

Running on your Hetzner CPU (no cloud)
Yes, you can run open-source TTS on CPU (e.g., lightweight engines like Piper-style setups), but tradeoffs:

Quality often below ElevenLabs/paid neural voices.

Speed can be slower than real time on CPU (model-dependent).

For 2 users, it’s totally viable if you:

generate once and cache audio per sentence/lesson,

keep concurrency low,

pre-generate audio overnight for new imports.

If you want the cleanest build for your LingQ-style MVP
Translation: DeepL API Free for sentence translations + cache. 
support.deepl.com

Popup “meaning”: dictionary/lemma first; add an “Explain in this sentence” button later.

Audio: start with Google TTS free tier (fast + simple), then swap to ElevenLabs only if you want premium voice. 
Google Cloud
+1

If you tell me roughly how much text/audio you expect per week (e.g., “~30k German words/week”), I’ll translate that into characters/month → expected monthly cost for (a) DeepL and (b) ElevenLabs, with a caching strategy that keeps it minimal.