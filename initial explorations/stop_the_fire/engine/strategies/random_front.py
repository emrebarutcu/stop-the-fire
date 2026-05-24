from __future__ import annotations

import random

import networkx as nx

from ..frontier import get_fire_front
from ..models import VertexState
from .base import Strategy


class RandomFrontStrategy(Strategy):
    """Uniformly random WHITE vertices on the fire front (stochastic baseline)."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    @property
    def name(self) -> str:
        return "random_front"

    def select_vertices(
        self,
        graph: nx.Graph,
        vertex_states: dict[int, VertexState],
    ) -> list[int]:
        candidates = list(get_fire_front(graph, vertex_states))
        if not candidates:
            return []
        self._rng.shuffle(candidates)
        return candidates
