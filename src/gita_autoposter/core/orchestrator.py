from __future__ import annotations

import json
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3

from gita_autoposter.agents.commentary_agent import CommentaryAgent
from gita_autoposter.agents.image_compose import ImageComposeAgent
from gita_autoposter.agents.image_generate import ImageGenerateAgent
from gita_autoposter.agents.image_prompt import ImagePromptAgent
from gita_autoposter.agents.monitor import MonitorAgent
from gita_autoposter.agents.post_packager import PostPackagerAgent
from gita_autoposter.agents.poster import PosterAgent
from gita_autoposter.agents.sequence import SequenceAgent
from gita_autoposter.agents.verse_fetch import VerseFetchAgent
from gita_autoposter.core.config import Config
from gita_autoposter.core.contracts import (
    ImageComposeInput,
    ImageArtifact,
    ImagePromptInput,
    PostPackageInput,
    RunReport,
    SequenceInput,
)
from gita_autoposter.core.visual_intent import resolve_visual_intent
from gita_autoposter.db import (
    add_artifact,
    add_draft,
    finish_run,
    init_db,
    insert_run,
    mark_verse_skipped,
    reserve_next_verse,
    update_draft_status,
    update_run_stage,
)
from gita_autoposter.dataset import VerseNotFoundError
from gita_autoposter.observability import setup_run_logger


@dataclass
class RunContext:
    config: Config
    run_id: str
    db: sqlite3.Connection
    artifact_dir: str
    run_dir: str | None = None
    logger: object | None = None
    skipped: list[dict] | None = None
    selection: dict | None = None


