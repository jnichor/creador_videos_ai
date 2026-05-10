# whisper.cpp Install — All Platforms

whisper.cpp gives word-level timestamps that drive the burned-in subtitle CSS. This is the killer feature of the pipeline — without it, subtitles drift visibly against the voice.

## Why whisper.cpp (not openai-whisper)

| | whisper.cpp | openai-whisper (Python) |
|---|---|---|
| Install | Pre-built binary or `make` | `pip install` |
| Speed | Very fast (CPU optimized C++) | Slower (Python overhead) |
| Models | Small ~466 MB, accurate | Same models, slower load |
| Word timestamps | Native, reliable | Requires extra config |
| Cross-platform | Yes (Windows binary, source for Mac/Linux) | Yes |

For a 30-second voice off, whisper.cpp transcribes in ~5-15 seconds on a modern CPU.

## Windows — pre-built binary (recommended)

```powershell
# Download v1.8.4 BLAS x64 (CPU-optimized, broad compatibility)
curl -L -o whisper.zip "https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.4/whisper-blas-bin-x64.zip"

# Extract to C:\whisper
mkdir C:\whisper
# Use Windows Explorer or 7-Zip to extract whisper.zip → C:\whisper\

# Add to PATH (persistent for current user)
[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';C:\whisper', 'User')
```

Restart your terminal to pick up the PATH change. Verify:

```powershell
whisper-cli --help
```

If you have an NVIDIA GPU and want CUDA acceleration:
```powershell
curl -L -o whisper-cuda.zip "https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.4/whisper-cublas-12.4.0-bin-x64.zip"
```

## macOS — build from source

```bash
brew install cmake  # if not already installed
git clone --depth 1 https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
make

# Binary lives at ./build/bin/whisper-cli
# Add to PATH or symlink
sudo ln -s "$PWD/build/bin/whisper-cli" /usr/local/bin/whisper-cli
```

For Apple Silicon, Metal acceleration is on by default — no extra flags needed.

## Linux — build from source

```bash
sudo apt install build-essential cmake
git clone --depth 1 https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
make

sudo ln -s "$PWD/build/bin/whisper-cli" /usr/local/bin/whisper-cli
```

## Download a model

The pipeline uses `ggml-small.bin` (~466 MB) — the multilingual variant. Best balance of accuracy and speed for short marketing scripts.

```bash
mkdir -p models
curl -L -o models/ggml-small.bin \
  "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
```

## ⚠ Critical: never use `.en` models for non-English voice

`small.en`, `base.en`, etc. are English-ONLY models. They will *translate* Spanish/Portuguese/French audio into English text instead of transcribing it. Symptoms:
- Spanish "Hay webs" comes out as "Hello world"
- Subtitle text doesn't match what was actually said

Always use the model without the `.en` suffix:
- ✅ `ggml-small.bin`
- ❌ `ggml-small.en.bin`

## Transcribe a voiceover

```bash
whisper-cli \
  -m models/ggml-small.bin \
  -l es \
  -oj \
  -of transcript \
  voiceover.mp3
```

Flags:
- `-m` — path to model
- `-l <code>` — language code (`es`, `en`, `pt`, `fr`, `de`, `it`, ...)
- `-oj` — output JSON
- `-of transcript` — output filename prefix → `transcript.json`

Then convert nested whisper JSON to flat array:

```bash
node scripts/transcript_convert.mjs transcript.json
```

This overwrites `transcript.json` with the simple `[{text, start, end}]` shape the pipeline uses.

## Model size guide

| Model | Size | Accuracy | Speed (CPU) |
|---|---|---|---|
| tiny | 75 MB | OK for English | ~30s for 30s audio |
| base | 142 MB | Better | ~20s |
| **small** ← recommended | 466 MB | Great for marketing scripts | ~10s |
| medium | 1.5 GB | Higher | ~30s |
| large-v3 | 3 GB | Best | ~60s |

For a 30-second voice off, `small` is plenty. Move to `medium`/`large` only if you have technical jargon or unusual accents that `small` mishears.
