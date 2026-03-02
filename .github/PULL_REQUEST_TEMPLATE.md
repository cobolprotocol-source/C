## PR Checklist — Safe Change

Use this template when proposing changes that must preserve determinism and auditability.

- [ ] I read `docs/SAFE_CHANGE.md` and the repository governance rules.
- [ ] My change is limited to formatting/comments/documentation OR I provided a clear risk assessment.
- [ ] I did NOT change control flow, algorithms, variable/function/class/file names, or reorder statements.
- [ ] I ran `tools/check_safe_change.py` locally and included the output in the PR description.
- [ ] If the change touches `core/` or `runtime/` areas, I included the required deterministic safety header.
- [ ] Tests: I added only non-invasive tests or updated docs; all tests relevant to this change pass.
- [ ] I requested review from the repository architect as specified in `.github/ARCHITECT_GOVERNANCE.md`.

Notes: If your change is potentially risky, open an RFC issue first and do not push direct fixes to core logic.
