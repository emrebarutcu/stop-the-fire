"""Wrapper around firefighter_engine.simulate that records per-turn full state.

The base engine only records (white,red,green) counts in SimResult.history,
which is enough for charts but not for animation. Here we capture, after each
turn, the set of vertices that turned RED and GREEN in that turn — small
diffs the frontend can replay.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

import networkx as nx

from firefighter_engine import (
    GREEN,
    RED,
    WHITE,
    Strategy,
    fire_front,
)


@dataclass
class TurnFrame:
    turn: int
    protected: List[int]   # vertices set GREEN this turn
    burned: List[int]      # vertices set RED this turn (spread)
    counts: Dict[str, int] # white / red / green totals after this turn


@dataclass
class RichSimResult:
    strategy: str
    n: int
    burned: int
    saved: int
    protected: int
    turns: int
    runtime_s: float
    fire_origin: int
    k: int
    frames: List[TurnFrame] = field(default_factory=list)
    final_state: Dict[int, str] = field(default_factory=dict)  # vertex id -> "WHITE"|"RED"|"GREEN"


def simulate_with_states(
    G: nx.Graph,
    fire_origin: int,
    strategy: Strategy,
    k: int = 2,
    max_turns: int = 1000,
) -> RichSimResult:
    state = {v: WHITE for v in G.nodes()}
    if fire_origin not in state:
        raise ValueError(f"fire_origin {fire_origin} is not a vertex of G")
    state[fire_origin] = RED

    frames: List[TurnFrame] = []
    t0 = time.perf_counter()
    turns = 0

    while True:
        front = fire_front(G, state)
        if not front:
            break

        candidates = strategy.select(G, state)
        seen = set()
        chosen: List[int] = []
        for v in candidates:
            if v in seen:
                continue
            seen.add(v)
            if state.get(v, RED) == WHITE:
                chosen.append(v)
                if len(chosen) >= k:
                    break
        for v in chosen:
            state[v] = GREEN

        new_red: List[int] = []
        for v in G.nodes():
            if state[v] != WHITE:
                continue
            for u in G.neighbors(v):
                if state[u] == RED:
                    new_red.append(v)
                    break
        for v in new_red:
            state[v] = RED

        turns += 1
        white_c = sum(1 for s in state.values() if s == WHITE)
        red_c = sum(1 for s in state.values() if s == RED)
        green_c = sum(1 for s in state.values() if s == GREEN)
        frames.append(
            TurnFrame(
                turn=turns,
                protected=list(chosen),
                burned=list(new_red),
                counts={"white": white_c, "red": red_c, "green": green_c},
            )
        )
        if turns >= max_turns:
            break

    runtime = time.perf_counter() - t0
    burned = sum(1 for s in state.values() if s == RED)
    protected = sum(1 for s in state.values() if s == GREEN)
    saved_white = sum(1 for s in state.values() if s == WHITE)

    name_map = {WHITE: "WHITE", RED: "RED", GREEN: "GREEN"}
    final_state = {int(v): name_map[s] for v, s in state.items()}

    return RichSimResult(
        strategy=strategy.name,
        n=G.number_of_nodes(),
        burned=burned,
        saved=saved_white + protected,
        protected=protected,
        turns=turns,
        runtime_s=runtime,
        fire_origin=fire_origin,
        k=k,
        frames=frames,
        final_state=final_state,
    )
