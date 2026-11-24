"""Human wording for doctor findings: one message and, when there is one, the
command or action that resolves it. Shared by ``sddkit doctor`` and the dashboard so
both say the same thing."""

from __future__ import annotations

from collections import defaultdict

# code -> (message template, fix hint). Templates use the finding's own fields.
_TEXT: dict[str, tuple[str, str]] = {
    "mojibake_v2": ("double-encoded text in {path}", "sddkit fix --mojibake"),
    "mojibake_v1": ("possible lost accent in {path}", "review by hand (a '?' may be genuine)"),
    "invalid_utf8": ("{path} is not valid UTF-8", "re-save the file as UTF-8"),
    "spec_without_todo": ("stage {stage} has a spec but no todo.md", "sddkit scaffold {stage}"),
    "closed_open_todo": ("closed stage {stage} has {open} open checkbox(es)",
                         "finish it, or mark [-] / [!] and record it in report section 7"),
    "track_not_started": ("track {track} has no stage yet", "start it, drop it from Active tracks, or set its State to 'on hold'"),
    "track_not_incorporated": ("track {track} has a closed stage not yet incorporated",
                               "sddkit track incorporate {track} <stage>"),
    "track_closed_in_place": ("track {track} is closed but still sits outside tracks/_closed/",
                              "sddkit track close {track} --archive"),
    "track_link_stale": ("{count} link(s) in the live index files still point at a track that moved to "
                         "tracks/_closed/ (first: {path}:{line})",
                         "point them at tracks/_closed/<slug>/, or drop them if they were only history"),
    "track_overlap": ("two tracks' footprints overlap: {detail}",
                      "sequence the later stage with 'Depends on' (sddkit track check)"),
    "track_claims_invalid": ("a claims.json is invalid: {detail}", "fix or delete the file, then sddkit track claim"),
    "sequence_duplicate": ("two files share number {number} in sequence {sequence}",
                           "renumber the newer one (never one already applied elsewhere)"),
    "session_inconsistent": ("saved session: {detail}", "sddkit session sync"),
    "session_state_mismatch": ("{detail}", "sddkit session sync"),
    "session_branch_mismatch": ("session expects branch {expected} but the current one is {current}",
                                "git switch {expected}, or record the new branch with sddkit session sync"),
    "session_branch_merged": ("session expects branch {expected}, which is already merged into {current}",
                              "record the current branch with sddkit session sync, or close the stage"),
    "weight_column_missing": ("the stage index (section 5) has {tables} table(s) without a Weight column, "
                              "so every audited stage gets the full audit; a stage can be marked light only through that column",
                              "sddkit fix --weight --dry-run, then sddkit fix --weight"),
    "constitution_oversized": ("the part of constitution.md every session reads (Settings and Current state) "
                               "is {bytes} bytes, over {limit}; the whole file is {total}; biggest sections: {top}",
                               "move the detail out of Settings and Current state into CHANGELOG.md and keep "
                               "a pointer; sddkit doctor --slim lists the long lines"),
    "duplicate_h2": ("section heading '{heading}' appears more than once",
                     "merge the sections or rename one"),
    "long_table_cell": ("table row at line {line} is over 600 bytes",
                        "{advice}"),
    "abs_file_links": ("absolute file:/// link at line {line}", "sddkit fix --links"),
    "feature_mismatch": ("feature {feature}: constitution says {constitution}, manifest says {manifest}",
                         "sddkit fix --features"),
    "manifest_eol_drift": ("{count} managed file(s) differ from the manifest only by line endings (e.g. {path})",
                           "sddkit fix --manifest"),
    "eol_crlf": ("{count} managed file(s) of the kit are in CRLF (e.g. {path}); the kit keeps LF",
                 "sddkit fix --eol --manifest --dry-run, then without --dry-run (--manifest re-records the hashes)"),
    "managed_file_edited": ("{count} managed file(s) differ from the kit and from the manifest (e.g. {path})",
                            "compare with the bundled kit and merge by hand, or restore from .sdd/.pre-migrate-backup/"),
    "readme_anchor_missing": (".sdd/README.md lacks the section '{anchor}' that skills and templates cite",
                              "merge that section from the bundled kit README into .sdd/README.md"),
    "provider_shim_unmanaged": ("{path} exists but provider {provider} is not managed by the manifest",
                                "sddkit migrate --to v4 --provider {provider}"),
    "migration_todo_pending": ("{path} still exists: the migration is not finished",
                               "have the agent finish its tasks, then delete the file (or delete it if you no longer need it)"),
    "cli_older_than_project": ("the installed sddkit is older than this project's kit",
                               "reinstall the CLI from the current checkout"),
    "kit_behind": ("this project's kit is {kit}, older than the installed sddkit {cli}",
                   "sddkit update --notes to read what changed, then sddkit update --dry-run"),
    "lock_without_audit": ("locked stage {stage} has no Locked-by-audit line in its spec",
                           "run the sdd-audit skill until READY TO LOCK, record it in audit.md, add the line"),
    "lock_audit_mismatch": ("stage {stage}: Locked-by-audit disagrees with audit.md ({detail})",
                            "correct the line or the record so they say the same"),
    "light_hits_audit_trigger": ("light stage {stage} touches {path}, which {trigger} in audit-lenses.md forces to full",
                                 "set Weight to full, or write why in the cell and get the owner's agreement"),
    "global_skill_stale": ("the global sdd skill {path} predates this kit",
                           "sddkit update --global-skill (keeps a backup)"),
    "cold_file_oversized": ("{path} is {bytes} bytes (limit {limit}){extra}", "{advice}"),
    "edd_missing_evals": ("stage {stage} has no evals.md", "sddkit scaffold {stage}"),
    "edd_closed_without_evals": ("closed stage {stage} has no evals.md (closed before EDD was turned on?)",
                                 "nothing to do if it predates EDD; otherwise add its evals.md and checklist.md"),
    "edd_spec_not_pointer": ("stage {stage} repeats acceptance criteria instead of pointing to evals.md", "sddkit migrate --edd-source-of-truth --dry-run"),
    "edd_todo_not_evals": ("stage {stage} final TODO check does not reference evals.md", "sddkit migrate --edd-source-of-truth --dry-run"),
    "edd_missing_checklist": ("closed stage {stage} has no checklist.md", "add the checklist from its template"),
    "edd_no_criteria": ("closed stage {stage} has an evals.md with no E-NNN criterion",
                        "add the criteria the stage was closed against, or mark why none applies"),
    "edd_eval_uncovered": ("{eval} of stage {stage} has no evidence in checklist.md or report.md",
                           "record its evidence, or mark it [-] / [!] in evals.md"),
    "edd_missing_performance_doc": ("milestones exist but avaliacao-desempenho.md does not",
                                    "create it from templates/avaliacao-desempenho.template.md"),
    "edd_milestone_without_evaluation": ("every stage of milestone {milestone} is done but it has no evaluation",
                                         "write milestones/<milestone>/avaliacao.md"),
    "milestone_not_contiguous": ("milestone {milestone} is not a contiguous slice of the queue",
                                 "reorder the queue or redefine the milestone"),
    "weight_light_without_reason": ("stage {stage} is marked light without a reason",
                                    "write it in the Weight cell, e.g. `light: only fixes a typo`, or set it to full"),
    "backlog_orphan": ("backlog section '{section}' matches no queue row or pending stage",
                       "delete the section, or add its slug to a `slug` column of the Provisional "
                       "queue TABLE in constitution.md §5 (e.g. `| slug | item | detail |` with a "
                       "row naming it) -- a bullet list or a `backlog.md#slug` anchor link is not "
                       "parsed, only a markdown table with a literal `slug` column is"),
    "queue_row_without_section": ("queue row {slug} points to the backlog but has no section there",
                                  "add a `## {slug}` section to backlog.md"),
    "adr_duplicate_id": ("{adr} is used by more than one file under .sdd/decisions/: {paths}",
                         "renumber the newer one (never one already cited elsewhere) and run sddkit adr index"),
    "adr_status_invalid": ("{adr} ({path}): {detail}",
                           "set `status:` in its frontmatter to proposta, aceita, implementada, substituída or obsoleta"),
    "adr_without_decision": ("{adr}: {detail}",
                             "set `decision: D-NNN` in its frontmatter to a row of section 3 (every record has a row)"),
    "decision_row_adr_missing": ("{decision} in section 3 points at {adr}, which is not in .sdd/decisions/",
                                 "fix or empty the Record cell, or restore the record"),
    "adr_implemented_without_ref": ("{adr} is `implementada` but names no `implemented_in`",
                                    "set `implemented_in:` to the stage, file or commit that implements it"),
    "adr_superseded_without_successor": ("{adr} is `substituída` but {detail}",
                                         "set `superseded_by:` to the record that replaces it "
                                         "(sddkit adr new --supersedes does it for you)"),
    "adr_index_stale": ("{path} does not match the records' frontmatter", "sddkit adr index"),
    "decisions_dir_missing": ("{count} decision(s) in section 3 and no .sdd/decisions/ folder",
                              "sddkit adr new \"<title>\" --decision D-NNN for a new record; "
                              "sddkit adr init rebuilds records for decisions made before this folder existed "
                              "(or write `not applicable` in section 7 if the project keeps no ADRs)"),
    "adr_external_path_missing": ("section 7 says the ADRs are external: {detail}",
                                  "fix the path in the `Decision records` field of section 7"),
    "docs_missing_file": ("planned document {path} does not exist", "sddkit document --create-stubs"),
    "docs_missing_header": ("{path} lacks {missing}", "add the header the plan requires"),
    "docs_path_outside_project": ("document {path} lives outside the project folder", "intended? edit the plan"),
    "dependency_inconsistent": ("{detail}", "sddkit deps list"),
    "tracks_setting_missing": ("real track activity (an Active tracks row, or a tracks/*/state.md) but "
                               "no explicit `Parallel tracks:` line in Settings",
                               "add `**Parallel tracks:** on` (real concurrency, claims checked) or `off` "
                               "(a sequential grouping, no other session working at the same time) -- "
                               "do not turn it on just to unblock a skill that checks it"),
    "inside_linked_worktree": ("this is a linked git worktree: its .sdd/ is a stale copy",
                               "continue from the main checkout"),
    "nested_worktree_copies": ("{count} agent worktree copies (with their own .sdd/) under {path}",
                               "sddkit fix --gitignore, and exclude the folder from test/lint globs"),
    "backup_not_ignored": ("{count} kit backup folder(s) under .sdd/ (e.g. {path}) are visible to Git; "
                           "`git add -A` would commit a copy of your files",
                           "sddkit fix --gitignore"),
    "backup_tracked": ("{count} kit backup folder(s) under .sdd/ (e.g. {path}) are already tracked by Git; "
                       "a copy of your files is in the repository",
                       "git rm -r --cached {path}  (then `sddkit doctor` says whether .gitignore still needs a line)"),
    "nested_worktree_copies_ignored": (
        "{count} agent worktree copies under {path} are already .gitignore'd, but a test/lint/"
        "type-check tool that reads the filesystem directly still scans them",
        "{advice}"),
}


