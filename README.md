# Agentic GPU kernel generation — two studies

A research workspace for one question: **can an agent that writes GPU kernels be made to
improve its own process, and what has to be true for that improvement to be real rather than
apparent?** It is not a single system. It holds two studies, each in its own folder, each a
reproduction of a different base loop plus a distinct question. Studying both is the point: a
claim about "agentic kernel optimization" should survive being checked against more than one
loop, and the two axes they examine — evaluation integrity and budget allocation — are
complementary rather than competing.

| folder | base system | the question it studies | status |
|---|---|---|---|
| [`argus/`](argus/README.md) | **CudaForge** — a Coder/Judge loop over profiler counters | What must a generator verify, what must its search respect, and what should its judge be told? | in this repository |
| `vulcan/` | **ForgeKernel** — architecture planning split from coding | How should a fixed budget be divided across operators and architecture hypotheses, and when is a gain real? | in this repository |

Both reproduce a different base on purpose. ForgeKernel separates architectural planning from
coding and promotes accepted kernels into the next reference; CudaForge is a compact loop with
hardware feedback. The same question asked of two very different loops is worth more than two
questions asked of one.

## Shared conventions

- **One metric, stated once.** Both studies report against the same scoring function —
  `S = 1/(1 + (T − T_SOL)/(T_b − T_SOL))`, geometric mean over an operator's workloads,
  arithmetic mean over a collection. `argus/docs/metric.md` states it and documents where the
  anchors come from.
- **CPU-first validation.** Every claim about the *reasoning* stack has a GPU-free test. A claim
  about hardware is marked as pending and carries the protocol that would measure it.
- **Simulation is labelled as simulation.** When a result comes from a synthetic landscape or
  emulated kernels, the document says which part of the experiment is real and which is not.
- **Pinned upstreams, vendored and gitignored.** Each study records the upstream commit it
  builds against, so a result can be reproduced against the same code.
- **No unmeasured numbers.** A gain is reported only from a paired measurement; a projected or
  synthetic number is labelled wherever it appears.

## Running a study

Each folder is self-contained; nothing needs a GPU to validate the reasoning.

```bash
# ARGUS
cd argus
export PYTHONPATH=src
python3 -m argus.cli selftest
python3 -m argus.cli hacklab --seed 1      # which verification gate accepts which kernel
python3 -m argus.cli ab --seeds 6 --evals 40
bash scripts/local_validate.sh             # the above + 53 unit tests

# VULCAN
cd vulcan
export PYTHONPATH=src
python3 -m vulcan selftest
python3 -m vulcan stats                    # headroom ranking of the 26 board kernels
python3 -m vulcan plan --hours 200         # score-aware budget allocation + latency targets
python3 -m vulcan transfer --target best --ratio 1.8   # B300 dev targets -> B200 scores
python3 -m vulcan demo --hours 200 --seed 7  # mock A/B of allocation vs portfolio
bash scripts/local_validate.sh             # the above + 94 unit tests
```

The planned hardware protocols are written down before any GPU time is requested:
[`argus/docs/experiments.md`](argus/docs/experiments.md).

## Where to read first

- [`argus/README.md`](argus/README.md) — research questions, findings, and the explicit table of
  what the simulator does and does not show.
- [`argus/docs/design/architecture.md`](argus/docs/design/architecture.md) — what is reproduced
  from the base loop and what is added.
- [`argus/docs/design/findings.md`](argus/docs/design/findings.md) — the findings and their
  current status.
- [`vulcan/README.md`](vulcan/README.md) — the same, for the ForgeKernel study: what is
  reproduced, what is added, and what is validated on CPU versus pending on hardware.
- [`vulcan/ARCHITECTURE.md`](vulcan/ARCHITECTURE.md) — the paper-to-code map of the reproduced
  loop and the reproduction procedure.
- [`vulcan/docs/LEADERBOARD_ANALYSIS.md`](vulcan/docs/LEADERBOARD_ANALYSIS.md) — the exact
  scoring rule recovered from the board's public API and where the headroom is.

## License

MIT; see [`LICENSE`](LICENSE). The upstreams each study builds on keep their own licenses and
are not redistributed here — each study pins its base's commit in its `scripts/bootstrap.sh`
(and, for `vulcan/`, in [`vulcan/NOTICE`](vulcan/NOTICE)).
