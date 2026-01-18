from datetime import datetime

from gita_autoposter.core.contracts import (
    Commentary,
    ComposedImage,
    ImageArtifact,
    ImageComposeInput,
    ImagePrompt,
    PostDraft,
    PostPackageInput,
    PostResult,
    RunReport,
    SequenceInput,
    SequenceSelection,
    VersePayload,
    VerseRef,
)


def test_contracts_validate() -> None:
    verse_ref = VerseRef(chapter=1, verse=1)
    verse_payload = VersePayload(
        verse_ref=verse_ref, sanskrit="test", translation="translation"
    )
    SequenceInput(run_id="run")
    SequenceSelection(verse_ref=verse_ref, ord_index=0)
    commentary = Commentary(
        verse_ref=verse_ref,
        social_en="social",
        professional_en="professional",
        practical_en="practical",
        caption_final_en="caption",
        hashtags=["#test"],
        fingerprint="hash",
    )
    image_prompt = ImagePrompt(
        verse_ref=verse_ref,
        prompt_text="prompt",
        style_profile="style",
        uniqueness_signature="sig",
        fingerprint="hash",
    )
    image_artifact = ImageArtifact(
        run_id="run",
        path_raw="path.png",
        hash_raw="hash",
        provider_name="mock",
    )
    compose_input = ImageComposeInput(verse_payload=verse_payload, image=image_artifact)
    composed_image = ComposedImage(
        run_id="run",
        path_composed="composed.png",
        hash_composed="hash",
        overlay_text="text",
        font_name="font",
    )
    post_package = PostPackageInput(commentary=commentary, composed_image=composed_image)
    post_draft = PostDraft(
        run_id="run", caption="caption", image_path="path.png", status="draft"
    )
    post_result = PostResult(
        run_id="run", platform_ids={"instagram": "1"}, status="success"
    )
    run_report = RunReport(
        run_id="run",
        status="success",
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        error=None,
        artifacts=[image_artifact],
    )

    assert verse_payload.verse_ref == verse_ref
    assert commentary.caption_final_en == "caption"
    assert image_prompt.uniqueness_signature == "sig"
    assert compose_input.image == image_artifact
    assert post_package.composed_image == composed_image
    assert post_draft.status == "draft"
    assert post_result.platform_ids["instagram"] == "1"
    assert run_report.status == "success"
