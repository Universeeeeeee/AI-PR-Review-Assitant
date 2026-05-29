from app.schemas import PrMetadata
from app.services.github_client import ChangedFile, GitHubPrContext
from app.services.rule_engine import analyze_rules


def test_analyze_rules_detects_security_risks_from_added_lines():
    context = _context(
        [
            ChangedFile(
                filename="src/Login.tsx",
                status="modified",
                additions=4,
                deletions=0,
                patch=(
                    "@@ -1 +1 @@\n"
                    '+ API_TOKEN = "secret-value"\n'
                    "+ dangerouslySetInnerHTML={{ __html: content }}\n"
                    "+ eval(userInput)\n"
                    '+ query = "SELECT * FROM users WHERE id=" + user_id\n'
                ),
            )
        ]
    )

    risks = analyze_rules(context)

    assert _rule_names(risks) >= {
        "hardcoded-secret",
        "unsafe-html",
        "unsafe-eval",
        "sql-string-concat",
    }
    for rule_name in ["hardcoded-secret", "unsafe-html", "unsafe-eval", "sql-string-concat"]:
        risk = _find_rule(risks, rule_name)
        assert risk.severity == "high"
        assert risk.source == "rule"
        assert risk.id.startswith(f"rule-{rule_name}-")


def test_analyze_rules_detects_removed_error_handling_and_null_checks():
    context = _context(
        [
            ChangedFile(
                filename="backend/app/service.py",
                status="modified",
                additions=0,
                deletions=2,
                patch="@@ -1,2 +0,0 @@\n- try:\n- if user is None:\n",
            )
        ]
    )

    risks = analyze_rules(context)

    assert _find_rule(risks, "removed-error-handling").severity == "medium"
    assert _find_rule(risks, "removed-null-check").severity == "medium"


def test_analyze_rules_emits_missing_tests_once_for_core_changes_without_tests():
    context = _context(
        [
            ChangedFile(
                filename="backend/app/main.py",
                status="modified",
                additions=3,
                deletions=1,
                patch="@@ -1 +1 @@\n-old\n+new\n",
            ),
            ChangedFile(
                filename="frontend/src/App.tsx",
                status="modified",
                additions=3,
                deletions=1,
                patch="@@ -1 +1 @@\n-old\n+new\n",
            ),
        ]
    )

    risks = analyze_rules(context)

    missing_tests = [risk for risk in risks if risk.rule_name == "missing-tests"]
    assert len(missing_tests) == 1
    assert missing_tests[0].severity == "medium"


def test_analyze_rules_skips_missing_tests_when_test_file_changed():
    context = _context(
        [
            ChangedFile(
                filename="backend/app/main.py",
                status="modified",
                additions=3,
                deletions=1,
                patch="@@ -1 +1 @@\n-old\n+new\n",
            ),
            ChangedFile(
                filename="backend/tests/test_main.py",
                status="modified",
                additions=5,
                deletions=0,
                patch="@@ -0,0 +1 @@\n+def test_main(): pass\n",
            ),
        ]
    )

    risks = analyze_rules(context)

    assert "missing-tests" not in _rule_names(risks)


def test_analyze_rules_detects_config_large_and_todo_risks():
    context = _context(
        [
            ChangedFile(
                filename="backend/app/config.py",
                status="modified",
                additions=2,
                deletions=0,
                patch="@@ -1 +1 @@\n+ FEATURE_FLAG = true\n+ # TODO: temporary config path\n",
            ),
            ChangedFile(
                filename="src/large.ts",
                status="modified",
                additions=350,
                deletions=0,
                patch="\n".join(["+ const value = 1;"] * 301),
            ),
        ]
    )

    risks = analyze_rules(context)

    assert _find_rule(risks, "config-change").severity == "medium"
    assert _find_rule(risks, "large-change").severity == "medium"
    assert _find_rule(risks, "unclear-todo-fixme").severity == "low"


def test_analyze_rules_detects_removed_tests():
    context = _context(
        [
            ChangedFile(
                filename="backend/tests/test_login.py",
                status="removed",
                additions=0,
                deletions=20,
                patch="@@ -1,2 +0,0 @@\n-def test_login():\n-    assert True\n",
            )
        ]
    )

    risks = analyze_rules(context)

    assert _find_rule(risks, "removed-tests").severity == "high"


def _context(files: list[ChangedFile]) -> GitHubPrContext:
    return GitHubPrContext(
        pr=PrMetadata(
            url="https://github.com/owner/repo/pull/1",
            owner="owner",
            repo="repo",
            number=1,
            title="Test PR",
            author="alice",
            base_branch="main",
            head_branch="feature",
            changed_files=len(files),
            additions=sum(file.additions for file in files),
            deletions=sum(file.deletions for file in files),
        ),
        files=files,
        truncated=False,
        warnings=[],
    )


def _rule_names(risks):
    return {risk.rule_name for risk in risks}


def _find_rule(risks, rule_name: str):
    matches = [risk for risk in risks if risk.rule_name == rule_name]
    assert matches, f"Expected rule {rule_name}"
    return matches[0]
