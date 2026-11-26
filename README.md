<div align="center">

# A self-improving architecture for agentic GPU kernel generation

**One loop, two coupled control planes — verification (ARGUS) and budget allocation (VULCAN).**

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](#quick-start)
[![CPU tests](https://img.shields.io/badge/CPU%20tests-147%20passing-brightgreen.svg)](#what-is-validated-today)
[![Hardware](https://img.shields.io/badge/Hardware-protocol%20written-yellow.svg)](docs/evaluation.md)
[![Target](https://img.shields.io/badge/Target-SOL--ExecBench-black.svg)](vulcan/docs/LEADERBOARD_ANALYSIS.md)

<!-- Diagrams are served via jsDelivr (gcore mirror) because raw.githubusercontent.com is
     unreachable on some networks; the files live in docs/images/ and the URL is pinned to a
     commit — bump the SHA in both image URLs when the figures change. -->
<img src="https://gcore.jsdelivr.net/gh/zixinzenith/agentic-kernel-studies@c35400c/docs/images/architecture-planes.png" width="740" alt="One objective scoring a budget plane (VULCAN) and a trust plane (ARGUS) that exchange candidates for verdicts and attributions, with a shared mechanism memory of certified and refuted mechanisms.">

</div>

An agent that writes GPU kernels can be made to improve its own process — but only if two things
hold at once. **The gains have to be real** (not a lower-precision shortcut, not a benchmark
artefact), and **the effort has to go where the objective can still move** (not into operators
already pinned at the hardware ceiling). Most agentic kernel systems optimise one of these and
assume the other.

This repository treats them as a single architecture. A kernel-generation loop is wrapped in two
coupled **control planes**:

- **ARGUS — the trust plane.** Decides what a candidate must prove before it is believed, what a
  judge should be told, and how to search so that a claimed gain is attributable rather than
  accidental.
- **VULCAN — the budget plane.** Decides which operators and which architecture hypotheses receive
  the next unit of GPU time, when a gain exceeds measurement noise, and how a result measured on
  one device transfers to the device the score is defined on.

They share one objective, one acceptance contract, and one mechanism memory. A candidate the
budget plane proposes is promoted only if the trust plane certifies it; what is certified becomes
memory that steers the next allocation. The loop is closed — **observe → allocate → search →
verify → promote → retain** — and every arrow is scored by the same function.

## Why this exists

Self-improving kernel agents fail in three characteristic ways, and each is a control problem,
not a model problem:

1. **Apparent improvement.** A candidate passes an output check while quietly lowering internal
   precision, caching an answer, or exploiting the stopwatch. The reported gain is real to the
   metric and false to the operator.
2. **Misallocated effort.** When an objective weights operators differently from how effort is
   spent, an agent polishes the operators that are already saturated. The score barely moves and
   the budget is gone.
3. **Knowledge that does not accumulate.** Each run rediscovers the same mechanisms and repeats
   the same failed ideas, because what was learned was never certified and never stored.

The trust plane addresses (1) and (3); the budget plane addresses (2) and (3). Neither is
sufficient alone: a perfectly verified search still wastes its budget, and a perfectly allocated
search still promotes shortcuts.

## The architecture

### The loop

A campaign is a sequence of decisions about *what to try next* and *whether to keep it*.

<p align="center"><img src="https://gcore.jsdelivr.net/gh/zixinzenith/agentic-kernel-studies@c35400c/docs/images/control-loop.png" width="840" alt="Closed loop: an operator set enters the budget plane, which proposes candidate architectures and implementations; the trust plane returns a verdict and attribution; certified mechanisms, refuted ideas and the sealed reference chain feed back through mechanism memory."></p>

Each round writes two kinds of state: an **allocation** (which operator, how many hours, which
architecture hypotheses, what latency target) and a **verdict** (accepted, rejected, reverted,
with the evidence that decided it). Memory closes the loop across rounds and across operators.

### Two control planes

| | **ARGUS** — trust | **VULCAN** — budget |
|---|---|---|
| question | is the gain real, and what must be verified? | where should effort go, and which architecture? |
| inputs | candidate kernel, reference, profiler counters, judge spec | operator set, board data, device calibration, mechanism memory |
| outputs | accept / reject / revert + attribution | allocation, architecture portfolio, latency targets |
| core artefacts | verification gates, reward-hack lab, attribution records, population search | objective algebra, allocator, portfolio, transfer calibration, precision contract |
| read first | [`argus/README.md`](argus/README.md) | [`vulcan/README.md`](vulcan/README.md) |

**Trust plane (ARGUS).** Verification is treated as a first-class object: gates are specified,
tested against adversarial kernels, and *told* to the judge rather than left implicit. A population
search replaces a single greedy chain so a lucky sample cannot be mistaken for capability, and
every candidate carries an attribution of where its gain came from. The reward-hack lab is how the
gates are falsified — a gate that accepts a known shortcut is a bug. Design notes:
[`argus/docs/design/architecture.md`](argus/docs/design/architecture.md), findings:
[`argus/docs/design/findings.md`](argus/docs/design/findings.md).

**Budget plane (VULCAN).** The board's objective is a nonlinear function of latency, so "make it
faster" is the wrong instruction. VULCAN optimises the published score directly: it allocates
GPU-hours across operators by marginal score gain, runs a portfolio of structurally distinct
architecture hypotheses under successive halving, repairs the workloads that miss the
fast-enough threshold first, and converts measurements on a development device into predicted
scores on the scoring device. It also enforces the precision contract that keeps gains honest.
Design notes: [`vulcan/README.md`](vulcan/README.md),
[`vulcan/docs/IMPROVEMENTS.md`](vulcan/docs/IMPROVEMENTS.md).

### What couples them

- **One objective.** Both planes score with
  `S = 1/(1 + (T − T_SOL)/(T_b − T_SOL))`, geometrically over an operator's workloads and
  arithmetically over a collection. Stated once in [`argus/docs/metric.md`](argus/docs/metric.md).
- **One acceptance contract.** A candidate is promoted only if it is correct, satisfies its
  precision contract, and clears a paired-measurement confidence gate. The trust plane supplies
  the first two; the budget plane supplies the third.
- **One mechanism memory.** Certified mechanisms (with executable applicability conditions) and
  refuted ideas live in the same store; the next allocation is conditioned on both.

## Design principles

- **One metric, stated once.** If two documents disagree about the objective, the objective is not
  being optimised. The formula and its anchors are fixed in one place.
- **CPU-first validation.** Every claim about the reasoning stack has a GPU-free test. A claim
  about hardware is marked pending and carries the protocol that would settle it. Nothing is
  upgraded from "simulated" to "measured" by prose.
- **Simulation is labelled as simulation.** Synthetic landscapes, emulated kernels and projected
  scores say so, in the document where they appear.
- **No unmeasured numbers.** A gain is reported only from a paired measurement; a projection is
  labelled a projection wherever it appears.
- **Precision is a hard constraint.** A faster kernel that computes at lower precision is not a
  faster kernel; it is a different, wrong kernel that may pass a tolerance.
- **Substrates are pinned.** Each base loop is recorded at a commit so a result can be reproduced
  against exactly the code that produced it. Substrates are vendored on demand and not
  redistributed (see [Related work and provenance](#related-work-and-provenance)).

## What is validated today

| area | evidence | status |
|---|---|---|
| objective algebra and aggregation | round-trips, identity checks | ✅ CPU |
| budget allocator (exact DP vs greedy vs uniform) | randomised instances, liveness tests | ✅ CPU |
| architecture portfolio / successive halving | best-arm recovery under a controlled landscape | ✅ CPU |
| mechanism memory (predicates, negatives, cross-arch) | retrieval and persistence tests | ✅ CPU |
| precision contract and reward-hack scan | contract-violation and cheat fixtures | ✅ CPU |
| cross-device transfer calibration | known-map recovery, score round-trips | ✅ CPU |
| board analysis | live public API snapshot, 26 operators / 660 workloads | ✅ data |
| closed-loop orchestration vs baselines | synthetic landscape, seeded and reproducible | ✅ simulated |
| verification gates and hack detection | adversarial kernel population | ✅ CPU |
| real kernel speed, judge behaviour on hardware, clock-locked scoring | protocols in [`docs/evaluation.md`](docs/evaluation.md) and [`vulcan/docs/B300_RUNBOOK.md`](vulcan/docs/B300_RUNBOOK.md) | ⏳ hardware |

**147 CPU tests** across the two planes (53 + 94), plus the per-plane self-tests and the local
validation scripts. The GPU-dependent claims are listed as pending, not implied.

## Results so far

**Board analysis (public data, not our measurement).** The SOL-ExecBench FlashInfer-Bench
collection on B200 (evaluation stack v1.1) scores 26 operators / 660 workloads. Recovering the
scoring rule from the public API reproduces the published collection scores exactly, which makes
one thing visible: with an unweighted per-operator mean, headroom sits in the mid-scoring
operators, not the near-ceiling attention kernels. Taking the best public implementation per
operator would already exceed the current rank-1 score. The full table, the arithmetic and the
implications are in
[`vulcan/docs/LEADERBOARD_ANALYSIS.md`](vulcan/docs/LEADERBOARD_ANALYSIS.md).

**Orchestration A/B (synthetic landscape, seeded).** On a controlled synthetic GPU with hidden
per-architecture quality, the two budget-plane mechanisms are separable and additive:

| strategy | score after 200 GPU-hours | gain vs uniform |
|---|---|---|
| uniform hours, one architecture | 0.8815 | — |
| headroom-proportional hours | 0.8959 | +0.0144 |
| allocation only (exact DP) | 0.8939 | +0.0125 |
| portfolio only (successive halving) | 0.9186 | +0.0371 |
| **allocation + portfolio + curriculum** | **0.9250** | **+0.0436** |

These are properties of the orchestration under a **synthetic** ground truth, reproducible with
`--seed`; they are not hardware results. The hardware protocols that would turn them into
measurements are written down before any GPU time is requested.

## Quick start

Each plane is self-contained; nothing here needs a GPU to validate the reasoning.

```bash
# ── Trust plane ────────────────────────────────────────────────
cd argus
export PYTHONPATH=src
python3 -m argus.cli selftest
python3 -m argus.cli hacklab --seed 1        # which verification gate accepts which kernel
python3 -m argus.cli ab --seeds 6 --evals 40 # population search vs a greedy chain
bash scripts/local_validate.sh               # the above + 53 unit tests

# ── Budget plane ───────────────────────────────────────────────
cd ../vulcan
export PYTHONPATH=src
python3 -m vulcan selftest
python3 -m vulcan stats                      # headroom ranking of the board's operators
python3 -m vulcan plan --hours 200           # score-aware allocation + latency targets
python3 -m vulcan transfer --target best --ratio 1.8   # dev-device targets ↔ scoring-device score
python3 -m vulcan demo --hours 200 --seed 7  # the A/B table above
bash scripts/local_validate.sh               # the above + 94 unit tests
```

Requirements: Python ≥ 3.9 and the standard library for the budget plane; `numpy` and `pytest`
for the trust plane's suite. The GPU paths (a pinned base loop, a Blackwell device, a
clock-locked scoring harness) are documented in each plane's runbook and are **not** exercised by
the CPU tests.

## Repository layout

```text
docs/                 the shared architecture, evaluation contract, and related work
argus/                trust plane: verification, attribution, population search
  docs/               design notes, findings, experiments, the metric
  src/ tests/         implementation and its CPU suite
vulcan/               budget plane: allocation, portfolio, transfer, mechanism memory
  ARCHITECTURE.md     the base loop, the layer, and how they meet
  docs/               leaderboard analysis, improvement register, hardware runbook
  src/ tests/         implementation and its CPU suite
  data/               board snapshot (public per-workload latencies and scores)
  configs/ scripts/   strategy config, bootstrap and local validation
LICENSE               MIT
```

## How to read this repository

1. [`docs/architecture.md`](docs/architecture.md) — the system: planes, interfaces, artifacts, and
   how a new substrate is admitted.
2. [`docs/evaluation.md`](docs/evaluation.md) — the shared metric, the validation ladder
   (CPU → simulated → hardware) and the promotion rules.
3. [`argus/README.md`](argus/README.md) — the trust plane's questions and findings.
4. [`vulcan/README.md`](vulcan/README.md) — the budget plane's questions and findings.
5. [`docs/related-work.md`](docs/related-work.md) — what this builds on, what is new, and what it
   deliberately does not claim.

## Roadmap

- [ ] **Hardware validation.** Execute the written protocols: development on a Blackwell device,
  scoring on the benchmark's reference device at its clock, with the precision and confidence
  gates enforced. See [`vulcan/docs/B300_RUNBOOK.md`](vulcan/docs/B300_RUNBOOK.md).
- [ ] **Wire mechanism memory end-to-end.** Emit certified entries into the substrate's own
  knowledge-base format so the generation agents read them (adapter exists; needs a live run).
- [ ] **Online calibration.** Replace the planning prior on improvement rate with rates fitted
  from the campaign's own latency-vs-hours history.
- [ ] **Graph-level search.** Move from per-operator implementations to fusion decisions across
  neighbouring operators — the larger, riskier lever.
- [ ] **A second substrate for the budget plane.** The control planes are loop-agnostic; the next
  step is to run them over a different generation loop and check that the conclusions transfer.

## Related work and provenance

The architecture is deliberately **substrate-agnostic**: it is a pair of control planes around a
kernel-generation loop, not a kernel generator itself. The two loops used here are public systems
chosen because they differ in the property each plane stresses — one separates architectural
planning from coding and promotes accepted kernels into the next reference; the other is a compact
feedback loop driven by profiler counters. Running the same planes on two different loops is a
check on the claim, not a claim about either loop.

| substrate | what it contributes | pin |
|---|---|---|
| **ForgeKernel** (OpenBMB / Tsinghua, arXiv:2611.04998) | architecture-first milestones; sealed-reference self-evolution; probe-certified hardware knowledge base | `b2c8ae8` (2026-11-11), Apache-2.0 |
| **CudaForge** | compact coder/judge loop over hardware counters | `eaba693f`, see `argus/scripts/bootstrap.sh` |
| **SOL-ExecBench / FlashInfer-Bench** | the objective, the operator set, and the published anchors `T_b`, `T_SOL` | `a9fa0804` / `15618a67` |

These substrates are **vendored on demand at pinned commits and are not redistributed**; each
plane's `scripts/bootstrap.sh` records the exact revision, and [`vulcan/NOTICE`](vulcan/NOTICE)
records the license. What this repository adds is orthogonal to them: the trust plane's
verification-and-attribution machinery, and the budget plane's allocation, portfolio, transfer and
precision-contract logic.

The wider context: kernel benchmarks and datasets (KernelBench, TritonBench), agentic generators
(Astra, STARK, K-Search, CudaForge, JustGoal, KernelSeek), and evolutionary code search
(AlphaEvolve, FunSearch). The trust plane's premise — that reported gains need adversarial
verification — is consistent with recent critiques of reward hacking in kernel-generation
benchmarks; the budget plane's premise — that the published objective, not raw speedup, is what a
leaderboard rewards — follows directly from the scoring rule recovered in
[`vulcan/docs/LEADERBOARD_ANALYSIS.md`](vulcan/docs/LEADERBOARD_ANALYSIS.md). A fuller discussion,
including what is and is not claimed relative to each system, is in
[`docs/related-work.md`](docs/related-work.md).

## Limitations

- **Hardware claims are pending.** The GPU protocols are written, not yet executed; no kernel
  speedup in this repository is a hardware measurement.
- **Synthetic results are synthetic.** The orchestration A/B is a controlled landscape. It shows
  which mechanism moves the score and by how much *under that landscape*, not how much it will
  move on a real device.
- **Board data moves.** The leaderboard snapshot is dated and must be refreshed; ranks change.
- **Two substrates is evidence, not proof.** Agreement across two loops supports loop-agnosticism;
  it does not establish it for every generator.
- **Cost.** Hardware campaigns are GPU-hours and frontier-model usage; the runbooks state the
  budget shape before a resource request is made.

## License and acknowledgments

MIT for this repository; see [`LICENSE`](LICENSE). Each substrate keeps its own license and is not
redistributed — see [`vulcan/NOTICE`](vulcan/NOTICE) and each plane's `scripts/bootstrap.sh`.

This work builds on the public loops named above and on the benchmarks and tooling around them:
CUDA / CuTe DSL and CUTLASS, Nsight Compute, FlashInfer, and the SOL-ExecBench / FlashInfer-Bench
evaluators. Their authors' releases made the comparison possible.