class _Missing(defaultdict):
    def __missing__(self, key: str) -> str:
        return "?"


def _fill(finding: dict, fields: dict) -> None:
    """Wording that depends on which section or file a finding is about (B-01, B-03)."""
    if finding["code"] == "long_table_cell":
        where = finding.get("destination")
        fields["advice"] = (
            f"keep 2-3 sentences and move the detail to {where} with a pointer; "
            "a locked decision is never archived to backlog.md" if where == "CHANGELOG.md" else
            f"keep 2-3 sentences and move the detail to {where}" if where else
            "keep 2-3 sentences and move the detail to the file that holds it "
            "(CHANGELOG.md for history, backlog.md for work still to do)")
    elif finding["code"] == "cold_file_oversized":
        if finding.get("path") == ".sdd/constitution.md":
            fields["extra"] = (f"; a session reads only {finding.get('hot', '?')} bytes of it (Settings and "
                               f"Current state); biggest sections: {finding.get('top', '')}")
            fields["advice"] = ("sddkit doctor --slim lists what to move and where; sddkit fix --slim --dry-run "
                                f"removes {finding.get('slim_bytes', 0)} B of unchanged template comments; "
                                "or set `**Constitution max size:**` in Settings")
        else:
            fields["extra"] = ""
            fields["advice"] = "keep it cold; trim its log rows, or set `**Cold file max size:**` in Settings"


