# Two comparisons, two different questions

Measured October 18, 2026 on Darwin arm64, Python 3.12.14. All data is synthetic. Source revision and every case are retained in the raw JSON files. Neither experiment measures road mileage, actual deliveries, fuel, profit or user adoption.

## 1. Can better planning shorten the same delivery day?

Compare nearest-feasible greedy routing with bounded 2-opt and cross-vehicle relocation. Both use the same 24 stops, four vans, 30-box vehicle capacity, six-hour shift, 30 km/h modelled speed and unloading windows.

All seeds **0–19** are included, with no selection of only successful cases. Across 20 days, both variants served all **480 deliveries**. The independent auditor checked coverage, capacity, schedule feasibility, return time and distance on every result.

| Metric | Baseline | Improved |
|---|---:|---:|
| Total modelled distance over 20 days | 3,566.19 km | 2,898.83 km |
| Deliveries served | 480 | 480 |
| Scenarios with a distance improvement | — | 20 of 20 |

**Aggregate distance reduction: 18.71%.** Formula: `(3566.1865 − 2898.8296) / 3566.1865 × 100`. The median per-scenario reduction is 19.67%; it is a different statistic. The resume uses the aggregate 18.7% figure. Local median calculation time for the complete baseline-plus-improvement comparison was 12.44 ms per scenario, but this is not an HTTP load test.

[Raw multi-vehicle results](results.json) · [Reproduction script](compare.py)

## 2. How much computation does a heuristic save versus brute force?

The exact reference enumerates every ordering of **eight stops for one vehicle**: `8! = 40,320` possibilities per case. The faster method builds a nearest-feasible route and improves it with 2-opt. Both evaluate identical distance, service-time and return constraints.

All seeds **0–9** are included. Every case has broad delivery windows, ample capacity and a six-hour shift, so all eight deliveries are feasible. Three paired timing trials per case alternate execution order. Timing includes the whole call; heuristic time includes both constructing the baseline and optimizing it. The summary is the median of the ten per-case median runtimes.

| Metric | Exact brute force | Heuristic |
|---|---:|---:|
| Median calculation time | 257.1929 ms | 0.7849 ms |
| Runtime ratio | 327.70× | 1× |
| Cases matching the exact optimum | 10 | 10 |
| Maximum observed distance gap | — | approximately 0% (floating-point tolerance) |

**Runtime reduction: 99.6948%, rounded to 99.7%.** This shows a speed/quality tradeoff evaluated on ten small fixtures. Matching the optimum here does not establish a guarantee on unseen cases, tighter windows or multiple vehicles. Exhaustive search remains exact for this bounded single-vehicle model; the heuristic is not exact.

The case generator, exact enumeration and all paired timings are public. The baseline contains no sleeps or deliberately expensive unrelated work. At eight stops, even brute force is usable; its factorial growth is why it is restricted to eight stops and kept out of the web API.

[Raw exact/heuristic results](brute-force-results.json) · [Reproduction script](brute_force.py)

## Run both experiments

From the environment described in the root README:

```sh
.venv/bin/python benchmarks/compare.py
.venv/bin/python benchmarks/brute_force.py
```

The scripts replace their local result JSON files with the new machine's measurements. Commit a new dated result if publishing a later experiment; preserve the earlier evidence in Git history. Values vary with processor, background load and software versions. The timing trials are short local experiments, not confidence intervals or production capacity guarantees.

## What to say in an interview

“On a fixed set of 20 synthetic delivery days, route improvement reduced total modelled distance 18.7% without losing deliveries or violating constraints. Separately, I compared an exact eight-stop enumerator with the heuristic: median time fell from 257 ms to 0.78 ms, with the same optimum on those ten fixtures. I would test more diverse data and use road travel times before applying it operationally.”
