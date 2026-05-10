/**
 * Convert whisper.cpp's nested JSON output into a flat word-level array.
 *
 * Usage:
 *   node transcript_convert.mjs <whisper-output.json> [output.json]
 *
 * Defaults to overwriting the input file with the flat format.
 *
 * Whisper.cpp v1.8+ JSON shape:
 *   {
 *     "transcription": [
 *       { "tokens": [{ "text": "Hay", "offsets": { "from": 130, "to": 270 } }, ...] }
 *     ]
 *   }
 *
 * Output shape:
 *   [
 *     { "text": "Hay",  "start": 0.13, "end": 0.27 },
 *     { "text": "webs", "start": 0.27, "end": 0.58 },
 *     ...
 *   ]
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Usage: node transcript_convert.mjs <whisper-output.json> [output.json]");
  process.exit(1);
}

const inputPath = resolve(args[0]);
const outputPath = args[1] ? resolve(args[1]) : inputPath;

const raw = JSON.parse(readFileSync(inputPath, "utf-8"));

// If input is already in flat shape, exit gracefully.
if (Array.isArray(raw) && raw.length > 0 && typeof raw[0]?.start === "number") {
  console.log(`Input is already in flat shape (${raw.length} words). No conversion needed.`);
  process.exit(0);
}

if (!raw.transcription || !Array.isArray(raw.transcription)) {
  console.error(`Unexpected JSON shape — expected { transcription: [...] } from whisper.cpp`);
  console.error(`Got top-level keys: ${Object.keys(raw).join(", ")}`);
  process.exit(1);
}

const words = [];
for (const segment of raw.transcription) {
  // Shape A: word-level via -ml 1 -sow → segment.text is one word, offsets at segment level
  if (typeof segment.text === "string" && segment.offsets && typeof segment.offsets.from === "number") {
    const text = segment.text.trim();
    if (!text || text.startsWith("[")) continue;
    words.push({
      text,
      start: segment.offsets.from / 1000,
      end: segment.offsets.to / 1000,
    });
    continue;
  }
  // Shape B: token-nested (older whisper.cpp output style)
  if (segment.tokens && Array.isArray(segment.tokens)) {
    for (const tok of segment.tokens) {
      const text = (tok.text || "").trim();
      if (!text || text.startsWith("[")) continue;
      if (!tok.offsets || typeof tok.offsets.from !== "number") continue;
      words.push({
        text,
        start: tok.offsets.from / 1000,
        end: tok.offsets.to / 1000,
      });
    }
  }
}

if (words.length === 0) {
  console.error("No words extracted. Check the input file format.");
  process.exit(1);
}

writeFileSync(outputPath, JSON.stringify(words, null, 2));
console.log(`Wrote ${words.length} words to ${outputPath}`);
console.log(`Duration: ${words[words.length - 1].end.toFixed(2)}s`);
console.log(`Preview: "${words.slice(0, 6).map(w => w.text).join(" ")}..."`);
