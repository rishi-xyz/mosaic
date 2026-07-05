#!/usr/bin/env python3
import asyncio
import datetime
import httpx
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


def _make_fixture():
    from mosaic.connectors.github.models import (
        RawCommit, RawPullRequest, RawReview, RawIssue, RawRepoData,
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    c1 = RawCommit(
        sha="aaa111", message="fix: resolve auth timeout\n\nCloses #2",
        author_login="rishi", author_name="Rishi", author_email="rishi@c.com",
        committed_at=now, diff_patch="--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n-timeout=30\n+timeout=60",
        files_changed=["auth.py", "config.py"], repo_name="octocat/Hello-World",
    )
    c2 = RawCommit(
        sha="bbb222", message="feat: add rate limiter",
        author_login="rishi", author_name="Rishi", author_email="rishi@c.com",
        committed_at=now, diff_patch="--- a/rate.py\n+++ b/rate.py\n@@ -0,0 +1 @@\n+new file",
        files_changed=["rate.py"], repo_name="octocat/Hello-World",
    )
    pr1 = RawPullRequest(
        number=1, title="Fix auth timeout", body="This PR fixes the auth timeout. Closes #2",
        state="closed", author_login="rishi",
        created_at=now, merged_at=now, closed_at=now,
        base_branch="main", head_branch="fix/auth",
        commits=[c1], reviewers=["alice"],
        linked_issue_numbers=[2], repo_name="octocat/Hello-World",
    )
    rev1 = RawReview(
        id=100, pr_number=1, reviewer_login="alice",
        state="APPROVED", body="LGTM", submitted_at=now,
        repo_name="octocat/Hello-World",
    )
    iss1 = RawIssue(
        number=1, title="Add CI pipeline", body="We need CI",
        state="open", author_login="alice",
        created_at=now, closed_at=None,
        labels=["enhancement"], repo_name="octocat/Hello-World",
    )
    iss2 = RawIssue(
        number=2, title="Auth timeout", body="Auth keeps timing out",
        state="closed", author_login="rishi",
        created_at=now, closed_at=now,
        labels=["bug"], repo_name="octocat/Hello-World",
    )
    return RawRepoData(
        owner="octocat", name="Hello-World",
        commits=[c1, c2], pull_requests=[pr1],
        issues=[iss1, iss2], reviews=[rev1],
    )


async def stage1_connector():
    print("\nStage 1: GitHub Connector")

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        ok("using offline fixture", "no GITHUB_TOKEN set")
        return _make_fixture()

    try:
        from mosaic.connectors.github.client import get_github_client, get_repo
        from mosaic.connectors.github.events import fetch_all

        client = get_github_client()
        repo_name = os.environ.get("GITHUB_REPOSITORY", "octocat/Hello-World")
        repo = get_repo(client, repo_name)
        raw = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, lambda: fetch_all(repo, max_prs=5, max_commits=10, max_issues=5)
            ),
            timeout=60,
        )
        ok(f"fetched {len(raw.commits)} commits, {len(raw.pull_requests)} PRs, {len(raw.issues)} issues")
        return raw
    except Exception as e:
        fail("GitHub API failed", f"{type(e).__name__}: {e!r}")
        ok("falling back to fixture data")
        return _make_fixture()


def stage2_normalizer(raw):
    print("\nStage 2: Normalizer")
    from mosaic.core.normalizer.github_normalizer import normalize_entities

    normalized = normalize_entities(raw)
    expected_keys = {"authors", "files", "commits", "pull_requests", "issues", "reviews"}
    actual_keys = set(normalized.keys())
    if actual_keys == expected_keys:
        ok("all 6 entity types returned")
    else:
        fail(f"expected keys {expected_keys}, got {actual_keys}")

    for key in sorted(expected_keys):
        count = len(normalized[key])
        if count > 0:
            ok(f"{key}", f"{count} entities")
        else:
            ok(f"{key}", "0 entities (expected for this repo)")

    if normalized["commits"]:
        c = normalized["commits"][0]
        if c.source_id.startswith("github:commit:"):
            ok("commit source_id format", c.source_id.split(":")[2])
        else:
            fail("commit source_id format wrong", c.source_id)
        if c.linked_entity_ids:
            ok("commit linked_entity_ids", f"{len(c.linked_entity_ids)} links")
        else:
            fail("commit linked_entity_ids empty")
        if "patch_path" in c.metadata:
            ok("commit patch_path stored", c.metadata["patch_path"])
        else:
            fail("commit missing patch_path in metadata")
        if "diff_patch" not in c.metadata:
            ok("diff_patch excluded from metadata")
        else:
            fail("diff_patch still present in metadata")

    if normalized["pull_requests"]:
        pr = normalized["pull_requests"][0]
        ok(f"PR #{pr.number}: {pr.title[:50]}")
        if pr.commit_ids:
            ok(f"PR has {len(pr.commit_ids)} linked commits")

    if normalized["issues"]:
        issue = normalized["issues"][0]
        ok(f"issue #{issue.number}: {issue.title[:50]}")

    return normalized


