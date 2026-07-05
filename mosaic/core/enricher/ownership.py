from collections import Counter

from mosaic.core.normalizer.schemas import NormalizedCommit


def infer_file_ownership(commits: list[NormalizedCommit]) -> dict[str, list[dict]]:
    file_authors: dict[str, Counter] = {}

    for commit in commits:
        for fpath in commit.files_changed:
            if fpath not in file_authors:
                file_authors[fpath] = Counter()
            file_authors[fpath][commit.author_id] += 1

    ownership: dict[str, list[dict]] = {}
    for fpath, author_counts in file_authors.items():
        total = sum(author_counts.values())
        owners = [
            {
                "author_id": author,
                "commit_count": count,
                "ownership_pct": round(count / total * 100, 1),
            }
            for author, count in author_counts.most_common()
        ]
        ownership[fpath] = owners

    return ownership
