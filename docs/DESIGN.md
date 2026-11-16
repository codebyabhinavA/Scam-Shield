# Scam Shield: Design Document

## Problem
People receive fraudulent SMS, WhatsApp, and email messages (fake KYC,
refund scams, fake job offers) and can't tell which are scams.

## Users
Ordinary people and non-technical family members.

## Core features (MVP)
- Sign up / log in
- Submit a suspicious message and get: risk level, red flags, next steps
- View and delete past checks
- Mark a check as "real scam" or "legit"

## Upgrades (only after MVP works)
- Voice dictation and read-aloud (browser Web Speech API)
- Link-check tool: the AI verifies URLs via a link-safety API

## Out of scope
Mobile app, auto-scanning SMS/WhatsApp, image analysis, payments,
admin dashboard, social features.

## Architecture
Browser (HTML/CSS/JS) -> FastAPI backend -> PostgreSQL (Neon)
                                         -> Gemini API (analysis)
                                         -> Link-safety API (upgrade)
The browser never talks to the database or AI directly.

## Data model (draft)
- users(id, email, password_hash, created_at)
- checks(id, user_id -> users, message_text, risk_level, summary,
         feedback, created_at)
- red_flags(id, check_id -> checks, type, explanation)

## API (draft)
POST /auth/signup | POST /auth/login
POST /checks | GET /checks | GET /checks/{id} | DELETE /checks/{id}
PATCH /checks/{id}/feedback

## Security rules
- Passwords hashed, never stored plain
- Every /checks route requires login and only touches the user's own rows
- API keys only in .env on the backend
- Personal data (phone numbers, OTPs) masked before text goes to the AI
- AI output validated before it is trusted or saved