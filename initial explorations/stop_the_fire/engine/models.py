from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VertexState(Enum):
    WHITE = "white"
    RED = "red"
    GREEN = "green"


@dataclass
class GameState:
    turn: int
    vertex_states: dict[int, VertexState]
    protected_this_turn: list[int]
    burned_this_turn: list[int]


@dataclass
class Metrics:
    K: int
    Y: int
    B: int
    K_over_Y: float
    K_over_B: float
    Y_over_B: float

    @classmethod
    def from_state(cls, vertex_states: dict[int, VertexState]) -> Metrics:
        K = sum(1 for s in vertex_states.values() if s == VertexState.RED)
        Y = sum(1 for s in vertex_states.values() if s == VertexState.GREEN)
        B = sum(1 for s in vertex_states.values() if s == VertexState.WHITE)
        return cls(
            K=K,
            Y=Y,
            B=B,
            K_over_Y=K / Y if Y > 0 else float("inf"),
            K_over_B=K / B if B > 0 else float("inf"),
            Y_over_B=Y / B if B > 0 else float("inf"),
        )


@dataclass
class GameResult:
    graph_seed: int
    n_vertices: int
    density: float
    strategy_name: str
    total_turns: int
    states: list[GameState]
    metrics: Metrics
