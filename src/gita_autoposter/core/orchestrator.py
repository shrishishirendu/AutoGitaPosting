from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3

from gita_autoposter.agents.commentary import CommentaryAgent
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
    PostPackageInput,
    RunReport,
    SequenceInput,
)
from gita_autoposter.db import (
    add_artifact,
    add_draft,
    finish_run,
    init_db,
    insert_run,
    update_draft_status,
)


@dataclass
class RunContext:
    config: Config
    run_id: str
    db: sqlite3.Connection
    artifact_dir: str


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

    def run_once(self, run_id: str | None = None) -> RunReport:
        init_db(self.db_conn)
        run_id = run_id or str(uuid.uuid4())
        started_at = datetime.utcnow()
        insert_run(self.db_conn, run_id, "running", started_at)

        artifact_dir = Path(self.config.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        ctx = RunContext(config=self.config, run_id=run_id, db=self.db_conn, artifact_dir=str(artifact_dir))
        report = RunReport(
            run_id=run_id,
            status="running",
            started_at=started_at,
            finished_at=None,
            error=None,
        )

        try:
            sequence_input = SequenceInput(run_id=run_id)
            verse_ref = self.sequence_agent.run(sequence_input, ctx)
            verse_payload = self.verse_fetch_agent.run(verse_ref, ctx)
            commentary = self.commentary_agent.run(verse_payload, ctx)
            image_prompt = self.image_prompt_agent.run(commentary, ctx)
            image_artifact = self.image_generate_agent.run(image_prompt, ctx)
            add_artifact(
                self.db_conn,
                run_id,
                "generated",
                image_artifact.path,
                image_artifact.hash,
                image_artifact.created_at,
            )
            report.artifacts.append(image_artifact)

            compose_input = ImageComposeInput(verse_payload=verse_payload, image=image_artifact)
            composed_image = self.image_compose_agent.run(compose_input, ctx)
            add_artifact(
                self.db_conn,
                run_id,
                "composed",
                composed_image.path,
                composed_image.hash,
                composed_image.created_at,
            )
            report.artifacts.append(
                ImageArtifact(
                    run_id=run_id,
                    path=composed_image.path,
                    hash=composed_image.hash,
                    created_at=composed_image.created_at,
                )
            )

            package_input = PostPackageInput(commentary=commentary, composed_image=composed_image)
            draft = self.post_packager_agent.run(package_input, ctx)
            add_draft(self.db_conn, run_id, draft.caption, draft.image_path, draft.status, draft.created_at)

            result = self.poster_agent.run(draft, ctx)
            update_draft_status(self.db_conn, run_id, result.status)

            report.status = "success"
            report.finished_at = datetime.utcnow()
            finish_run(self.db_conn, run_id, report.status, report.finished_at, None)
        except Exception as exc:  # noqa: BLE001 - intentional guardrail
            report.status = "failed"
            report.finished_at = datetime.utcnow()
            report.error = str(exc)
            finish_run(self.db_conn, run_id, report.status, report.finished_at, report.error)
            raise

        return self.monitor_agent.run(report, ctx)
