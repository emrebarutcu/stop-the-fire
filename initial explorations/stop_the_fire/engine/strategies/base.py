from __future__ import annotations

from abc import ABC, abstractmethod

import networkx as nx

from ..models import VertexState


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def select_vertices(
        self,
        graph: nx.Graph,
        vertex_states: dict[int, VertexState],
    ) -> list[int]:
        """Return WHITE vertex IDs in preference order; engine takes the first ``protect_per_turn``."""
        ...
