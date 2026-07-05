from mosaic.core.normalizer.schemas import (
    NormalizedPullRequest,
    NormalizedIssue,
    NormalizedDecision,
)


def _make_decision_id(repo: str, pr_number: int) -> str:
    return f"github:decision:{repo}:{pr_number}"


def infer_decisions(
    pull_requests: list[NormalizedPullRequest],
    issues: list[NormalizedIssue],
) -> list[NormalizedDecision]:
    issue_by_number: dict[int, NormalizedIssue] = {i.number: i for i in issues}
    decisions: list[NormalizedDecision] = []

    for pr in pull_requests:
        if pr.state != "closed" or not pr.merged_at:
            continue

        if not pr.linked_issue_numbers:
            continue

        for issue_num in pr.linked_issue_numbers:
            linked_issue = issue_by_number.get(issue_num)
            if not linked_issue:
                continue

            decision_id = _make_decision_id(pr.repo_name, pr.number)
            decisions.append(
                NormalizedDecision(
                    source_id=decision_id,
                    title=f"Decision: {pr.title}",
                    body=f"PR #{pr.number}: {pr.title}\nIssue #{issue_num}: {linked_issue.title}\n\n{pr.body}",
                    created_at=pr.merged_at,
                    author_id=pr.author_id,
                    repo_name=pr.repo_name,
                    metadata={
                        "pr_number": pr.number,
                        "issue_number": issue_num,
                        "pr_title": pr.title,
                        "issue_title": linked_issue.title,
                    },
                    pr_number=pr.number,
                    issue_number=issue_num,
                    description=f"PR #{pr.number} (\"{pr.title}\") merged, linked to Issue #{issue_num} (\"{linked_issue.title}\")",
                    linked_entity_ids=[pr.source_id, linked_issue.source_id],
                )
            )

    return decisions