def describe(finding: dict) -> tuple[str, str]:
    """(message, hint) for one finding; unknown codes fall back to the code itself."""
    message, hint = _TEXT.get(finding["code"], (finding["code"], ""))
    def shown(value):
        if isinstance(value, bool):
            return "on" if value else "off"
        return ", ".join(str(x) for x in value) if isinstance(value, list) else value

    fields = _Missing(str, {k: shown(v) for k, v in finding.items()})
    _fill(finding, fields)
    detail = finding.get("detail")
    if isinstance(detail, dict):  # a track conflict: {"kind", "tracks", "paths"|"value"}
        extra = detail.get("paths") or detail.get("value") or ""
        fields["detail"] = " ".join(filter(None, [
            f"{detail.get('kind')}:", " vs ".join(detail.get("tracks", [])),
            ", ".join(extra) if isinstance(extra, list) else str(extra)]))
    return message.format_map(fields), hint.format_map(fields)


def location(finding: dict) -> str:
    """Where one finding is, in a few words (``doctor --all``): file and line, stage, track..."""
    where = []
    if finding.get("path"):
        where.append(str(finding["path"]) + (f":{finding['line']}" if finding.get("line") else ""))
    elif finding.get("line"):
        where.append(f"line {finding['line']}")
    for key in ("stage", "track", "milestone", "heading", "feature", "section", "slug"):
        if finding.get(key):
            where.append(f"{key} {finding[key]}")
    if finding.get("bytes"):
        where.append(f"{finding['bytes']} B")
    return ", ".join(where) or finding["code"]


def group(findings: list[dict]) -> list[dict]:
    """Collapse repeats of one code into a single entry with a count (103 absolute
    links are one problem, not 103)."""
    groups: dict[str, dict] = {}
    for finding in findings:
        entry = groups.setdefault(finding["code"], {"first": finding, "count": 0, "members": []})
        entry["count"] += 1
        entry["members"].append(finding)
    out = []
    for code, entry in groups.items():
        message, hint = describe(entry["first"])
        out.append({"code": code, "severity": entry["first"]["severity"], "message": message,
                    "hint": hint, "count": entry["count"], "members": entry["members"]})
    return out
