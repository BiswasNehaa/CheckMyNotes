# CheckMyNotes — Project Summary

**Repo:** https://github.com/BiswasNehaa/CheckMyNotes
**Deployed app:** https://acadine-frontend.onrender.com

## What's Done
- Student login: enter a name, creates/reuses a student record (see assumption below).
- Upload handwritten notebook page images, tagged to a subject and date.
- Real AI checking via Groq's free-tier vision model, with retry-on-failure; if AI checking still fails, the page is marked `failed` with a clear retry option instead of a fabricated grade.
- Evaluation results are cached by image content, per student — re-checking the exact same image returns the same result instead of calling the AI again (also saves the free tier's tight quota).
- View past remarks anytime, per subject and per day, with clickable mistake pins on the page image.
- Download as PDF: full merged notebook, a single day's pages, or a single page — each with pins drawn directly on the image plus the full written explanation, so the PDF is self-contained.

## What's Broken / Known Limitations
- No password-based auth — login is name-only, so anyone who enters the same name reuses that student's data (see assumption below).
- Groq's free tier allows only ~1000 output tokens/minute. Uploading several pages back-to-back can cause later pages in the same batch to hit the rate limit and come back `failed`, needing a manual retry from the Notebook view.
- Only image uploads (JPG/PNG) are supported — no PDF-file upload.
- No auth beyond a spoofable `X-Student-Id` header — anyone who knows or guesses a student ID can read/write their data.
- Deployed on Render's free tier: no persistent disk, so the SQLite database and uploaded images reset if the backend service restarts or redeploys ([tracked as an issue](https://github.com/BiswasNehaa/CheckMyNotes/issues/8)).

## What's Next
- Real authentication, and migrating off Render's ephemeral disk to a managed Postgres + object storage ([issue #8](https://github.com/BiswasNehaa/CheckMyNotes/issues/8)).

## Assumptions Made
- **Login**: a lightweight "enter your name" identity step (creates/reuses a student record) instead of full username/password authentication — chosen for time constraints.
- **AI provider**: Groq's free-tier vision model, using a student-supplied API key read from a backend `.env` file (not committed). The recruiter's tech list mentioned LLaMA 3.3 70B, which is text-only on Groq — since this task requires reading handwritten images, a vision-capable Groq model was used instead.
- **Rate-limit handling**: retry with backoff; if it still fails, the page is explicitly marked `failed` rather than substituted with a fabricated result — so a shown grade can always be trusted as real.
