# AI Krish: photo and camera analysis

## What it does
- Attach photos with the **+** button, drag and drop, or paste. Take a photo with **Take a photo** (webcam or phone camera, asks permission).
- Add an optional details line ("where, when, what to check"). Ask your question. AI Krish answers from the real pixels plus your details.
- **Think Harder** (header toggle) runs a deeper workflow: look carefully, answer from the observations, check the answer against the image, correct it if needed. It shows a short explanation, never private reasoning.
- If analysis fails, the chat says so. It never pretends a photo was analysed.

## How it works
- Browser: photos are shrunk (max 2000 px, JPEG) so they fit Vercel's ~4.5 MB request limit.
- `POST /api/analyze` (multipart): checks the passcode, rate limit and size, verifies each file by its real bytes, then streams progress lines and a final result.
- Images are held in memory for that one request only. Nothing is written to disk or stored.
- Images go **only** to vision-capable models: Gemini when `GEMINI_API_KEY` is set, or a provider where you set `<PROVIDER>_VISION_MODEL`. Text models (Groq/Cerebras gpt-oss) never receive images.

## Run locally (macOS Terminal)
```
cd ~/JarvisAI/jarvis-web
npm install
npm run dev
```
Open http://localhost:3000. The camera works on localhost and on https sites. It does not work on a plain http address like http://192.168.x.x:3000, so test phone cameras on your deployed https site.

## Check that your vision model really reads images
```
npm run check:vision
```
It sends a tiny red image to each configured vision provider and prints PASS or FAIL. No keys are printed.

## Tests and checks
```
npm test
npm run typecheck
npm run lint
npm run build
```
`npm run lint` already reported errors in `app/alerts/*` and 2 in `app/page.tsx` before this update. They are not caused by it.

## Deploy to Vercel
Your project is linked to Vercel from this Mac. Deploying updates the live site.
1. Make sure `APP_PASSCODE` and `GEMINI_API_KEY` exist in Production: `npx vercel env ls`
2. Optional vision model override: `npx vercel env add GEMINI_VISION_MODEL production`
3. Deploy: `npx vercel --prod`

Environment variables you add for Production are not available in Preview deployments.

## Troubleshooting
- "No vision-capable model is configured": add `GEMINI_API_KEY` on the server.
- "rate limit reached": the provider's free quota for that model is used up. Wait a minute, use Think Harder less (it makes 3 to 4 calls per photo), or set `GEMINI_VISION_MODELS` to a list of models so the next one is tried automatically. Run `npm run check:vision` to test every model in the list.
- 413 or "upload too large": use fewer or smaller photos (about 4 MB in total).
- 503 "APP_PASSCODE is not set": set `APP_PASSCODE` in Vercel and redeploy.
- Camera blocked: allow camera access for the site in the browser's settings.
