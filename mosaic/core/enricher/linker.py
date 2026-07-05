import re

from mosaic.core.normalizer.schemas import (
    NormalizedIssue,
    NormalizedPullRequest,
    NormalizedSlackMessage,
)


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


def _build_pr_lookup(
    pull_requests: list[NormalizedPullRequest],
) -> dict[str, dict[int, NormalizedPullRequest]]:
    lookup: dict[str, dict[int, NormalizedPullRequest]] = {}
    for pr in pull_requests:
        lookup.setdefault(pr.repo_name, {})[pr.number] = pr
    return lookup


def _build_issue_lookup(
    issues: list[NormalizedIssue],
) -> dict[str, dict[int, NormalizedIssue]]:
    lookup: dict[str, dict[int, NormalizedIssue]] = {}
    for issue in issues:
        lookup.setdefault(issue.repo_name, {})[issue.number] = issue
    return lookup


def _try_link(
    ref_type: str,
    repo: str,
    number: int,
    msg: NormalizedSlackMessage,
    pr_lookup: dict[str, dict[int, NormalizedPullRequest]],
    issue_lookup: dict[str, dict[int, NormalizedIssue]],
) -> None:
    if ref_type == "pr":
        candidates = pr_lookup.get(repo, {})
        entity = candidates.get(number)
    else:
        candidates = issue_lookup.get(repo, {})
        entity = candidates.get(number)

    if entity is None:
        return

    if entity.source_id not in msg.linked_entity_ids:
        msg.linked_entity_ids.append(entity.source_id)
    if msg.source_id not in entity.linked_entity_ids:
        entity.linked_entity_ids.append(msg.source_id)


def link_slack_to_github(
    slack_messages: list[NormalizedSlackMessage],
    pull_requests: list[NormalizedPullRequest],
    issues: list[NormalizedIssue],
    default_repo: str = "",
) -> None:
    pr_lookup = _build_pr_lookup(pull_requests)
    issue_lookup = _build_issue_lookup(issues)

    pr_explicit = re.compile(r"(?:^|\s)PR[\s#-]+(\d+)(?:\s|$|[.,!?])", re.IGNORECASE)
    bare_ref = re.compile(r"(?:^|\s)#(\d+)(?:\s|$|[.,!?])")
    cross_repo = re.compile(r"(\S+/\S+)#(\d+)")

    repos_with_data = set(pr_lookup.keys()) | set(issue_lookup.keys())

    for msg in slack_messages:
        texts = [msg.body] + msg.replies

        for text in texts:
            if not text:
                continue

            # Cross-repo: owner/repo#123 — try PR then issue
            for match in cross_repo.finditer(text):
                repo, num = match.group(1), int(match.group(2))
                if repo in pr_lookup:
                    _try_link("pr", repo, num, msg, pr_lookup, issue_lookup)
                if repo in issue_lookup:
                    _try_link("issue", repo, num, msg, pr_lookup, issue_lookup)

            # PR-123, PR #123, PR#123
            for match in pr_explicit.finditer(text):
                num = int(match.group(1))
                for repo in repos_with_data:
                    _try_link("pr", repo, num, msg, pr_lookup, issue_lookup)

            # #123 — try as issue and PR against all known repos
            for match in bare_ref.finditer(text):
                num = int(match.group(1))
                for repo in repos_with_data:
                    _try_link("issue", repo, num, msg, pr_lookup, issue_lookup)
                    _try_link("pr", repo, num, msg, pr_lookup, issue_lookup)
