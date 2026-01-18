Project: Bhagavad Gita Agentic Auto Posting System

Goal:
Create an agentic workflow that posts the next Bhagavad Gita verse daily (incremental, no repetition) to Instagram and Facebook, with a newly generated image each time containing the Sanskrit verse in Devanagari.

MVP Requirements:
1) Incremental posting:
   - Each day posts the next verse from an Excel sequence.
   - No repetition guaranteed.
2) Input file:
   - An Excel file contains chapter_number and verse_number in the desired order.
3) Verse text:
   - Fetch the Sanskrit verse in Devanagari for the given chapter/verse.
4) Translation:
   - Provide English translation of the verse.
5) Commentary:
   - Write English commentary covering 3 aspects:
     - Social
     - Professional
     - Practical
6) Image prompt:
   - Generate an image prompt based on translation and/or commentary.
   - Ensure every post uses a new prompt/image (novelty required).
7) Image generation:
   - Generate a single image from the prompt using a pluggable image provider.
8) Verse on image:
   - Render the Sanskrit verse in Devanagari on top of the image (font-safe, readable).
9) Posting:
   - Post image + caption to Instagram and Facebook (Meta Graph API).
   - Support DRY_RUN mode that generates and stores outputs without posting.

Architecture:
- Agentic pipeline with strict message contracts.
- SQLite for state:
  - verse cursor/history
  - post drafts and statuses
  - artifact metadata (image hashes, prompts)
- Orchestrator runs agents in sequence with retries and logging.

MVP Agents:
- SequenceAgent (Excel -> next verse, no repetition)
- VerseFetchAgent (Sanskrit + English translation)
- CommentaryAgent (social/professional/practical)
- ImagePromptAgent (novel prompt)
- ImageGenerateAgent (image)
- ImageComposeAgent (Devanagari overlay)
- PostPackagerAgent (caption + image package)
- PosterAgent (FB/IG post; DRY_RUN supported)
- MonitorAgent (logging, retries, alerts)

Enhancements (Later):
- VoiceoverAgent (Sanskrit shloka TTS; optional voice cloning)
- VideoAgent (short video from translation/commentary)
- LinkedInToneAgent (tone adaptation)
- CarouselAgent (12–15 slides)
- LinkedInPosterAgent
- YouTubeShortsPosterAgent
