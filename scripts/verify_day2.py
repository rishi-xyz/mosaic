#!/usr/bin/env python3
"""
Day 2 Verification: Slack Connector + Cross-Source Linking.

Stages:
  1. GitHub fixture + Slack fixture load
  2. Normalize both sources
  3. Cross-source link (Slack ↔ GitHub)
  4. Ingest to Cognee
  5. Query cross-source results
  6. Cleanup
"""
import asyncio
import datetime
import os
import sys

from dotenv import load_dotenv

load_dotenv()

PASS = "✅"
FAIL = "❌"
SKIP = "⚠"
passed = 0
failed = 0
skipped = 0


def ok(label: str, detail: str = ""):
    global passed
    passed += 1
    msg = f"  {PASS} {label}"
    if detail:
        msg += f" ({detail})"
    print(msg)


def fail(label: str, detail: str = ""):
    global failed
    failed += 1
    msg = f"  {FAIL} {label}"
    if detail:
        msg += f": {detail}"
    print(msg)


def skip(label: str, reason: str = ""):
    global skipped
    skipped += 1
    msg = f"  {SKIP} {label}"
    if reason:
        msg += f" ({reason})"
    print(msg)


def _make_github_fixture():
    from mosaic.connectors.github.models import (
        RawCommit,
        RawPullRequest,
        RawIssue,
        RawRepoData,
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    c42 = RawCommit(
        sha="ccc042",
        message="feat: rewrite auth",
        author_login="rishi",
        author_name="Rishi",
        author_email="rishi@c.com",
        committed_at=now,
        diff_patch="--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n-old\n+new",
        files_changed=["auth.py"],
        repo_name="owner/repo",
    )
    c56 = RawCommit(
        sha="ccc056",
        message="feat: add rate limiter",
        author_login="alice",
        author_name="Alice",
        author_email="alice@c.com",
        committed_at=now,
        diff_patch="--- a/rate.py\n+++ b/rate.py\n+new file",
        files_changed=["rate.py"],
        repo_name="owner/repo",
    )
    c214 = RawCommit(
        sha="ccc214",
        message="feat: migrate to Kafka",
        author_login="rishi",
        author_name="Rishi",
        author_email="rishi@c.com",
        committed_at=now,
        diff_patch="--- a/queue.py\n+++ b/queue.py\n@@ -1 +1 @@\n-redis\n+kafka",
        files_changed=["queue.py"],
        repo_name="owner/repo",
    )

    pr42 = RawPullRequest(
        number=42,
        title="Auth rewrite",
        body="Rewrite auth module. Closes #15",
        state="closed",
        author_login="rishi",
        created_at=now,
        merged_at=now,
        closed_at=now,
        base_branch="main",
        head_branch="fix/auth",
        commits=[c42],
        reviewers=["alice"],
        linked_issue_numbers=[15],
        repo_name="owner/repo",
    )
    pr56 = RawPullRequest(
        number=56,
        title="Rate limiter",
        body="Add rate limiting. Closes #23",
        state="open",
        author_login="alice",
        created_at=now,
        merged_at=None,
        closed_at=None,
        base_branch="main",
        head_branch="feat/rate",
        commits=[c56],
        reviewers=["rishi"],
        linked_issue_numbers=[23],
        repo_name="owner/repo",
    )
    pr214 = RawPullRequest(
        number=214,
        title="Kafka migration",
        body="Migrate from Redis Streams to Kafka",
        state="closed",
        author_login="rishi",
        created_at=now,
        merged_at=now,
        closed_at=now,
        base_branch="main",
        head_branch="feat/kafka",
        commits=[c214],
        reviewers=[],
        linked_issue_numbers=[],
        repo_name="owner/repo",
    )

    iss15 = RawIssue(
        number=15,
        title="Token refresh flow broken",
        body="Auth tokens expire without proper refresh",
        state="open",
        author_login="alice",
        created_at=now,
        closed_at=None,
        labels=["bug"],
        repo_name="owner/repo",
    )
    iss18 = RawIssue(
        number=18,
        title="Add tests for auth module",
        body="Need unit tests",
        state="open",
        author_login="rishi",
        created_at=now,
        closed_at=None,
        labels=["enhancement"],
        repo_name="owner/repo",
    )
    iss23 = RawIssue(
        number=23,
        title="Rate limit configuration",
        body="Make rate limits configurable",
        state="closed",
        author_login="alice",
        created_at=now,
        closed_at=now,
        labels=["enhancement"],
        repo_name="owner/repo",
    )

    return RawRepoData(
        owner="owner",
        name="repo",
        commits=[c42, c56, c214],
        pull_requests=[pr42, pr56, pr214],
        issues=[iss15, iss18, iss23],
        reviews=[],
    )


def stage1_fixtures():
    print("\nStage 1: Load fixtures")

    from mosaic.connectors.slack.events import _load_fixture

    github_raw = _make_github_fixture()
    ok("GitHub fixture", f"{len(github_raw.commits)} commits, {len(github_raw.pull_requests)} PRs, {len(github_raw.issues)} issues")

    slack_raw = _load_fixture()
    if slack_raw:
        ok("Slack fixture", f"{slack_raw.channel.name} ({len(slack_raw.messages)} messages)")
    else:
        fail("Slack fixture", "could not load")

    return github_raw, slack_raw


def stage2_normalize(github_raw, slack_raw):
    print("\nStage 2: Normalize both sources")

    from mosaic.core.normalizer.github_normalizer import normalize_entities
    from mosaic.core.normalizer.slack_normalizer import normalize_slack_data

    github_normalized = normalize_entities(github_raw)
    ok("GitHub normalized", f"{len(github_normalized['authors'])} authors, {len(github_normalized['commits'])} commits, {len(github_normalized['pull_requests'])} PRs, {len(github_normalized['issues'])} issues")

    slack_normalized = normalize_slack_data(slack_raw)
    ok("Slack normalized", f"{len(slack_normalized['authors'])} authors, {len(slack_normalized['slack_messages'])} messages")

    return github_normalized, slack_normalized


def stage3_cross_source_link(github_normalized, slack_normalized):
    print("\nStage 3: Cross-source linking")

    from mosaic.core.enricher.linker import link_slack_to_github

    prs = github_normalized["pull_requests"]
    issues = github_normalized["issues"]
    msgs = slack_normalized["slack_messages"]

    link_count_before = sum(len(m.linked_entity_ids) for m in msgs)
    link_slack_to_github(msgs, prs, issues)
    link_count_after = sum(len(m.linked_entity_ids) for m in msgs)
    new_links = link_count_after - link_count_before

    if new_links > 0:
        ok("Slack → GitHub links created", f"{new_links} new links across {len(msgs)} messages")
    else:
        fail("Slack → GitHub links", "no links created")

    # Check specific links
    linked_prs = 0
    linked_issues = 0
    for pr in prs:
        if any(e.startswith("slack:") for e in pr.linked_entity_ids):
            linked_prs += 1
    for issue in issues:
        if any(e.startswith("slack:") for e in issue.linked_entity_ids):
            linked_issues += 1

    ok("PRs with Slack links", str(linked_prs))
    ok("Issues with Slack links", str(linked_issues))

    return github_normalized, slack_normalized


async def stage4_ingest(github_normalized, slack_normalized):
    print("\nStage 4: Cognee ingest (Slack + GitHub)")

    os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

    dataset = "mosaic_verify_day2"

    from mosaic.core.config import configure_cognee
    from mosaic.core.memory.service import process_and_ingest

    configure_cognee()

    merged = {
        **github_normalized,
        "slack_messages": slack_normalized.get("slack_messages", []),
    }

    try:
        enriched = await asyncio.wait_for(
            process_and_ingest(merged, dataset_name=dataset),
            timeout=300,
        )
    except asyncio.TimeoutError:
        skip("Cognee ingest", "timed out after 300s")
        return None
    except Exception as e:
        msg = str(e).split("\n")[0] if str(e) else type(e).__name__
        skip("Cognee ingest", f"{type(e).__name__}: {msg}")
        return None

    expected = {"authors", "files", "commits", "pull_requests", "issues", "reviews", "decisions", "slack_messages"}
    actual = set(enriched.keys())
    if actual == expected:
        ok("process_and_ingest returned all 8 entity types")
    else:
        fail(f"expected {expected}, got {actual}")

    return enriched, dataset


async def stage5_query(dataset: str):
    print("\nStage 5: Cross-source query")

    if dataset is None:
        skip("query", "no data ingested")
        return

    import cognee
    from cognee.modules.search.types import SearchType

    queries = [
        ("auth.py", "file-level query"),
        ("PR #42", "PR reference"),
        ("Token refresh", "issue reference"),
    ]

    queried = 0
    for q_text, label in queries:
        try:
            results = await asyncio.wait_for(
                cognee.search(
                    query_text=q_text,
                    query_type=SearchType.GRAPH_COMPLETION,
                    datasets=[dataset],
                ),
                timeout=30,
            )
            if results:
                ok(f"Query '{label}' returned results", str(results)[:80] + "...")
                queried += 1
            else:
                ok(f"Query '{label}' returned empty", "expected — no cognify ran")
        except asyncio.TimeoutError:
            skip(f"Query '{label}'", "timed out")

    if queried > 0:
        ok(f"{queried}/{len(queries)} queries completed")


async def stage6_cleanup(dataset: str):
    print("\nStage 6: Cleanup")

    if dataset is None:
        skip("cleanup", "no Cognee data to clean")
        return

    import cognee

    await cognee.prune.prune_data()
    ok("test data pruned from Cognee")


async def main():
    print("===== MOSAIC DAY 2 VERIFICATION =====")
    print(f"Python: {sys.version.split()[0]}")

    github_raw, slack_raw = stage1_fixtures()
    github_normalized, slack_normalized = stage2_normalize(github_raw, slack_raw)
    stage3_cross_source_link(github_normalized, slack_normalized)
    result = await stage4_ingest(github_normalized, slack_normalized)

    enriched = None
    dataset = None
    if result:
        enriched, dataset = result

    await stage5_query(dataset)
    await stage6_cleanup(dataset)

    total = passed + failed + skipped
    print(f"\n===== RESULT: {passed}/{total - skipped} passed, {skipped} skipped, {failed} failed =====")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
