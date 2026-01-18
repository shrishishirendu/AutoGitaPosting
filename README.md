# Gita Autoposter

Production-grade scaffold for an agentic workflow that assembles a daily Bhagavad Gita post with a generated image and caption.

## Architecture overview
- Orchestrator runs a deterministic agent pipeline in Milestone 2.
- Strict Pydantic contracts define all messages.
- SQLite persists runs, artifacts, drafts, and sequencing state.
- Verses are loaded from a vendored Bhagavad Gita dataset built into `data/gita/verses.json`.
- DRY_RUN prevents external posting and uses mock platform IDs.

## Agents
- SequenceAgent
- VerseFetchAgent
- CommentaryAgent
- ImagePromptAgent
- ImageGenerateAgent
- ImageComposeAgent
- PostPackagerAgent
- PosterAgent
- MonitorAgent

## Excel format
Provide a `.xlsx` file with headers `chapter_number` and `verse_number` (integers), in the exact order you want them posted. Configure the path with `SEQUENCE_XLSX_PATH` (default: `data/sequence/verses.xlsx`).

## Dataset
Vendored upstream data lives in `data/vendor/gita_gita/` with attribution and the upstream license. The app reads the canonical dataset from `data/gita/verses.json` (override with `GITA_DATASET_PATH`).

Build the canonical dataset with:
```bash
gita-autoposter build-dataset
```

Validate the sequence against the dataset:
```bash
gita-autoposter validate-dataset
```

License note: the upstream dataset is included under The Unlicense with attribution in `data/vendor/gita_gita/`.

## Images
Image prompts are stored with fingerprints for uniqueness. Raw and composed images are saved under `artifacts/images/`.
Use the preview helper:
```bash
gita-autoposter preview-image --chapter 1 --verse 1
```

List recent image prompts and hashes:
```bash
gita-autoposter list-images --last 5
```

If you need the Devanagari font, run:
```bash
python scripts/download_fonts.py
```

## Quickstart
Initialize the database:
```bash
gita-autoposter init-db
```

Load the verse sequence:
```bash
gita-autoposter load-sequence
```

Show upcoming and posted verses:
```bash
gita-autoposter show-sequence --limit 5
```

Run once (DRY_RUN by default):
```bash
gita-autoposter run-once
```

Show recent runs:
```bash
gita-autoposter status --limit 5
```

## Crash-safe sequencing
The Sequencer reserves a verse before any generation. If a run crashes after reserving,
the next run replays the same reserved verse without advancing the cursor. Only after
posting (even in DRY_RUN) does the system mark the verse as POSTED and move to the next.

## DRY_RUN
When `DRY_RUN=true`, the PosterAgent skips external APIs and returns mock platform IDs while still persisting drafts and artifacts.
