"""VULCAN -- Value-of-information Utilization for Leaderboard-Conditioned Architecture search.

VULCAN is the budget plane of the architecture in the repository root: it sits *around* a pinned
kernel-generation loop and turns "make every kernel a bit faster" into "maximize the benchmark's
actual published objective under a fixed GPU budget".

The name labels this control plane; the trust plane is ``argus``.  Nothing in ``vulcan`` imports
the generation loop: the package is pure standard-library Python and is therefore validated on any
CPU.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "objective",
    "stats",
    "allocator",
    "portfolio",
    "kb_graph",
    "cluster",
    "precision_guard",
    "roofline",
    "calibration",
    "kb_hw_adapter",
    "curriculum",
    "supervisor",
]
