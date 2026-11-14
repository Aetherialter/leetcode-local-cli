import io
import tokenize
from importlib.resources import files
from pathlib import Path

from leetcode_local_cli.models.solution import (
    ProblemMetadata,
    SolutionFileInspection,
    SolutionFileStatus,
    WorkspaceError,
)
from leetcode_local_cli.storage.safe_files import SafeFileError, atomic_write_text
from leetcode_local_cli.storage.solution_source import (
    SolutionSourceEncodingError,
    read_solution_source,
)

METADATA_PREFIX = "# @lc "
START_FLAG = "# @lc submit_begin"
END_FLAG = "# @lc submit_end"
NOT_IMPLEMENTED_PLACEHOLDER = 'raise NotImplementedError("请实现题目方法")'

SOLUTION_FILE_HEADER = """# pyright: reportUnusedImport=false, reportUnusedVariable=false
# ruff: noqa: F401, F841
"""

SOLUTION_IMPORTS = """from typing import Any, Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict, deque
from functools import cache, lru_cache
from itertools import accumulate, combinations, permutations, product
from bisect import bisect_left, bisect_right, insort
from heapq import heapify, heappop, heappush
from math import gcd, inf, isqrt, lcm
"""


def _normalize_python_code(python_code: str) -> str:
    code = python_code.rstrip()
    if not code:
        return code

    lines = code.splitlines()
    last_line = lines[-1]
    stripped_last_line = last_line.rstrip()
    indentation = last_line[: len(last_line) - len(last_line.lstrip())]
    if stripped_last_line.endswith(": pass"):
        header = stripped_last_line.removesuffix("pass").rstrip()
        return "\n".join(
            [*lines[:-1], header, f"{indentation}    {NOT_IMPLEMENTED_PLACEHOLDER}"]
        )
    if stripped_last_line.endswith(":"):
        return f"{code}\n{indentation}    {NOT_IMPLEMENTED_PLACEHOLDER}"
    return code


def build_solution_content(python_code: str, metadata: ProblemMetadata) -> str:
    metadata_content = (
        f"{METADATA_PREFIX}problem_id: {metadata.problem_id}\n"
        f"{METADATA_PREFIX}submit_question_id: {metadata.submit_question_id}\n"
        f"{METADATA_PREFIX}title: {metadata.title}\n"
        f"{METADATA_PREFIX}title_slug: {metadata.title_slug}\n\n"
    )
    return (
        f"{SOLUTION_FILE_HEADER}"
        f"{metadata_content}"
        f"{SOLUTION_IMPORTS}\n\n"
        f"{files('leetcode_local_cli.models').joinpath('nodes.py').read_text(encoding='utf-8')}\n\n"
        f"{START_FLAG}\n"
        f"{_normalize_python_code(python_code)}\n"
        f"{END_FLAG}\n"
    )


def write_solution_file(
    path: Path,
    python_code: str,
    metadata: ProblemMetadata,
) -> None:
    try:
        atomic_write_text(
            path,
            build_solution_content(python_code, metadata),
            label="solution.py",
        )
    except SafeFileError as exc:
        raise WorkspaceError(str(exc)) from exc


def _collect_standalone_lc_comments(content: str) -> list[tuple[int, str]]:
    """Collect standalone `# @lc ...` comments outside f-strings and strings."""
    comments: list[tuple[int, str]] = []
    fstring_depth = 0
    try:
        for token in tokenize.generate_tokens(io.StringIO(content).readline):
            if token.type == tokenize.FSTRING_START:
                fstring_depth += 1
                continue
            if token.type == tokenize.FSTRING_END:
                fstring_depth = max(0, fstring_depth - 1)
                continue
            if token.type != tokenize.COMMENT or fstring_depth > 0:
                continue
            line_text = token.line
            if line_text[: token.start[1]].strip() or line_text[token.end[1] :].strip():
                continue
            comment = token.string.strip()
            if comment.startswith(METADATA_PREFIX):
                comments.append((token.start[0], comment))
    except tokenize.TokenError as exc:
        message = exc.args[0] if exc.args else ""
        if (
            fstring_depth > 0
            or not isinstance(message, str)
            or not message.startswith("unexpected EOF in multi-line statement")
        ):
            raise WorkspaceError(
                "solution.py 存在未闭合字符串或词法错误，无法解析提交区域"
            ) from exc
    except IndentationError as exc:
        raise WorkspaceError("solution.py 存在缩进错误，无法解析提交区域") from exc
    if fstring_depth > 0:
        raise WorkspaceError("solution.py 存在未闭合字符串或词法错误，无法解析提交区域")
    return comments


