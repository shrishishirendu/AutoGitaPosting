from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class VerseRef(BaseModel):
    chapter: int
    verse: int


class VersePayload(BaseModel):
    verse_ref: VerseRef
    ord_index: Optional[int] = None
    sanskrit: str
    translation: str


class SequenceInput(BaseModel):
    run_id: str


class SequenceSelection(BaseModel):
    verse_ref: VerseRef
    ord_index: int


class Commentary(BaseModel):
    verse_ref: VerseRef
    social_en: str
    professional_en: str
    practical_en: str
    caption_final_en: str
    hashtags: List[str]
    style_notes: Optional[str] = None
    fingerprint: str


class ImagePrompt(BaseModel):
    verse_ref: VerseRef
    prompt_text: str
    style_profile: str
    uniqueness_signature: str
    fingerprint: str


class IntentType(str, Enum):
    DIALOGUE = "DIALOGUE"
    SITUATIONAL = "SITUATIONAL"
    CHAPTER_CONTEXT = "CHAPTER_CONTEXT"
    DIVINE_FALLBACK = "DIVINE_FALLBACK"


class VisualIntent(BaseModel):
    intent_type: IntentType
    primary_characters: List[str] = Field(default_factory=list)
    scene_description: str
    confidence: float
    rationale: str


class ImageArtifact(BaseModel):
    run_id: str
    path_raw: str
    hash_raw: str
    provider_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImageComposeInput(BaseModel):
    verse_payload: VersePayload
    image: ImageArtifact


class ImagePromptInput(BaseModel):
    verse_payload: VersePayload
    commentary: Commentary
    visual_intent: VisualIntent


class ComposedImage(BaseModel):
    run_id: str
    path_composed: str
    hash_composed: str
    overlay_text: str
    font_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PostDraft(BaseModel):
    run_id: str
    caption: str
    image_path: str
    status: str
    social_en: Optional[str] = None
    professional_en: Optional[str] = None
    practical_en: Optional[str] = None
    caption_final_en: Optional[str] = None
    hashtags: Optional[List[str]] = None
    style_notes: Optional[str] = None
    fingerprint: Optional[str] = None
    image_prompt_text: Optional[str] = None
    image_prompt_fingerprint: Optional[str] = None
    image_style_profile: Optional[str] = None
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
