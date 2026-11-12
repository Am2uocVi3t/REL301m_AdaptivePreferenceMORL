# Git workflow and pair-review policy

This document describes the team's ownership and review agreement for the
REL301m project. Merging source code does not establish scientific claims or
authorize experiment execution.

## Ownership matrix

| Feature branch | Co-owners | Observer | Responsibility |
|---|---|---|---|
| `feat/algorithm-curriculum` | Ngo Hoai Nam, Huynh Quoc Viet | Le Nguyen Gia Hung | Vector Q-network, masked heads, curriculum and training loop |
| `feat/env-baselines` | Le Nguyen Gia Hung, Ngo Hoai Nam | Huynh Quoc Viet | Environment/reward wrappers, declared dynamics shifts and baseline adapters |
| `feat/eval-pipeline` | Le Nguyen Gia Hung, Huynh Quoc Viet | Ngo Hoai Nam | Metrics, statistical analysis, evaluation and preference-demo integration |

These are responsibility assignments, not evidence that every planned metric,
shift, baseline or comparative study has been completed.

## Review and merge

The original team agreement calls for both co-owners to inspect the change and
agree before merging a feature into `main`. GitHub does not allow a PR author
to approve their own PR, so the partner supplies the independent approval and
the author records their own checks in the PR description. The repository's
actual branch-protection rules determine the required approval count.

The observer checks that the responsible pair reviewed the change, required
checks passed and no merge conflicts remain. The observer should not merge on
the pair's behalf without their recorded agreement. Do not bypass branch
protection, dismiss reviews merely to force a merge or treat an approval as
scientific qualification.

## Daily workflow

Inspect the working tree first and preserve unrelated changes. Use a dedicated
branch for substantial work; coding-agent branches normally use `codex/`.

```bash
git status --short
git fetch origin
git switch -c codex/describe-the-change origin/main

# Make the intended changes and run appropriate checks.
python -m pytest -q

# Stage only files belonging to the change.
git add <reviewed-file> <another-reviewed-file>
git diff --cached --check
git diff --cached
git commit -m "docs: describe the completed change"
git push -u origin codex/describe-the-change
```

Do not use blanket staging when the checkout contains unrelated user edits.
Update from `main` and resolve conflicts only after inspecting the live
working tree. Never discard user changes to make a branch appear clean.

## Pull request description

Lead with the problem and resulting behavior. State what changed, what was
tested and any meaningful limitation. Link experiment claims to versioned
evidence rather than to a successful software check.

```markdown
Summary:
- Explain the concrete problem and final behavior.

Review:
- Author checked the intended changes and validation.
- Partner reviewed and approved.
- Observer verified the required process, where applicable.

Validation:
- List commands and actual outcomes.
- Report skips, unavailable artifacts and unresolved limitations.
```

Keep scientific gates separate: checkpoint locking, final-test access, paid
review and new training require their own authorization and evidence.

## Branch-protection administration

Repository owners manage protection settings; this guide does not authorize
changing them. The team's intended protection is PR-based review, approval
requirements compatible with GitHub's author-review rule, dismissal of stale
approvals after new commits, appropriate status checks and no protection bypass.

For a blocked PR, inspect GitHub's reported reason and obtain the required
review. Do not weaken repository rules to finish a hand-in.
