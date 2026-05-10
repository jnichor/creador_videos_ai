# Voice Off Presets — ElevenLabs

Recommended voices and tone settings per language. Always preview 2-3 voices with the same script before committing — voice choice has more impact on perceived quality than any visual polish.

## Voice selection

| Language | Recommended voice | Tone |
|---|---|---|
| Spanish (LATAM) | **Mateo Aragon** | Conversational, persuasive-educational |
| Spanish (Spain) | **Bea** | Crisp, professional |
| English (US) | **Adam** | Deep, cinematic |
| English (UK) | **Dorothy** | Warm, narrator |
| Portuguese (BR) | **Antoni** | Friendly, approachable |
| French | **Charlotte** | Smooth, premium |
| German | **Klaus** | Professional, authoritative |
| Italian | **Giovanni** | Warm, conversational |

## Tone presets — settings per use case

| Use case | Style | Speed | Stability | Notes |
|---|---|---|---|---|
| Cinematic / luxury | 50–60 | 0.9 | 50 | More emotion, slower delivery |
| Educational / corporate | 30–40 | 0.95 | 60 | Steady, informative |
| Hype / launch | 60–80 | 1.0 | 35 | High energy, more inflection |
| News / journalistic | 20–30 | 1.0 | 70 | Neutral, no emotion swings |
| Conversational | 40 | 0.95 | 55 | Default for most marketing |

**Stability**: Don't go above 65 — voice gets robotic.
**Style**: Above 70, voice over-acts. Below 20, monotone.
**Speed**: 0.9 sounds "cinematic", 1.0 is neutral, 1.1+ rushes.
**Speaker Boost**: Always ON.

## Common gotchas

### 1. Numbers and dates

ElevenLabs reads `+51 999 888 777` as "fifty-one nine hundred ninety-nine..." Write phonetically:

- Spanish: `más cincuenta y uno, nueve nueve nueve, ocho ocho ocho, siete siete siete`
- English: `plus one, five five five, one two three, four five six seven`

Same for prices, times, addresses.

### 2. Brand names

Spell out tricky brands. Use TTS preview to test before downloading. If the engine mispronounces, try:
- Phonetic respelling: `Cau-sal A-I Digital`
- Adding a comma or pause: `Causal, AI, Digital.`
- Capitalizing differently: `causal ai digital`

### 3. Pauses and pacing

ElevenLabs respects:
- `...` (three dots) → slight pause
- Double line breaks (paragraph break) → longer pause
- Dashes `—` → mid-sentence beat

Use them for emotional emphasis. Marketing scripts benefit from a pause before the brand name reveal.

### 4. Punctuation tone

Stops at `.` are stronger than at `,`. Use this rhythm intentionally — short sentences = punchier delivery.

## Free tier limits

ElevenLabs free tier: ~10,000 characters/month. A 30-second script is ~250 chars. So you have room for ~40 video scripts/month before needing a paid plan.

If you hit the limit:
- **Coqui TTS** (open source, local) — good quality, more setup
- **Bark** (open source, local) — emotional but slower
- **Microsoft Edge TTS** (free, online) — passable quality, easy
