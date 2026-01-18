from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class VerseRef(BaseModel):
    chapter: int
    verse: int


class VersePayload(BaseModel):
    verse_ref: VerseRef
    sanskrit: str
    translation: str


class SequenceInput(BaseModel):
    run_id: str


class Commentary(BaseModel):
    verse_ref: VerseRef
    social: str
    professional: str
    practical: str
    caption: str


class ImagePrompt(BaseModel):
    verse_ref: VerseRef
    prompt: str
    uniqueness_signature: str


class ImageArtifact(BaseModel):
    run_id: str
    path: str
    hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImageComposeInput(BaseModel):
    verse_payload: VersePayload
    image: ImageArtifact


class ComposedImage(BaseModel):
    run_id: str
    path: str
    hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PostDraft(BaseModel):
    run_id: str
    caption: str
    image_path: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PostPackageInput(BaseModel):
    commentary: Commentary
    composed_image: ComposedImage


class PostResult(BaseModel):
    run_id: str
    platform_ids: Dict[str, str]
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunReport(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    error: Optional[str]
    artifacts: List[ImageArtifact] = Field(default_factory=list)
