"""Human wording for doctor findings: one message and, when there is one, the
command or action that resolves it. Shared by ``sdd doctor`` and the dashboard so
both say the same thing."""

from __future__ import annotations

from collections import defaultdict

# code -> (message template, fix hint). Templates use the finding's own fields.
_TEXT: dict[str, tuple[str, str]] = {
    "mojibake_v2": ("double-encoded text in {path}", "sdd fix --mojibake"),
    "mojibake_v1": ("possible lost accent in {path}", "review by hand (a '?' may be genuine)"),
    "invalid_utf8": ("{path} is not valid UTF-8", "re-save the file as UTF-8"),
    "spec_without_todo": ("stage {stage} has a spec but no todo.md", "sdd scaffold {stage}"),
    "closed_open_todo": ("closed stage {stage} has {open} open checkbox(es)",
                         "finish it, or mark [-] / [!] and record it in report section 7"),
    "track_not_started": ("track {track} has no stage yet", "start it, or drop it from Active tracks"),
    "track_not_incorporated": ("track {track} has a closed stage not yet incorporated",
                               "sdd track incorporate {track} <stage>"),
    "track_overlap": ("two tracks' footprints overlap: {detail}",
                      "sequence the later stage with 'Depends on' (sdd track check)"),
    "track_claims_invalid": ("a claims.json is invalid: {detail}", "fix or delete the file, then sdd track claim"),
    "sequence_duplicate": ("two files share number {number} in sequence {sequence}",
                           "renumber the newer one (never one already applied elsewhere)"),
    "session_inconsistent": ("saved session: {detail}", "sdd session sync"),
    "session_state_mismatch": ("{detail}", "sdd session sync"),
    "session_branch_mismatch": ("session expects branch {expected} but the current one is {current}",
                                "git switch {expected}, or record the new branch with sdd session sync"),
    "constitution_oversized": ("constitution.md is {bytes} bytes and is read at every session",
                               "move narrative to CHANGELOG.md; keep section 5 rows short"),
    "duplicate_h2": ("section heading '{heading}' appears more than once",
                     "merge the sections or rename one"),
    "long_table_cell": ("table row at line {line} is over 600 bytes",
                        "keep 2-3 sentences and move the detail to backlog.md"),
    "abs_file_links": ("absolute file:/// link at line {line}", "sdd fix --links"),
    "feature_mismatch": ("feature {feature}: constitution says {constitution}, manifest says {manifest}",
                         "sdd fix --features"),
    "provider_shim_unmanaged": ("{path} exists but provider {provider} is not managed by the manifest",
                                "sdd migrate --to v4 --provider {provider}"),
    "cli_older_than_project": ("the installed sdd is older than this project's kit",
                               "reinstall the CLI from the current checkout"),
    "cold_file_oversized": ("{path} is {bytes} bytes", "keep it cold; trim its log rows"),
    "edd_missing_evals": ("stage {stage} has no evals.md", "sdd scaffold {stage}"),
    "edd_spec_not_pointer": ("stage {stage} repeats acceptance criteria instead of pointing to evals.md", "sdd migrate --edd-source-of-truth --dry-run"),
    "edd_todo_not_evals": ("stage {stage} final TODO check does not reference evals.md", "sdd migrate --edd-source-of-truth --dry-run"),
    "edd_missing_checklist": ("closed stage {stage} has no checklist.md", "add the checklist from its template"),
    "edd_eval_uncovered": ("{eval} of stage {stage} has no evidence in checklist.md or report.md",
                           "record its evidence, or mark it [-] / [!] in evals.md"),
    "edd_missing_performance_doc": ("milestones exist but avaliacao-desempenho.md does not",
                                    "create it from templates/avaliacao-desempenho.template.md"),
    "edd_milestone_without_evaluation": ("every stage of milestone {milestone} is done but it has no evaluation",
                                         "write milestones/<milestone>/avaliacao.md"),
    "milestone_not_contiguous": ("milestone {milestone} is not a contiguous slice of the queue",
                                 "reorder the queue or redefine the milestone"),
    "backlog_orphan": ("backlog section '{section}' matches no queue row or pending stage",
                       "delete it or add its queue row"),
    "queue_row_without_section": ("queue row {slug} points to the backlog but has no section there",
                                  "add the section to backlog.md"),
    "docs_missing_file": ("planned document {path} does not exist", "sdd document --create-stubs"),
    "docs_missing_header": ("{path} lacks {missing}", "add the header the plan requires"),
    "docs_path_outside_project": ("document {path} lives outside the project folder", "intended? edit the plan"),
    "dependency_inconsistent": ("{detail}", "sdd deps list"),
    "inside_linked_worktree": ("this is a linked git worktree: its .sdd/ is a stale copy",
                               "continue from the main checkout"),
    "nested_worktree_copies": ("{count} agent worktree copies (with their own .sdd/) under {path}",
                               "sdd fix --gitignore, and exclude the folder from test/lint globs"),
}


class _Missing(defaultdict):
    def __missing__(self, key: str) -> str:
        return "?"


def describe(finding: dict) -> tuple[str, str]:
    """(message, hint) for one finding; unknown codes fall back to the code itself."""
    message, hint = _TEXT.get(finding["code"], (finding["code"], ""))
    def shown(value):
        if isinstance(value, bool):
            return "on" if value else "off"
        return ", ".join(str(x) for x in value) if isinstance(value, list) else value

    fields = _Missing(str, {k: shown(v) for k, v in finding.items()})
    detail = finding.get("detail")
    if isinstance(detail, dict):  # a track conflict: {"kind", "tracks", "paths"|"value"}
        extra = detail.get("paths") or detail.get("value") or ""
        fields["detail"] = " ".join(filter(None, [
            f"{detail.get('kind')}:", " vs ".join(detail.get("tracks", [])),
            ", ".join(extra) if isinstance(extra, list) else str(extra)]))
    return message.format_map(fields), hint.format_map(fields)


def group(findings: list[dict]) -> list[dict]:
    """Collapse repeats of one code into a single entry with a count (103 absolute
    links are one problem, not 103)."""
    groups: dict[str, dict] = {}
    for finding in findings:
        entry = groups.setdefault(finding["code"], {"first": finding, "count": 0})
        entry["count"] += 1
    out = []
    for code, entry in groups.items():
        message, hint = describe(entry["first"])
        out.append({"code": code, "severity": entry["first"]["severity"], "message": message,
                    "hint": hint, "count": entry["count"]})
    return out
