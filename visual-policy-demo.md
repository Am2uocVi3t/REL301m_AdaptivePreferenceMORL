# Visual policy replay - bounded presentation plan

Scope: replace the caption/slider-first presentation with native environment
sprites. No training, optimization, new paid review, final test, checkpoint lock,
method comparison, or scientific gate change.

Predeclared before rollout on 2026-10-17:
- LunarLander: first primary adaptive seed 20262001, saved steps 50k and 500k.
- Minecart: first remediation-v2 seed 20264011, saved steps 100k and 1M.
- One nominal-validation episode per checkpoint, same seed within environment:
  training-run validation base seeds 20000 and 670000 respectively.
- Select the existing validation preference nearest the simplex centre by squared
  Euclidean distance; ties use first index. No outcome-dependent selection.
- Greedy ensemble-mean inference; at most 1000 transitions per episode.
- Show both saved training stages side by side, actions and cumulative raw reward.
  This is a newly rendered replay, not original training footage, not an online
  learning run and not a MORL-versus-baseline performance estimate.
- Keep every trajectory including failure. No retries to find attractive scenes.
- Preserve the 12-page report; replace guide instructions for the new visual demo.

Verification: execute renderer, inspect actual frames, decode MP4s, validate trace
and input/output hashes, exercise skip-on-resume, run project quality gate.
Browser playback must remain explicitly unverified if local-file access is blocked.
