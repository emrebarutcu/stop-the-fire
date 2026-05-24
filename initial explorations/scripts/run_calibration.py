#!/usr/bin/env python3
"""Run the calibration experiment: Max Degree strategy, density=0.30, n in {10, 30, 100}."""

from calibration.runner import CalibrationConfig, run_calibration, print_summary
from engine.strategies import MaxDegreeStrategy

config = CalibrationConfig(
    density=0.30,
    vertex_counts=[15, 20, 25],
    n_runs=30,
    strategy=MaxDegreeStrategy(),
)

print(f"Running calibration: {config.strategy.name}")
print(f"  density = {config.density}")
print(f"  vertex counts = {config.vertex_counts}")
print(f"  runs per config = {config.n_runs}")

df = run_calibration(config)
print_summary(df, input_density=config.density)

print(f"CSV saved to: {config.output_dir / f'{config.strategy.name}_d{config.density}.csv'}")
