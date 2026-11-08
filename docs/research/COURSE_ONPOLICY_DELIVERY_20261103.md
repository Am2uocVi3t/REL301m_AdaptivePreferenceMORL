# Updated course report, demo and separate Lunar pilot

The group-template report at `paper/REL301m/main.tex` now includes the completed
three-seed Minecart confirmation, native task table and seed-level learning
curves. Historical failures are retained; stale n-step-running statements are
replaced with its completed negative outcome. The report does not claim
adaptive benefit or reliable Lunar landing. PDF13 pages compiled with existing
D-drive Tectonic; results pages visually inspected, no undefined references.

Current package: `outputs/REL301m_Course_Project_20261103` and matching ZIP.
PDF: `outputs/course-report-latex/REL301m_Course_Project_Report.pdf`.
Launcher `START_COURSE_DEMO.bat` now prefers this package.

Minecart uses final4M confirmation seed20264311, selected by lowest seed ID,
not observed score. Actor argmax inference; the other two portable confirmation
models are retained. The default panel uses balanced preference, the user panel
can change preference. Lunar remains the legacy100k PCQN with an explicit
unqualified-landing label while the new PPO pilot is a separate job.

Verification:20 real Minecart cases (two profiles x10 seeds), source actor and
portable inference action equivalence, raw reward sums and native rendering.
Actual Edge checks pass on an independently launched package outside repo cwd:
both environments, controls/live preference, PDF links, no page errors or
horizontal mobile overflow. No independent semantic-review PASS is claimed.
Evidence: `research/qualification/course_onpolicy_delivery_20261103.json` and
`research/qualification/onpolicy_course_demo_20261103.json`.

The demo website is inference only. Training progress remains in the native
PowerShell/Rich terminal. New Lunar specialist is separately frozen and must
pass its own native+100 AND pad-x criterion; Minecart success is not transferred
as a Lunar result. Its protocol is `LUNAR_PPO_SPECIALIST_V1.md`.
