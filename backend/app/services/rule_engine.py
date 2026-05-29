import hashlib
import re

from app.schemas import RiskItem
from app.services.github_client import ChangedFile, GitHubPrContext


SECRET_PATTERN = re.compile(
    r"\b[\w-]*(api[_-]?key|token|secret|password|passwd|private[_-]?key)[\w-]*\b\s*[:=]\s*['\"][^'\"]{6,}['\"]",
    re.IGNORECASE,
)
SQL_PATTERN = re.compile(r"\b(select|insert|update|delete)\b.+(\+|f['\"]|\.format\()", re.IGNORECASE)
ERROR_HANDLER_PATTERN = re.compile(r"\b(try|catch|except)\b|error\s*handler", re.IGNORECASE)
NULL_CHECK_PATTERN = re.compile(
    r"\b(null|undefined|none)\b|is\s+None|==\s*None|!=\s*None|==\s*null|!=\s*null|\?\.",
    re.IGNORECASE,
)
TODO_PATTERN = re.compile(r"\b(todo|fixme|temporary|hack)\b", re.IGNORECASE)
IF_CONDITION_PATTERN = re.compile(r"\bif\b(.+)")

CONFIG_SUFFIXES = (".env", ".yaml", ".yml", ".json", ".toml")
LOCK_FILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
CORE_PREFIXES = ("src/", "backend/", "frontend/", "app/")
CORE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx")


def analyze_rules(context: GitHubPrContext) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for file in context.files:
        risks.extend(_scan_file(file))

    if _has_core_change(context.files) and not _has_test_change(context.files):
        risks.append(
            _risk(
                rule_name="missing-tests",
                severity="medium",
                file=None,
                evidence="missing-tests",
                title="核心代码变更可能缺少测试覆盖",
                description="本 PR 修改了核心代码文件，但没有看到测试文件同步变更，建议人工确认测试覆盖是否足够。",
                suggestion="建议补充或更新与本次核心逻辑变更相关的自动化测试。",
            )
        )

    return _dedupe(risks)


def _scan_file(file: ChangedFile) -> list[RiskItem]:
    added_lines, deleted_lines = _patch_lines(file.patch)
    risks: list[RiskItem] = []

    for line in added_lines:
        if SECRET_PATTERN.search(line):
            risks.append(
                _risk(
                    "hardcoded-secret",
                    "high",
                    file.filename,
                    line,
                    "疑似硬编码密钥",
                    "新增内容中出现类似 token、secret、password 或 api_key 的敏感配置，可能需要人工确认。",
                    "建议改为从环境变量或密钥管理服务读取，并确认真实密钥未提交到仓库。",
                )
            )
        if "dangerouslySetInnerHTML" in line:
            risks.append(
                _risk(
                    "unsafe-html",
                    "high",
                    file.filename,
                    line,
                    "可能存在不安全 HTML 注入",
                    "新增内容使用 dangerouslySetInnerHTML，若输入未清洗可能带来 XSS 风险。",
                    "建议确认 HTML 内容来源可信，并补充必要的 sanitize 处理。",
                )
            )
        if re.search(r"\beval\s*\(|\bFunction\s*\(", line):
            risks.append(
                _risk(
                    "unsafe-eval",
                    "high",
                    file.filename,
                    line,
                    "可能存在动态代码执行风险",
                    "新增内容使用 eval 或 Function 构造执行动态代码，建议人工重点确认。",
                    "建议改用明确的解析或映射逻辑，避免执行不可控字符串。",
                )
            )
        if SQL_PATTERN.search(line):
            risks.append(
                _risk(
                    "sql-string-concat",
                    "high",
                    file.filename,
                    line,
                    "可能存在 SQL 字符串拼接风险",
                    "新增 SQL 语句看起来包含字符串拼接，可能需要确认是否使用参数化查询。",
                    "建议改为参数化查询或 ORM 安全查询接口。",
                )
            )
        if TODO_PATTERN.search(line):
            risks.append(
                _risk(
                    "unclear-todo-fixme",
                    "low",
                    file.filename,
                    line,
                    "新增临时或待处理标记",
                    "新增内容包含 TODO、FIXME、temporary 或 hack，建议确认是否适合随本 PR 合入。",
                    "建议在 PR 描述中说明后续处理计划，或在当前 PR 中完成相关清理。",
                )
            )
        if _is_complex_condition(line):
            risks.append(
                _risk(
                    "complex-condition",
                    "low",
                    file.filename,
                    line,
                    "条件判断复杂度可能增加",
                    "新增条件判断较长或包含多个逻辑分支，后续维护和测试成本可能上升。",
                    "建议拆分条件、提取命名变量，并补充覆盖关键分支的测试。",
                )
            )

    for line in deleted_lines:
        if ERROR_HANDLER_PATTERN.search(line):
            risks.append(
                _risk(
                    "removed-error-handling",
                    "medium",
                    file.filename,
                    line,
                    "可能删除了异常处理逻辑",
                    "删除内容中包含 try、catch、except 或错误处理相关逻辑，建议确认失败场景仍有兜底。",
                    "建议补充异常路径测试，或确认新的统一错误处理逻辑已经覆盖该场景。",
                )
            )
        if NULL_CHECK_PATTERN.search(line):
            risks.append(
                _risk(
                    "removed-null-check",
                    "medium",
                    file.filename,
                    line,
                    "可能删除了空值保护",
                    "删除内容中包含 null、undefined、None 或可选链相关判断，建议确认空值输入仍被处理。",
                    "建议补充空值、缺省值或异常输入场景测试。",
                )
            )

    if _is_config_file(file.filename):
        severity = "high" if any(SECRET_PATTERN.search(line) for line in added_lines) else "medium"
        risks.append(
            _risk(
                "config-change",
                severity,
                file.filename,
                file.filename,
                "配置文件发生变更",
                "本 PR 修改了配置相关文件，可能影响运行环境、部署行为或本地启动方式。",
                "建议确认 README、环境变量示例和部署配置是否同步更新。",
            )
        )

    if _is_large_change(file):
        risks.append(
            _risk(
                "large-change",
                "medium",
                file.filename,
                f"{file.additions}:{file.deletions}:{len(file.patch)}",
                "单文件变更较大",
                "单个文件的 patch 行数或字符数较大，Review 成本和遗漏风险可能上升。",
                "建议拆分变更或在 PR 描述中说明主要修改点。",
            )
        )

    if _is_test_file(file.filename) and (file.status == "removed" or file.deletions >= 20):
        risks.append(
            _risk(
                "removed-tests",
                "high",
                file.filename,
                f"{file.status}:{file.deletions}",
                "测试覆盖可能被削弱",
                "本 PR 删除了测试文件或大量测试代码，可能降低回归保护能力。",
                "建议确认删除原因，并补充等价测试或在 PR 描述中说明覆盖策略。",
            )
        )

    return risks