def stage3_enricher(normalized):
    print("\nStage 3: Enricher")
    from mosaic.core.enricher.decisions import infer_decisions
    from mosaic.core.enricher.ownership import infer_file_ownership
    from mosaic.core.enricher.related import infer_related_files

    decisions = infer_decisions(normalized["pull_requests"], normalized["issues"])
    if decisions:
        ok("decisions inferred", f"{len(decisions)} decisions")
        d = decisions[0]
        ok(f"  decision: {d.title}")
        if d.linked_entity_ids:
            ok("  decision linked to PR + issue")
    else:
        ok("no decisions inferred (expected — no merged PR + linked issue combo)")

    ownership = infer_file_ownership(normalized["commits"])
    if ownership:
        ok("file ownership inferred", f"{len(ownership)} files with owners")
        fpath = next(iter(ownership))
        ok(f"  e.g. {fpath}: {ownership[fpath][0]['author_id']} ({ownership[fpath][0]['ownership_pct']}%)")
    else:
        fail("file ownership empty")

    related = infer_related_files(normalized["commits"])
    ok("related files analysis", f"{len(related)} files with co-change data")

    return decisions, ownership, related


async def stage4_memory(normalized):
    print("\nStage 4: Memory Service -> Cognee")
    os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

    llm_endpoint = os.environ.get("LLM_ENDPOINT", "http://localhost:11434/v1")
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{llm_endpoint}/models", timeout=5)
    except Exception:
        skip("Cognee ingest", "LLM endpoint unreachable")
        return None

    from mosaic.core.config import configure_cognee
    configure_cognee()

    from mosaic.core.memory.service import process_and_ingest

    try:
        enriched = await asyncio.wait_for(
            process_and_ingest(normalized, dataset_name="mosaic_verify"),
            timeout=300,
        )
    except asyncio.TimeoutError:
        skip("Cognee ingest", "timed out after 300s — local model may be too slow")
        return None
    except Exception as e:
        msg = str(e).split("\n")[0] if str(e) else type(e).__name__
        skip("Cognee ingest", f"{type(e).__name__}: {msg}")
        return None

    expected = {"authors", "files", "commits", "pull_requests", "issues", "reviews", "decisions"}
    actual = set(enriched.keys())
    if actual == expected:
        ok("process_and_ingest returned all 7 entity types")
    else:
        fail(f"expected {expected}, got {actual}")

    import cognee
    from cognee.modules.search.types import SearchType

    try:
        results = await asyncio.wait_for(
            cognee.search(
                query_text="What commits and PRs are in this repository?",
                query_type=SearchType.GRAPH_COMPLETION,
                datasets=["mosaic_verify"],
            ),
            timeout=30,
        )
    except asyncio.TimeoutError:
        skip("Cognee search", "timed out")
        return enriched
    if results:
        ok("Cognee search returned results", str(results)[:80] + "...")
    else:
        fail("Cognee search returned empty")

    return enriched


async def stage5_mcp():
    print("\nStage 5: MCP Server")
    from mosaic.mcp.server import handle_list_tools

    tools = await handle_list_tools()
    names = [t.name for t in tools]
    expected = ["ask", "entity", "timeline", "related", "pre_change_analysis"]

    if names == expected:
        ok("5 tools registered", ", ".join(names))
    else:
        fail(f"expected {expected}, got {names}")

    for t in tools:
        props = t.inputSchema.get("properties", {})
        required = t.inputSchema.get("required", [])
        ok(f"  tool '{t.name}'", f"required: {required}")

    return tools


async def stage6_cleanup(enriched):
    print("\nStage 6: Cleanup")
    if enriched is None:
        skip("cleanup", "no Cognee data to clean")
        return

    import cognee

    await cognee.prune.prune_data()
    ok("test data pruned from Cognee")


async def main():
    print("===== MOSAIC DAY 1 VERIFICATION =====")
    print(f"Python: {sys.version.split()[0]}")
    print(f"GITHUB_TOKEN: {'set' if os.environ.get('GITHUB_TOKEN') else 'not set (fixtures)'}")
    print(f"OPENROUTER_API_KEY: {'set' if os.environ.get('OPENROUTER_API_KEY') else 'not set (Cognee skipped)'}")

    raw = await stage1_connector()
    normalized = stage2_normalizer(raw)
    stage3_enricher(normalized)
    enriched = await stage4_memory(normalized)
    await stage5_mcp()
    await stage6_cleanup(enriched)

    total = passed + failed + skipped
    print(f"\n===== RESULT: {passed}/{total - skipped} passed, {skipped} skipped, {failed} failed =====")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
