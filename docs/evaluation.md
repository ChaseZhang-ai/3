# Evaluation contract

How this repository decides that something is true. The contract is shared by both planes; it is
what makes a number in one plane comparable to a number in the other.

## 1. The objective

```
per workload   S_w = 1 / (1 + (T_w − T_SOL,w) / (T_b,w − T_SOL,w))
per operator   S_k = geomean over the operator's workloads of S_w
collection     S   = unweighted arithmetic mean over the operators of S_k
```

- `T_b` — the benchmark's **scoring baseline** latency for that workload; `S = 0.5` at `T_b`.
- `T_SOL` — the **speed-of-light** latency for that workload; `S → 1` as a kernel approaches it.
- `Fast₁` — the separate fraction of workloads strictly faster than `T_b`.

The aggregation rule is not assumed: it is recovered from the benchmark's public data and checked
by reproducing the published collection scores from the published per-operator scores (see
[`../vulcan/docs/LEADERBOARD_ANALYSIS.md`](../vulcan/docs/LEADERBOARD_ANALYSIS.md)). If a
different aggregation is used anywhere, that is a bug in the reporting, not a variant.

Two consequences follow and are used by the budget plane:

- With an **unweighted** per-operator mean, the marginal value of effort is governed by an
  operator's remaining gap, not its workload count. Saturated operators are poor places to spend.
- `S` is nonlinear (convex) in latency, so a fixed *percentage* cut is not a fixed score gain.

## 2. The validation ladder

Every claim has a rung. Moving up a rung requires evidence, not confidence.

| rung | what it establishes | how |
|---|---|---|
| **CPU** | the reasoning stack is self-consistent | unit tests + self-tests, no GPU |
| **simulated** | the mechanism moves the objective under a controlled ground truth | seeded synthetic landscape; the landscape is described |
| **hardware** | the effect exists on a real device | paired measurement under the written protocol |

**Rules.**

- A claim is stated at its rung and never promoted by prose. "Projected", "synthetic" and
  "simulated" appear at the point of use.
- A result from the simulated rung is a statement about the orchestration, not about kernels. It
  says *which* mechanism helps and *how strongly under the landscape*, never how much it will help
  on silicon.
- A hardware claim carries its protocol (device, clock, cache state, timer, tolerance) and a
  status; it is `pending` until executed.

## 3. Promotion rules

A candidate becomes the next reference only when all three hold, in this order:

1. **Correctness.** It passes the operator's official or benchmark tolerance test on every input
   group, and the anti-delegation check (it must not call the reference).
2. **Precision contract.** It computes at or above the precision the operator's accuracy budget
   requires — input, accumulation and output precision — **even if its elementwise error currently
   passes**. A candidate that lowers internal precision to pass a tolerance is rejected here, not
   rewarded.
3. **Confidence.** The lower end of the paired-ratio bootstrap interval
   (`T_ref / T_cand`, candidate and reference timed in the same job) exceeds `1 + margin`, where
   `margin` is derived from the measured noise floor. Pairing cancels shared drift; the interval,
   not the median, decides.

A *change* with no attributable gain is reverted and recorded as **negative memory** with the
conditions under which it failed, so it is not re-attempted under the same trigger.

## 4. Precision, probes and hack detection

The precision contract is enforced, not hoped for, because the failure is silent: the ablation
literature records kernels that pass an output-error check while lowering internal precision.
Enforcement has three parts:

- **Contract.** A per-operator declaration of `input / accumulation / output` precision, with
  bit-exact required for pack/unpack/index operators. A narrower accumulation than the contract is
  a rejection.
- **Adversarial probes.** Input families that expose approximation shortcuts a tolerance hides:
  correlated keys, long memory, near-cancellation, wide dynamic range, zero-output guard, and
  `-inf` parity. These are run *before* a gain is believed.
- **Static scan.** Heuristics for the classic cheats — delegation to a reference op, returning
  the input unchanged, identity-based caching, in-kernel accumulation downcast, environment or
  L2-policy tampering. Advisory, and a hit must be cleared before submission.

The trust plane's **reward-hack lab** is the falsification side: it maintains a population of
deliberately incorrect kernels and checks that the gates reject them. A gate that accepts a known
shortcut is a bug in the gate.

## 5. Hardware protocol (written before resource is requested)

The scoring device is fixed by the benchmark and its clock is locked; development happens on a
different device. The protocol therefore has two stages and an explicit transfer step.

1. **Development.** Iterate on the development device. Two rungs of target are used: a local
   target from the transfer calibration (below) and the operator's own improvement curve.
2. **Transfer.** Fit `t_scoring ≈ a · t_dev + b` (or a ratio) on paired measurements. The cheapest
   anchor is the benchmark's own scoring baseline: its scoring-device latency is published, and the
   same baseline can be run on the development device. From the fit, convert a development
   measurement into a predicted score **with an interval**, and invert a score goal into a
   development latency target. With no paired measurements the map is an explicit assumption, never
   presented as a measurement.
3. **Scoring.** Re-measure the finalists on the scoring device at the benchmark's clock, pass the
   submission checklist, and submit. Details, commands and the checklist:
   [`../vulcan/docs/B300_RUNBOOK.md`](../vulcan/docs/B300_RUNBOOK.md).

Submission is gated on the predicted-interval: a candidate is submitted only if the interval's low
end clears the target, so a lucky dev measurement does not become a wasted submission.

## 6. Reporting

- **One metric.** Every table states its objective, or links to this document.
- **Paired or absent.** A gain is reported from a paired measurement; otherwise it is a projection
  and is labelled as one.
- **Statuses are explicit.** `✅ CPU`, `✅ simulated`, `✅ data`, `⏳ hardware`.
- **Negative results are results.** Refuted mechanisms are reported, not buried; they are what
  prevents the loop from repeating itself.

## 7. Current status

| claim class | rung | where |
|---|---|---|
| objective algebra, aggregation | ✅ CPU | `vulcan/tests/test_objective.py`, `argus/tests/test_objective.py` |
| allocation optimality vs baselines | ✅ simulated | `vulcan/tests/test_allocator.py`, `vulcan demo` |
| portfolio best-arm recovery | ✅ simulated | `vulcan/tests/test_portfolio.py` |
| precision contract, hack scan | ✅ CPU | `vulcan/tests/test_precision_guard.py` |
| verification gates vs shortcuts | ✅ CPU | `argus` tests + `argus.cli hacklab` |
| transfer calibration | ✅ CPU | `vulcan/tests/test_calibration.py` |
| board scoring rule | ✅ data | `vulcan/data/`, `scripts/fetch_board.py` |
| kernel speed on silicon | ⏳ hardware | protocol in §5 |
| judge behaviour on hardware | ⏳ hardware | `argus/docs/experiments.md` |
