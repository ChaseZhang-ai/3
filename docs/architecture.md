# System architecture

One generation loop, two control planes, three shared contracts. This document is the map; the
planes' own documents carry their internals.

```text
                       ┌──────────────────────────────────────────────┐
                       │  Objective  (one metric, one aggregation)     │
                       └───────────────┬──────────────────────────────┘
                                       │ scores every decision
        ┌──────────────────────────────┴───────────────────────────────┐
        │                                                              │
        │   BUDGET PLANE (vulcan/)                TRUST PLANE (argus/) │
        │   ─────────────────────                 ──────────────────── │
        │   allocation ──┐                        ┌── verification      │
        │   portfolio  ──┼──▶ candidate ────────▶─┼── attribution       │
        │   transfer   ──┘         ▲              └── hack detection    │
        │                          │                     │             │
        │                          └──── verdict ◀────────┘             │
        │                                    │                          │
        │                                    ▼                          │
        │                    ┌────────────────────────────┐             │
        │                    │ Mechanism memory           │             │
        │                    │ certified + refuted entries│             │
        │                    └────────────────────────────┘             │
        └──────────────────────────────────────────────────────────────┘
```

## 1. Responsibilities

The system answers two questions per round, and keeps them separate on purpose:

- **Where does the next unit of effort go?** (budget plane)
- **Is what came back real?** (trust plane)

Separating them matters because they fail independently. A search that is trusted but unfocused
spends its budget on saturated operators; a search that is focused but credulous promotes a
lower-precision shortcut. Merging the two into one "optimizer" hides which of the two is broken
when the score does not move.

## 2. Interfaces between the planes

The planes communicate through three small, explicit records rather than shared mutable state.
The names below match the Python modules in each plane.

### `Allocation` (budget → trust)

What to attempt, with what budget and against what target.

| field | meaning |
|---|---|
| `operator` | the operator/workload group under optimisation |
| `hours` | the effort budget for this attempt |
| `hypotheses` | the set of structurally distinct candidate architectures to try |
| `target_latency` | the latency that would realise the desired score |
| `provenance` | which mechanisms and measurements produced this plan |

Produced by `vulcan.allocator` / `vulcan.supervisor`; consumed by the generation loop and the
trust plane's bench protocol.

### `Candidate` (loop → trust)

A concrete implementation plus the conditions under which it was produced.

| field | meaning |
|---|---|
| `code_or_artifact` | the kernel or an opaque reference to it |
| `measurements` | paired timing samples, not a single number |
| `counters` | profiler features used for attribution and applicability predicates |
| `declared_precision` | input / accumulation / output precision the candidate actually uses |
| `claim` | the effect the candidate asserts, and on which workloads |

### `Verdict` (trust → budget, trust → memory)

The decision, with the evidence and the attribution that justify it.

| field | meaning |
|---|---|
| `decision` | `accept` / `reject` / `revert` |
| `reason` | the failing gate or the cleared gates, item by item |
| `confidence` | the paired-ratio interval and the noise floor it was compared against |
| `attribution` | where the gain came from (which change, measured how) |
| `memory_updates` | entries to certify or refute |

A candidate is promoted to the reference chain only on `accept`. `revert` writes a **negative**
memory entry so the same idea is not re-attempted under the same conditions.

## 3. The loop as a state machine

```text
  plan ──▶ propose ──▶ measure ──▶ verify ──┬─ accept ──▶ promote ──▶ retain ──▶ plan
                                            ├─ reject ──▶ retain(refuted) ─────▶ plan
                                            └─ revert ──▶ restore ──▶ retain(refuted) ─▶ plan
```

- **plan** uses the objective, the board data (if any), the device calibration, and mechanism
  memory to produce an `Allocation`.
- **propose** runs the generation loop over the allocation's hypotheses (a portfolio, not a single
  chain).
- **measure** times the candidate against the current reference in the same job; a paired
  measurement is the unit of evidence.
- **verify** applies correctness, the precision contract, adversarial probes, and the confidence
  gate.
- **promote / retain** updates the reference chain and mechanism memory.

The loop terminates when the confidence interval of the best candidate no longer clears the noise
floor, or when the budget is exhausted. A plateau is an estimate, not a proof.

## 4. The three shared contracts

### Objective

```
per workload   S_w = 1 / (1 + (T_w − T_SOL,w) / (T_b,w − T_SOL,w))
per operator   S_k = geomean over the operator's workloads of S_w
collection     S   = unweighted arithmetic mean over operators of S_k
```

Both planes call the same implementation (`vulcan.objective`) and the same anchors. If an
evaluation uses a different aggregation, it is not this objective and must say so.

### Acceptance

Correct **and** precision-contract-satisfying **and** confident. The order matters: a candidate
that fails correctness or the precision contract is rejected before its timing is even considered,
so a fast-but-wrong kernel can never look like progress.

### Mechanism memory

One store, two polarities, each entry carrying:

- the mechanism and the minimal recipe;
- **applicability conditions as executable predicates** over measured features, so retrieval is a
  filter rather than a suggestion;
- an evidence reference (a probe or a paired job);
- a polarity: `certified` (prescribe) or `refuted` (do not re-attempt under these conditions);
- an optional cross-architecture analogue, which is a *candidate* until re-probed.

The budget plane cites entries when planning; the trust plane writes them when deciding.

## 5. Admitting a new substrate

The planes are loop-agnostic. A new generation loop is admitted by satisfying five things, none of
which is specific to the loops currently used:

1. **A measurable interface.** It can produce a candidate and return paired measurements plus
   profiler counters for a declared operator/workload set.
2. **A judge, or the information to build one.** The correctness criterion, or the operator
   specification from which the trust plane builds and calibrates a judge.
3. **A pinned revision.** The exact commit is recorded in `scripts/bootstrap.sh` and vendored on
   demand; nothing is redistributed.
4. **A clock and a device contract.** How latency is measured (device time, cold cache, clock
   lock) and on which device the score is defined.
5. **An objective adapter.** A mapping from the loop's notion of a task to the shared objective's
   operator/workload structure.

A substrate that cannot state (3) and (4) cannot produce a reproducible number, so it cannot be
compared.

## 6. Invariants

These hold across both planes and are checked in tests, not just asserted in prose:

- The objective is implemented once; no second aggregation hides in a report.
- A promoted reference is never slower than its predecessor beyond the noise floor.
- A refuted mechanism carries the conditions under which it was refuted.
- A hardware claim has a written protocol and a status; it is `pending` until executed.
- A simulated number is labelled simulated at the point of use.

## 7. Where the code lives

| concern | budget plane | trust plane |
|---|---|---|
| objective | `vulcan/objective.py` | `docs/metric.md` (argus) |
| allocation | `vulcan/allocator.py` | — |
| portfolio | `vulcan/portfolio.py` | population search (`argus/src`) |
| precision | `vulcan/precision_guard.py` | verification gates (`argus/src`) |
| confidence | `vulcan/stats.py` | measurement protocol (`argus/docs/experiments.md`) |
| memory | `vulcan/kb_graph.py` | mechanism records (`argus/src`) |
| transfer | `vulcan/calibration.py` | — |
| orchestration | `vulcan/supervisor.py` | campaign driver (`argus`) |
