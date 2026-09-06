# CheckMyNotes — Project Summary

**Repo:** https://github.com/BiswasNehaa/CheckMyNotes
**Deployed app:** https://acadine-frontend.onrender.com

## What's Done
- Student login: enter a name, creates/reuses a student record (see assumption below).
- Upload handwritten notebook page images, tagged to a subject and date.
- Real AI checking via Groq's free-tier vision model, with retry-on-failure and a simulated fallback so the pipeline never gets stuck.
- Evaluation results are cached by image content — re-checking the exact same image returns the same result instead of calling the AI again (also saves the free tier's tight quota).
- View past remarks anytime, per subject and per day, with clickable mistake pins on the page image.
- Download as PDF: full merged notebook, a single day's pages, or a single page — each with pins drawn directly on the image plus the full written explanation, so the PDF is self-contained.

## What's Broken / Known Limitations
- No password-based auth — login is name-only, so anyone who enters the same name reuses that student's data (see assumption below).
- Groq's free tier allows only ~1000 output tokens/minute. Uploading several pages back-to-back can cause later pages in the same batch to fall back to the simulated evaluator instead of real AI — by design, so the app never breaks, but accuracy dips under bursty uploads.
- Only image uploads (JPG/PNG) are supported — no PDF-file upload.
- The image-hash evaluation cache isn't scoped per student, so two different students uploading byte-identical images would share a cached result (unlikely in practice, but worth noting).
- Deployed on Render's free tier: no persistent disk, so the SQLite database and uploaded images reset if the backend service restarts or redeploys.

## What's Next
- Time-permitting polish: scope the evaluation cache and evaluate endpoint to the logged-in student, add a database index on the image hash, and lower AI temperature further for even more consistent scoring.

## Assumptions Made
- **Login**: a lightweight "enter your name" identity step (creates/reuses a student record) instead of full username/password authentication — chosen for time constraints.
- **AI provider**: Groq's free-tier vision model, using a student-supplied API key read from a backend `.env` file (not committed). The recruiter's tech list mentioned LLaMA 3.3 70B, which is text-only on Groq — since this task requires reading handwritten images, a vision-capable Groq model was used instead.
- **Rate-limit handling**: retry with backoff, then fall back to a simulated evaluator and mark the result as such — so upload → check → view never gets stuck, per the brief's note that pipeline reliability matters more than raw accuracy.