def _patch_lines(patch: str) -> tuple[list[str], list[str]]:
    added_lines: list[str] = []
    deleted_lines: list[str] = []
    for line in patch.splitlines():
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            added_lines.append(line[1:].strip())
        elif line.startswith("-"):
            deleted_lines.append(line[1:].strip())
    return added_lines, deleted_lines


def _risk(
    rule_name: str,
    severity: str,
    file: str | None,
    evidence: str,
    title: str,
    description: str,
    suggestion: str,
) -> RiskItem:
    digest = hashlib.sha1(f"{rule_name}|{file or 'pr'}|{evidence}".encode("utf-8")).hexdigest()[:8]
    return RiskItem(
        id=f"rule-{rule_name}-{digest}",
        severity=severity,
        source="rule",
        rule_name=rule_name,
        file=file,
        title=title,
        description=description,
        suggestion=suggestion,
    )


def _is_config_file(filename: str) -> bool:
    normalized = filename.lower()
    basename = normalized.rsplit("/", 1)[-1]
    return (
        basename == ".env.example"
        or "config" in normalized
        or normalized.endswith(CONFIG_SUFFIXES)
    )


def _is_large_change(file: ChangedFile) -> bool:
    normalized = file.filename.lower()
    if normalized.endswith(LOCK_FILES):
        return False
    return len(file.patch.splitlines()) > 300 or len(file.patch) > 12000


def _is_test_file(filename: str) -> bool:
    normalized = filename.lower()
    basename = normalized.rsplit("/", 1)[-1]
    return (
        "/test/" in normalized
        or "/tests/" in normalized
        or "__tests__" in normalized
        or basename.startswith("test_")
        or basename.endswith("_test.py")
        or ".test." in basename
        or ".spec." in basename
    )


def _has_core_change(files: list[ChangedFile]) -> bool:
    return any(_is_core_file(file.filename) for file in files)


def _has_test_change(files: list[ChangedFile]) -> bool:
    return any(_is_test_file(file.filename) for file in files)


def _is_core_file(filename: str) -> bool:
    normalized = filename.replace("\\", "/").lower()
    if _is_test_file(normalized):
        return False
    return normalized.startswith(CORE_PREFIXES) and normalized.endswith(CORE_SUFFIXES)


def _is_complex_condition(line: str) -> bool:
    match = IF_CONDITION_PATTERN.search(line)
    if not match:
        return False
    condition = match.group(1)
    return len(condition) > 100 or condition.count("&&") + condition.count("||") + condition.count(" and ") + condition.count(" or ") >= 3


def _dedupe(risks: list[RiskItem]) -> list[RiskItem]:
    seen: set[str] = set()
    unique: list[RiskItem] = []
    for risk in risks:
        if risk.id in seen:
            continue
        seen.add(risk.id)
        unique.append(risk)
    return unique
