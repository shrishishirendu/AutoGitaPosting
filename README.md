# Gita Autoposter

Production-grade scaffold for an agentic workflow that assembles a daily Bhagavad Gita post with a generated image and caption.

## Architecture overview
- Orchestrator runs a deterministic agent pipeline in Milestone 1.
- Strict Pydantic contracts define all messages.
- SQLite persists runs, artifacts, and drafts.
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

## Quickstart
Initialize the database:
```bash
gita-autoposter init-db
```

Run once (DRY_RUN by default):
```bash
gita-autoposter run-once
```

Show recent runs:
```bash
gita-autoposter status --limit 5
```

## DRY_RUN
When `DRY_RUN=true`, the PosterAgent skips external APIs and returns mock platform IDs while still persisting drafts and artifacts.