def _parse_solution_submission_content(content: str) -> tuple[ProblemMetadata, str]:
    comments = _collect_standalone_lc_comments(content)
    begin_lines = [lineno for lineno, text in comments if text == START_FLAG]
    end_lines = [lineno for lineno, text in comments if text == END_FLAG]

    if not begin_lines or not end_lines:
        raise WorkspaceError("solution.py 提交区域标记不完整，请先执行 lc solve <题号>")
    if len(begin_lines) > 1 or len(end_lines) > 1:
        raise WorkspaceError("solution.py 存在重复的提交区域标记，请保留唯一一对标记")

    begin_line = begin_lines[0]
    end_line = end_lines[0]
    if begin_line >= end_line:
        raise WorkspaceError(
            "solution.py 提交区域标记顺序无效，请检查 # @lc submit_begin 与 # @lc submit_end"
        )

    metadata: dict[str, str] = {}
    for lineno, text in comments:
        if lineno >= begin_line:
            break
        item = text.removeprefix(METADATA_PREFIX)
        key, separator, value = item.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()

    lines = io.StringIO(content).readlines()
    submission_code = "".join(lines[begin_line : end_line - 1]).strip()
    if not submission_code:
        raise WorkspaceError("solution.py 提交区域为空")

    if not all(
        [
            metadata.get("problem_id"),
            metadata.get("submit_question_id"),
            metadata.get("title"),
            metadata.get("title_slug"),
        ]
    ):
        raise WorkspaceError(
            "solution.py 缺少元数据：problem_id、submit_question_id、title、title_slug"
        )

    return (
        ProblemMetadata(
            problem_id=metadata["problem_id"],
            submit_question_id=metadata["submit_question_id"],
            title=metadata["title"],
            title_slug=metadata["title_slug"],
        ),
        submission_code,
    )


def parse_solution_submission(path: Path) -> tuple[ProblemMetadata, str]:
    try:
        content = read_solution_source(path)
    except FileNotFoundError as exc:
        raise WorkspaceError("未找到 solution.py，请先执行 lc solve <题号>") from exc
    except SolutionSourceEncodingError as exc:
        raise WorkspaceError(str(exc)) from exc
    except OSError as exc:
        raise WorkspaceError("无法读取 solution.py，请检查文件权限") from exc
    return _parse_solution_submission_content(content)


def inspect_solution_file(path: Path) -> SolutionFileInspection:
    try:
        content = read_solution_source(path)
    except FileNotFoundError:
        return SolutionFileInspection(status=SolutionFileStatus.MISSING)
    except SolutionSourceEncodingError as exc:
        return SolutionFileInspection(
            status=SolutionFileStatus.INVALID_ENCODING,
            detail=str(exc),
        )
    except OSError:
        return SolutionFileInspection(status=SolutionFileStatus.READ_ERROR)

    if not content.strip():
        return SolutionFileInspection(status=SolutionFileStatus.EMPTY)

    try:
        compile(content, str(path), "exec")
    except SyntaxError as exc:
        return SolutionFileInspection(
            status=SolutionFileStatus.INVALID_SYNTAX,
            detail=exc.msg,
            syntax_line=exc.lineno,
        )

    try:
        metadata, _ = _parse_solution_submission_content(content)
    except WorkspaceError as exc:
        return SolutionFileInspection(
            status=SolutionFileStatus.NOT_SUBMITTABLE,
            detail=str(exc),
        )

    return SolutionFileInspection(
        status=SolutionFileStatus.READY,
        metadata=metadata,
    )