class Orchestrator:
    def __init__(self, config: Config, db_conn) -> None:
        self.config = config
        self.db_conn = db_conn

        self.sequence_agent = SequenceAgent()
        self.verse_fetch_agent = VerseFetchAgent()
        self.commentary_agent = CommentaryAgent()
        self.image_prompt_agent = ImagePromptAgent()
        self.image_generate_agent = ImageGenerateAgent()
        self.image_compose_agent = ImageComposeAgent()
        self.post_packager_agent = PostPackagerAgent()
        self.poster_agent = PosterAgent()
        self.monitor_agent = MonitorAgent()

    def run_once(
        self, run_id: str | None = None, post_now: bool = True, scheduled_time: str | None = None
    ) -> RunReport:
        init_db(self.db_conn)
        run_id = run_id or str(uuid.uuid4())
        started_at = datetime.utcnow()
        insert_run(self.db_conn, run_id, "running", started_at, stage="init")

        artifact_dir = Path(self.config.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        run_dir = artifact_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        logger = setup_run_logger(run_id, run_dir)
        ctx = RunContext(
            config=self.config,
            run_id=run_id,
            db=self.db_conn,
            artifact_dir=str(artifact_dir),
            run_dir=str(run_dir),
            logger=logger,
            skipped=[],
            selection=None,
        )
        report = RunReport(
            run_id=run_id,
            status="running",
            started_at=started_at,
            finished_at=None,
            error=None,
        )
        stage = "init"
        error_type: str | None = None
        error_trace: str | None = None

        try:
            stage = "sequence"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            sequence_input = SequenceInput(run_id=run_id)
            selection = self.sequence_agent.run(sequence_input, ctx)
            ctx.selection = {
                "chapter": selection.verse_ref.chapter,
                "verse": selection.verse_ref.verse,
            }
            logger.info(
                "selection",
                extra={
                    "stage": stage,
                    "chapter": selection.verse_ref.chapter,
                    "verse": selection.verse_ref.verse,
                },
            )

            stage = "fetch"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            verse_payload = self._fetch_with_skips(selection, ctx)

            stage = "commentary"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            commentary = self.commentary_agent.run(verse_payload, ctx)
            visual_intent = resolve_visual_intent(verse_payload, commentary)

            stage = "image_prompt"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            prompt_input = ImagePromptInput(
                verse_payload=verse_payload,
                commentary=commentary,
                visual_intent=visual_intent,
            )
            image_prompt = self.image_prompt_agent.run(prompt_input, ctx)
            add_artifact(
                self.db_conn,
                run_id,
                "prompt",
                path="",
                hash_value="",
                created_at=datetime.utcnow(),
                prompt_text=image_prompt.prompt_text,
                prompt_fingerprint=image_prompt.fingerprint,
            )

            stage = "image_generate"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            image_artifact = self.image_generate_agent.run(image_prompt, ctx)
            add_artifact(
                self.db_conn,
                run_id,
                "generated",
                image_artifact.path_raw,
                image_artifact.hash_raw,
                image_artifact.created_at,
                provider_name=image_artifact.provider_name,
                path_raw=image_artifact.path_raw,
                hash_raw=image_artifact.hash_raw,
            )
            report.artifacts.append(image_artifact)

            stage = "image_compose"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            compose_input = ImageComposeInput(verse_payload=verse_payload, image=image_artifact)
            composed_image = self.image_compose_agent.run(compose_input, ctx)
            add_artifact(
                self.db_conn,
                run_id,
                "composed",
                composed_image.path_composed,
                composed_image.hash_composed,
                composed_image.created_at,
                path_composed=composed_image.path_composed,
                hash_composed=composed_image.hash_composed,
                overlay_text=composed_image.overlay_text,
                font_name=composed_image.font_name,
            )
            report.artifacts.append(
                ImageArtifact(
                    run_id=run_id,
                    path_raw=composed_image.path_composed,
                    hash_raw=composed_image.hash_composed,
                    provider_name="composed",
                    created_at=composed_image.created_at,
                )
            )

            stage = "package"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            package_input = PostPackageInput(commentary=commentary, composed_image=composed_image)
            draft = self.post_packager_agent.run(package_input, ctx)
            add_draft(
                self.db_conn,
                run_id,
                draft.caption,
                draft.image_path,
                draft.status,
                draft.created_at,
                social_en=draft.social_en,
                professional_en=draft.professional_en,
                practical_en=draft.practical_en,
                caption_final_en=draft.caption_final_en,
                hashtags=" ".join(draft.hashtags or []),
                style_notes=draft.style_notes,
                fingerprint=draft.fingerprint,
                image_prompt_text=image_prompt.prompt_text,
                image_prompt_fingerprint=image_prompt.fingerprint,
                image_style_profile=image_prompt.style_profile,
                scheduled_time_sydney=scheduled_time,
            )

            caption_path = run_dir / "caption.txt"
            caption_path.write_text(draft.caption_final_en or draft.caption, encoding="utf-8")

            stage = "post"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_start", extra={"stage": stage})
            if post_now:
                result = self.poster_agent.run(draft, ctx)
                update_draft_status(self.db_conn, run_id, result.status)
            else:
                update_draft_status(self.db_conn, run_id, "scheduled")

            stage = "finish"
            update_run_stage(self.db_conn, run_id, stage)
            logger.info("stage_complete", extra={"stage": stage})
            report.status = "success"
            report.finished_at = datetime.utcnow()
            finish_run(self.db_conn, run_id, report.status, report.finished_at, None)
        except Exception as exc:  # noqa: BLE001 - intentional guardrail
            error_type = type(exc).__name__
            error_trace = traceback.format_exc()
            logger.error(
                "stage_failed",
                extra={"stage": stage, "error_type": error_type, "error": str(exc)},
            )
            report.status = "failed"
            report.finished_at = datetime.utcnow()
            report.error = str(exc)
            finish_run(self.db_conn, run_id, report.status, report.finished_at, report.error)
            raise
        finally:
            self._write_run_report(
                ctx,
                report,
                stage,
                error_type,
                error_trace,
            )

        return self.monitor_agent.run(report, ctx)

    def _fetch_with_skips(self, selection, ctx, max_skips: int = 10):
        attempts = 0
        current_selection = selection
        while True:
            try:
                if ctx.logger:
                    ctx.logger.info(
                        "fetch_attempt",
                        extra={
                            "stage": "fetch",
                            "chapter": current_selection.verse_ref.chapter,
                            "verse": current_selection.verse_ref.verse,
                        },
                    )
                payload = self.verse_fetch_agent.run(current_selection, ctx)
                ctx.selection = {
                    "chapter": current_selection.verse_ref.chapter,
                    "verse": current_selection.verse_ref.verse,
                }
                return payload
            except VerseNotFoundError as exc:
                attempts += 1
                chapter = current_selection.verse_ref.chapter
                verse = current_selection.verse_ref.verse
                ord_index = current_selection.ord_index
                message = f"Verse not found in dataset: {chapter}.{verse}"
                if ctx.skipped is not None:
                    ctx.skipped.append(
                        {
                            "chapter": chapter,
                            "verse": verse,
                            "ord_index": ord_index,
                            "reason": message,
                        }
                    )
                if ctx.logger:
                    ctx.logger.warning(
                        "verse_skipped",
                        extra={"stage": "fetch", "chapter": chapter, "verse": verse},
                    )
                print(f"Warning: Skipping verse {chapter}.{verse}: not found in dataset")
                mark_verse_skipped(ctx.db, ctx.run_id, chapter, verse, ord_index, message)
                if attempts >= max_skips:
                    raise RuntimeError(
                        f"No valid verses found in dataset after skipping {attempts} entries."
                    ) from exc
                next_chapter, next_verse, next_ord = reserve_next_verse(ctx.db, ctx.run_id)
                current_selection = current_selection.model_copy(
                    update={
                        "verse_ref": current_selection.verse_ref.model_copy(
                            update={"chapter": next_chapter, "verse": next_verse}
                        ),
                        "ord_index": next_ord,
                    }
                )

    def _write_run_report(
        self,
        ctx: RunContext,
        report: RunReport,
        stage: str,
        error_type: str | None,
        error_trace: str | None,
    ) -> None:
        if not ctx.run_dir:
            return
        run_dir = Path(ctx.run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "run_report.json"
        error = None
        if report.status == "failed":
            error = {
                "type": error_type or "Exception",
                "message": report.error,
                "traceback": error_trace,
            }
        report_payload = {
            "run_id": ctx.run_id,
            "status": report.status,
            "stage": stage,
            "started_at": report.started_at.isoformat() if report.started_at else None,
            "finished_at": report.finished_at.isoformat() if report.finished_at else None,
            "selection": ctx.selection,
            "skipped": ctx.skipped or [],
            "output_paths": {
                "caption": str(run_dir / "caption.txt") if (run_dir / "caption.txt").exists() else None,
                "image": None,
            },
            "posting_ids": {},
            "error": error,
        }
        if report.artifacts:
            last_image = report.artifacts[-1]
            report_payload["output_paths"]["image"] = last_image.path_raw

        if ctx.db:
            draft_row = ctx.db.execute(
                "SELECT image_path, facebook_post_id, instagram_post_id FROM drafts WHERE run_id = ?",
                (ctx.run_id,),
            ).fetchone()
            if draft_row:
                report_payload["output_paths"]["image"] = draft_row["image_path"]
                report_payload["posting_ids"] = {
                    "facebook": draft_row["facebook_post_id"],
                    "instagram": draft_row["instagram_post_id"],
                }

        report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
