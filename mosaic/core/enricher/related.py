from collections import defaultdict

from mosaic.core.normalizer.schemas import NormalizedCommit


def infer_related_files(commits: list[NormalizedCommit], min_cooccurrence: int = 2) -> dict[str, list[dict]]:
    file_pairs: dict[tuple[str, str], int] = defaultdict(int)

    for commit in commits:
        files = sorted(commit.files_changed)
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pair = (files[i], files[j])
                file_pairs[pair] += 1

    related: dict[str, list[dict]] = {}
    for (fa, fb), count in file_pairs.items():
        if count < min_cooccurrence:
            continue
        if fa not in related:
            related[fa] = []
        if fb not in related:
            related[fb] = []
        related[fa].append({"file": fb, "cooccurrence_count": count})
        related[fb].append({"file": fa, "cooccurrence_count": count})

    for f in related:
        related[f].sort(key=lambda x: x["cooccurrence_count"], reverse=True)

    return related
