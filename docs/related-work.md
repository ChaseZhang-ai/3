# Related work and provenance

This document states plainly what the repository builds on, what it adds, and what it does not
claim. It is deliberately near the end of the reading order: the system is introduced on its own
terms first, and its relationship to prior work is explained here.

## 1. Substrates

The control planes are **loop-agnostic**. They wrap a kernel-generation loop; they are not one.
Two public loops are used because they differ in exactly the property each plane stresses, which
makes agreement between them evidence rather than repetition.

### ForgeKernel (OpenBMB / Tsinghua, arXiv:2611.04998, Apache-2.0)

A self-evolving kernel agent. It separates an **architecture agent** (which writes a milestone
curriculum of decisions and contracts) from a **coding agent** (which implements one decision at a
time), promotes every accepted kernel to the **next reference** so optimisation continues past the
best known implementation, and accumulates **probe-certified hardware mechanisms** in a knowledge
base shared across operators. On Hopper and Blackwell it reports matching or beating 18 of 22
expert-library kernels and all seven published kernels of three generation systems.

*Why it is a substrate here:* its separation of planning from coding and its reference-promotion
chain are the cleanest available setting in which to ask "where should the budget go?" — the
budget plane's question. Pin: `b2c8ae8` (2026-11-11).

### CudaForge (pinned `eaba693f`)

A compact coder/judge loop driven by hardware counters. Smaller and more homogeneous than
ForgeKernel, which makes it a good setting in which to ask "what must the judge be told, and what
must a candidate prove?" — the trust plane's question.

### Benchmarks

KernelBench and TritonBench provide operator suites; **SOL-ExecBench / FlashInfer-Bench** provides
the objective used here, with published per-workload anchors (`T_b`, `T_SOL`). The scoring rule,
its aggregation and its leaderboard are analysed in
[`../vulcan/docs/LEADERBOARD_ANALYSIS.md`](../vulcan/docs/LEADERBOARD_ANALYSIS.md). Pins:
`a9fa0804` (SOL-ExecBench), `15618a67` (FlashInfer-Bench).

**Provenance.** Substrates are cloned on demand at the pinned commits into a gitignored `vendor/`
directory and are **not redistributed**. Each plane's `scripts/bootstrap.sh` records the revision
and `vulcan/NOTICE` records the license. The code in `argus/` and `vulcan/` that is not the
vendored tree is original to this repository.

## 2. The surrounding literature

The repository sits at the intersection of three lines of work.

**Agentic kernel generation.** Astra and STARK combine multi-agent collaboration with search and
profiling; K-Search co-evolves a world model with the search; CudaForge and KernelAgent use
hardware feedback cheaply; JustGoal argues a general agent can beat specialised scaffolding;
KernelSeek argues that *direction* matters more than *tools*; GEAK targets Triton on AMD. The
recurring open question is not "can an agent write a kernel" but "when should a gain be believed,
and where should the next hour go" — which is what the two planes isolate.

**Verification and reward hacking.** Recent critiques of kernel-generation benchmarks report that
reported speedups can be artefacts of tolerant checkers, host-bound timing, or precision
substitution. The trust plane takes this as the primary threat model rather than a caveat: gates
are specified, falsified against a population of known-bad kernels, and only then trusted.

**Budgeted search and knowledge reuse.** Evolutionary code search (AlphaEvolve, FunSearch) shows
LLM-driven search can beat hand-tuned heuristics when a fast evaluator exists; knowledge-reuse
systems (KernelClaw, KLineage) show that prior findings can be retained. The budget plane makes
the allocation explicit and score-aware, and makes retention *conditional* — certified or refuted,
with executable applicability predicates.

## 3. What this repository adds

Relative to the substrates and the systems above, the contribution is the pair of control planes
and the contracts between them:

- **Trust plane (ARGUS).** Verification as a first-class, falsifiable object; a reward-hack lab
  that tests the gates against deliberately wrong kernels; attribution of a gain to a change;
  population search instead of a single greedy chain, so a lucky sample is not read as capability.
- **Budget plane (VULCAN).** The published objective optimised directly, an exact score-aware
  allocation of hours across operators, a portfolio of structurally distinct architecture
  hypotheses under successive halving, explicit repair of the workloads missing the fast-enough
  threshold, a hard precision contract, and a calibrated transfer from a development device to the
  device on which the score is defined.
- **The loop.** One objective, one acceptance contract, one mechanism memory with both certified
  and refuted entries — so what one plane learns changes what the other does next.

None of this is a new base model and none of it is a new kernel generator; it is the control layer
around a generator.

## 4. What is not claimed

- **No hardware results yet.** Every GPU claim is `pending` and carries a written protocol. The
  synthetic orchestration results say how the mechanisms behave under a controlled landscape, not
  on silicon.
- **No claim to surpass expert kernels** on this repository's evidence; that is the substrate's
  published result, not ours.
- **No claim of independence from the substrates.** They are used openly and pinned; the
  contribution is what is built around them.
- **No claim of generality beyond two loops.** Agreement across two substrates supports
  loop-agnosticism; it does not prove it. Admitting a third substrate is a roadmap item with an
  explicit checklist in [`architecture.md`](architecture.md) §5.

## 5. Attribution

Ideas drawn from prior work are attributed to it here and in the per-plane documents. Any error in
attribution is ours and should be reported as an issue.
