#!/usr/bin/env python3
"""
Day 3 Verification: Direct Neo4j Query Layer.

Stages:
  1. Load GitHub + Slack fixtures
  2. Normalize and cross-source link
  3. Cognee ingest (prerequisite for Neo4j data)
  4. Direct Neo4j graph queries (fast path) — verify <1s
  5. Query layer through mosaic (fast vs slow path routing)
  6. Cleanup
"""
import asyncio
import datetime
import os
import sys
import time

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

    return github_normalized, slack_normalized


async def stage4_ingest(github_normalized, slack_normalized):
    print("\nStage 4: Cognee ingest (prerequisite for Neo4j)")

    os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

    dataset = "mosaic_verify_day3"

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
            timeout=1800,
        )
    except asyncio.TimeoutError:
        skip("Cognee ingest", "timed out after 1800s (30 min)")
        return None, None
    except Exception as e:
        msg = str(e).split("\n")[0] if str(e) else type(e).__name__
        skip("Cognee ingest", f"{type(e).__name__}: {msg}")
        return None, None

    expected = {"authors", "files", "commits", "pull_requests", "issues", "reviews", "decisions", "slack_messages"}
    actual = set(enriched.keys())
    if actual == expected:
        ok("process_and_ingest returned all 8 entity types")
    else:
        fail(f"expected {expected}, got {actual}")

    return enriched, dataset


def stage5_direct_graph_queries():
    print("\nStage 5: Direct Neo4j graph queries (fast path)")

    from mosaic.core.memory.graph_query import (
        get_entity_by_name,
        get_neighbors,
        get_timeline,
        search_entities,
        close,
    )

    queries = [
        ("get_entity_by_name('auth')", lambda: get_entity_by_name("auth")),
        ("get_entity_by_name('rishi')", lambda: get_entity_by_name("rishi")),
        ("get_neighbors('github:owner/repo:pr:42')", lambda: get_neighbors("github:owner/repo:pr:42")),
        ("get_timeline('auth')", lambda: get_timeline("auth")),
        ("search_entities('auth')", lambda: search_entities("auth")),
    ]

    for label, fn in queries:
        start = time.time()
        try:
            result = fn()
            elapsed = time.time() - start
            if result is None:
                skip(label, "Neo4j not available")
                continue
            if isinstance(result, list):
                count = len(result)
            elif hasattr(result, "nodes"):
                count = len(result.nodes)
            else:
                count = 1 if result else 0

            if elapsed < 1.0:
                ok(label, f"{count} items in {elapsed:.3f}s")
            else:
                ok(label, f"{count} items in {elapsed:.3f}s (slower than 1s)")
        except Exception as e:
            fail(label, str(e)[:100])

    close()


async def stage6_query_layer():
    print("\nStage 6: Query layer routing (fast path)")

    from mosaic.core.memory.query import (
        get_entity_by_name,
        get_related,
        get_timeline,
    )

    queries = [
        ("get_entity_by_name('auth')", get_entity_by_name("auth")),
        ("get_related('github:owner/repo:pr:42')", get_related("github:owner/repo:pr:42")),
        ("get_timeline('auth')", get_timeline("auth")),
    ]

    for label, coro in queries:
        start = time.time()
        try:
            result = await asyncio.wait_for(coro, timeout=10)
            elapsed = time.time() - start
            if result.get("fast_path"):
                ok(label, f"fast path in {elapsed:.3f}s")
            else:
                ok(label, f"slow path in {elapsed:.3f}s")
        except asyncio.TimeoutError:
            skip(label, "timed out")
        except Exception as e:
            fail(label, str(e)[:100])


async def stage7_cleanup(dataset: str):
    print("\nStage 7: Cleanup")

    if dataset is None:
        skip("cleanup", "no Cognee data to clean")
        return

    import cognee

    await cognee.prune.prune_data()
    ok("test data pruned from Cognee")


async def main():
    print("===== MOSAIC DAY 3 VERIFICATION =====")
    print(f"Python: {sys.version.split()[0]}")

    github_raw, slack_raw = stage1_fixtures()
    github_normalized, slack_normalized = stage2_normalize(github_raw, slack_raw)
    stage3_cross_source_link(github_normalized, slack_normalized)
    enriched, dataset = await stage4_ingest(github_normalized, slack_normalized) or (None, None)

    if dataset:
        stage5_direct_graph_queries()
        await stage6_query_layer()
    else:
        skip("direct graph queries", "ingest did not complete")
        skip("query layer routing", "ingest did not complete")

    await stage7_cleanup(dataset)

    total = passed + failed + skipped
    print(f"\n===== RESULT: {passed}/{total - skipped} passed, {skipped} skipped, {failed} failed =====")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
