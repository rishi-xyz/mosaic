import re

from mosaic.core.normalizer.schemas import NormalizedPullRequest, NormalizedIssue


def link_prs_to_issues(
    pull_requests: list[NormalizedPullRequest],
    issues: list[NormalizedIssue],
) -> None:
    issue_by_number: dict[int, NormalizedIssue] = {i.number: i for i in issues}

    for pr in pull_requests:
        for issue_num in pr.linked_issue_numbers:
            linked = issue_by_number.get(issue_num)
            if linked:
                if linked.source_id not in pr.linked_entity_ids:
                    pr.linked_entity_ids.append(linked.source_id)
                if pr.source_id not in linked.linked_entity_ids:
                    linked.linked_entity_ids.append(pr.source_id)
                linked.linked_pr_number = pr.number


def detect_cross_refs(text: str, repo_name: str) -> list[dict]:
    if not text:
        return []
    refs = []
    pattern = r"(?:#(\d+))"
    for match in re.finditer(pattern, text):
        refs.append({
            "type": "issue",
            "repo": repo_name,
            "number": int(match.group(1)),
        })
    return refs
