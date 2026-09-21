<!-- CROSS-CUTTING REQUIREMENTS — project-owned checklist consulted by sdd-specify.
     Copy to `.sdd/cross-cutting.md` and edit it for this project. Each item becomes an
     acceptance criterion of the stage being specified, or is waived IN WRITING in the
     spec's §6. Requirements discovered late (dark theme, responsive layout...) are the
     most expensive kind: they touch every screen already built.
     Write the content in the project language (Settings > Language). -->

# Cross-cutting requirements

> Items every stage must consider. "Not applicable" is a valid answer, but it is
> written down with a reason, not skipped.

- [ ] Light and dark theme (no hard-coded colors or constants that ignore the theme)
- [ ] Responsive layout (mobile, tablet, desktop)
- [ ] Accessibility (keyboard, focus, labels, contrast)
- [ ] Empty, loading and error states
- [ ] Permissions per role (who can see / change what)
- [ ] E-mails and notifications this behavior should trigger
- [ ] Texts, copy and translations
- [ ] Brand and visual identity
- [ ] Data retention, privacy and audit trail
- [ ] Observability (logs, metrics, alerts)
