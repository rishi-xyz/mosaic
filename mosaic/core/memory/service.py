import cognee

from mosaic.core.normalizer.schemas import (
    NormalizedCommit,
    NormalizedPullRequest,
    NormalizedIssue,
    NormalizedReview,
    NormalizedFile,
    NormalizedAuthor,
    NormalizedDecision,
)
from mosaic.core.enricher.decisions import infer_decisions
from mosaic.core.enricher.ownership import infer_file_ownership
from mosaic.core.enricher.related import infer_related_files


_METADATA_EXCLUDE = {"diff_patch", "patch_path"}


def _entity_to_text(entity) -> str:
    lines = [
        f"Type: {entity.entity_type.value}",
        f"Title: {entity.title}",
        f"Body: {entity.body}",
        f"Source: {entity.source.value}",
        f"Source ID: {entity.source_id}",
        f"Repo: {entity.repo_name}",
    ]
    if entity.metadata:
        for k, v in entity.metadata.items():
            if k in _METADATA_EXCLUDE:
                continue
            if isinstance(v, list):
                lines.append(f"{k}: {', '.join(str(x) for x in v)}")
            else:
                lines.append(f"{k}: {v}")
    if entity.linked_entity_ids:
        lines.append(f"Linked To: {', '.join(entity.linked_entity_ids)}")
    return "\n".join(lines)


async def ingest_to_cognee(
    entities: dict[str, list],
    dataset_name: str = "mosaic_engineering_memory",
) -> None:
    all_texts = []

    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            text = _entity_to_text(entity)
            all_texts.append(text)

    if all_texts:
        await cognee.add(data=all_texts, dataset_name=dataset_name)


async def cognify(dataset_name: str = "mosaic_engineering_memory") -> None:
    await cognee.cognify(dataset_name=dataset_name)


async def process_and_ingest(
    normalized: dict[str, list],
    dataset_name: str = "mosaic_engineering_memory",
) -> dict[str, list]:
    prs: list[NormalizedPullRequest] = normalized.get("pull_requests", [])
    issues: list[NormalizedIssue] = normalized.get("issues", [])
    commits: list[NormalizedCommit] = normalized.get("commits", [])
    authors: list[NormalizedAuthor] = normalized.get("authors", [])
    files: list[NormalizedFile] = normalized.get("files", [])
    reviews: list[NormalizedReview] = normalized.get("reviews", [])

    decisions = infer_decisions(prs, issues)
    file_ownership = infer_file_ownership(commits)
    file_relations = infer_related_files(commits)

    for f in files:
        if f.path in file_ownership:
            f.metadata["owners"] = file_ownership[f.path]
        if f.path in file_relations:
            f.metadata["related_files"] = file_relations[f.path]

    enriched = {
        "authors": authors,
        "files": files,
        "commits": commits,
        "pull_requests": prs,
        "issues": issues,
        "reviews": reviews,
        "decisions": decisions,
    }

    await ingest_to_cognee(enriched, dataset_name)
    try:
        await cognify(dataset_name)
    except Exception:
        pass

    return enriched
