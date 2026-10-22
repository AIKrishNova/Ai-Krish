# AI Krish assistant

A small personal assistant you run in Terminal.

## Start it

Typed commands only:

    cd ~/Desktop/Ai-Krish && python3 -m assistant

With voice (listen command):

    cd ~/Desktop/Ai-Krish && ~/.ai-krish/venv/bin/python -m assistant

## What it can do

Type `help` inside the assistant for the full list: notes, clipboard,
opening approved apps/websites/folders, spoken replies (`speak on`),
and push-to-talk (`listen`).

## Voice notes

- Nothing is recorded unless you type `listen`. One command = one recording.
- Speech is turned into text on this Mac. Audio is not sent anywhere.
- Default speech model is base.en (about 150 MB, downloaded once).
  To try another: AIKRISH_WHISPER_MODEL=tiny.en before the start command.
- The voice libraries live in ~/.ai-krish/venv, outside the repo.

## Tests

    cd ~/Desktop/Ai-Krish && python3 -m unittest discover -s tests -t .
