# English team guide and MORL glossary

Use this explanation with the current English report and inference demo. It
does not introduce a new slide deck, video, experiment or scientific claim.

## The project in one paragraph

Multi-objective reinforcement learning returns a reward vector instead of a
single score. This project trains policies that also receive a preference
vector, so the same network can express different trade-offs. It implements
preference-conditioned vector Q-learning with adaptive allocation signals and
separately declared PPO task-feasibility studies. The original comparison
failed its Minecart task qualification. Later PPO confirmations passed bounded
task gates. The demo exposes trained policies; adaptive-allocation superiority
remains unestablished.

## Roles recorded by the team

- **Le Nguyen Gia Hung:** introduce the problem and operate the live demo.
- **Huynh Quoc Viet:** explain the architecture, reward vectors and algorithms.
- **Ngo Hoai Nam:** explain experimental evidence, failure analysis and limits.
- **Lecturer:** Luu Giang Nam.

These are existing team responsibilities, not academic titles or a newly
approved presentation schedule.

## Technical glossary

| Term | Meaning in this project |
|---|---|
| MORL | Reinforcement learning with several reward components and potentially conflicting objectives. |
| Preference vector, `w` | Nonnegative objective weights summing to one; an input to the policy. |
| Linear scalarization | Combining a vector return with the preference using a weighted sum. The report uses fixed scales and discounting. |
| Pareto front | A set of mutually nondominated return vectors; improving one objective can require sacrificing another. |
| PCQN | This project's preference-conditioned vector Q-network. It is not the return/horizon-conditioned PCN algorithm. |
| Double DQN | Online action selection and target-network evaluation in the Bellman target; each masked head selects its own next action. |
| Masked heads | Multiple value heads over shared features, with replay masks. This is not a fully independent ensemble or calibrated uncertainty guarantee. |
| Credit assignment | Learning which earlier decisions contributed to delayed returns. Minecart diagnosis motivates this concern without establishing a unique cause. |
| PPO | A policy-gradient actor-critic method with a clipped policy-ratio objective. Its success here is not a universal superiority result. |
| PopArt | Critic normalization that preserves unnormalized value outputs when target statistics change. |
| GAE | An advantage estimator used by the Lunar-specific PPO implementation; do not attribute it to every Minecart PPO run. |
| Training seed | Random initialization/execution identity for an independently trained policy. |
| Environment seed | An evaluation case's initial randomness; several cases do not become several independent training replications. |
| Sampled inference | Draw an action from the actor's categorical probabilities. |
| Argmax inference | Choose the highest-probability action; the current demo uses this mode. |
| Hypervolume | A Pareto-set metric relative to a fixed reference point; it does not certify task competence by itself. |
| Qualification gate | A predeclared requirement that must pass before specified scientific actions can proceed. |
| Provenance | Source identities, protocol/checkpoint hashes, seeds, budgets and retained vectors linking a result to its execution. |

## Explain the research sequence

1. The original study asked whether difficulty, disagreement, coverage/recency
   and progress could improve allocation across preferences.
2. The primary PCQN block completed 30 jobs across two environments, three arms
   and five paired training seeds. It retained 28,800 validation episodes.
3. Minecart's two ore objectives were zero across all 14,400 primary validation
   episodes. This blocked the comparative qualification and final-test workflow.
4. Separate diagnosis/remediation studies preserved negative outcomes. They do
   not establish that all value-based methods fail or isolate a single cause.
5. Later declared PPO studies demonstrated task competence under specific
   nominal profiles: three Minecart confirmation seeds and two prospective
   Lunar confirmation seeds. The Lunar pilot is separate.
6. The English demo loads fixed exported actors; sliders change their inputs.
   There is no retraining, optimizer step or final-test evaluation in the demo.

Use the [Minecart results](../../research/ONPOLICY_CONFIRMATION_RESULTS_20261103.md)
and [Lunar results](../../research/LUNAR_CONFIRMATION_RESULTS_20261103.md) for
exact budgets, seed-level results and uncertainty limits.

## Common questions and defensible answers

**What is the contribution?**
An auditable implementation and investigation, retained negative task evidence,
and separately declared bounded PPO task confirmations. The project does not
claim a new PPO algorithm or established adaptive-allocation benefit.

**Why did the value-learning study fail?**
The observed Minecart policies did not deliver ore in the audited validation
block. Recorded diagnostics suggest sparse/delayed credit and backbone issues.
The later PPO result changes several conditions and budgets, so it cannot prove
that one component alone caused recovery.

**Does 10/10 mean the policy always succeeds?**
No. It is the observed count on specified cases at a declared final checkpoint.
Training seeds, evaluation cases and inference modes must remain distinct.
Unseen preferences and shifted dynamics need their own evidence.

**Does moving a slider train the model?**
No. It changes the preference input to frozen weights. The pending/live labels
explain when the input takes effect and whether episode history is retained.

**Why do some preferences fail or look similar?**
Conditioning does not guarantee that every trade-off was learned. Some corner
weights also express different goals, such as fuel preservation rather than
landing or ore delivery. Show the behavior and use the appropriate utility/task
definition; do not hide failed cases or substitute a better-looking model.

**What remains incomplete?**
The original adaptive comparison, predictive-signal analysis, complete target
ablations and qualified dynamics-generalization study. Final-test gates remain
locked. The English report states these limitations explicitly.

## Before demonstrating

Read the [English demo walkthrough](../../../demo/interactive/README_EN.md),
confirm the displayed checkpoint/seed and use a single controlling browser tab.
Keep the local Python server running during the demonstration. Stop it with
Ctrl+C afterward. Use the report's evidence tables for conclusions, not the
appearance of an individual animation.
