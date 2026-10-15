# Paper Full-Text Access Policy Plan

Goal: make paper access and evidence level explicit so agents never treat metadata or an abstract as a completed reading.

## Tasks

- [x] Add access/evidence fields and semantic rules to the literature registry and JSON Schema.
- [x] Extend the paper CLI to record access outcomes and block `read` without full text.
- [x] Add regression tests for accessible, paywalled, and incomplete-note cases.
- [x] Document autonomous-agent boundaries and the full-text escalation protocol.
- [x] Fix stale registry paths, update handoff/memory, and regenerate manifests.
- [x] Run full validation, update PR #5, and leave a clean cross-chat handoff.

## Done when

- [x] An inaccessible paper remains `screened`, is marked `full_text_required`, and causes the handoff to request user-supplied authorized full text.
