# PowerPoint Outline (12 Slides)

## Slide 1 - Title
- UNICEF Humanitarian Audio Intelligence using Foundation Models
- Name, course, date

## Slide 2 - Problem Statement
- Decision-makers need fast, understandable risk briefings
- Raw tables are hard to consume under time pressure

## Slide 3 - Why It Matters / Business Value
- Faster situational awareness
- Better communication for field teams
- Scalable daily or hourly spoken updates

## Slide 4 - Input Data
- Source CSVs from provided UNICEF outputs
- Summary metrics, regional risks, lead-time exposures

## Slide 5 - Models Used
- SpeechT5 for speech generation
- SpeechT5 HiFi-GAN vocoder
- Whisper Small for ASR-based evaluation

## Slide 6 - Pipeline Architecture
- CSV ingestion -> prompt generation -> TTS audio -> ASR transcription -> metrics
- Baseline vs improved comparison branch

## Slide 7 - Prompt/Input Engineering
- Baseline: short generic operational message
- Improved: structured domain-specific bulletin with percentile and horizon details

## Slide 8 - Evaluation Setup
- WER for transcription quality
- TTS latency
- Fact coverage score for summary usefulness

## Slide 9 - Results Table
- Show baseline vs improved metric values
- Highlight tradeoffs

## Slide 10 - Demo Link
- 1-2 minute demo: input, run, output audio, key findings
- Include QR code or URL

## Slide 11 - Limitations and Failure Cases
- No human MOS listening study yet
- Voice identity not domain tuned
- Potential numeric pronunciation errors in long numbers

## Slide 12 - AI Tools Disclosure + Next Steps
- Tools used: GitHub Copilot, Hugging Face, etc.
- What was AI-assisted vs manually verified
- Next: multilingual briefings and text-summary-to-voice chain
