# Explain RescueRoute with confidence

This project was created with AI assistance under Abhijith's direction. Use these exercises to build your own understanding. The code, tests and recorded experiments support the implementation; they do not automatically establish independent authorship or operational experience.

## Start with the human problem

A coordinator has boxes of food, several vans and pantries that accept deliveries during particular hours. A route that looks short on a map may overfill a van or arrive after a pantry closes. The system has to explain which deliveries fit, which do not, and why.

Our prototype models one depot with all boxes loaded at the start. It shows fictional pantry locations, per-van routes and unloading times. It never claims that real meals were delivered.

## The algorithms

**Brute force:** list all possible orders for one van, simulate each route and retain the shortest feasible one. With eight stops there are 40,320 orders; adding one stop multiplies the work by nine. The exact solver is intentionally bounded and CLI-only.

**Greedy baseline:** choose the nearest next stop that still fits the vehicle's capacity, delivery window and return deadline. It is fast and understandable, but an early choice can produce later detours or strand a feasible delivery.

**2-opt:** reverse a segment of a route. In an unconstrained route this often removes crossing paths; here every candidate must also satisfy the schedule. Shorter geometric distance alone is insufficient.

**Relocation:** remove a stop from one van and insert it at a feasible point in another van's route. This can reduce duplicated travel. The implementation rechecks capacity, windows and return time for both routes.

**Stopping rule:** accept the best valid distance improvement in each pass, up to eight passes. Stop early if no move helps. This bounds computation and preserves a valid plan, but can stop at a local optimum.

## Why the measurements are meaningful

The distance experiment serves the exact same 480 deliveries in both variants across 20 fixed scenarios. The 18.7% figure is computed from total modelled kilometres, not the average percentage and not an estimate of profit.

The runtime experiment uses ten smaller eight-stop cases so the exact optimum can be computed. Median runtime fell from about 257 ms to 0.78 ms (99.7% less time). The heuristic matched the optimum in all ten, but that is an observation on those cases, not a mathematical guarantee.

The full [report](benchmarks/README.md) includes unrounded numbers, all cases, scripts, source revision, environment and limitations. Do not generalize straight-line distance to actual traffic, fuel cost, emissions or deliveries completed in a real business.

## Systems questions an interviewer may ask

**How do retries avoid duplicate records?** A caller provides an idempotency key. SQLite stores one record per key, together with a hash of the normalized scenario. Identical replays return the stored comparison; changed payloads using that key are rejected. Concurrent calls may compute twice but persist one result.

**Why store the input with the plan?** A saved plan is an immutable snapshot. Later changes to a scenario must not silently change what an earlier route result meant.

**What does independent verification add?** A separate auditor recomputes route distance and times and checks every constraint without using the planner's schedule function. A shared algorithm defect is less likely to survive than if the solver merely asserted its own output was correct.

**Why no map provider?** The project isolates planning and constraint logic using synthetic coordinates. Real operations need a road travel-time matrix, routing data rights, traffic assumptions, geocoding validation and a human dispatcher review.

**What if a delivery is unassigned?** An individually impossible stop can be explained by capacity or timing. Otherwise the UI explicitly says the greedy baseline did not fit it; it does not claim that no feasible plan exists. The optimization preserves the served set for a fair distance comparison.

## Practice in order

1. Trace the one-stop API example in `docs/API.md` by hand. Calculate travel time, waiting, unloading and return.
2. Explain the crossing-route test and draw why a segment reversal helps.
3. Reproduce the two benchmark scripts and calculate the percentages from your own output.
4. Create a case where the greedy route fails to serve a stop that another assignment could serve.
5. Add a swap move or a different initial assignment and compare every original scenario before adding new ones.
6. Measure quality and runtime as the pass limit changes. Describe the curve rather than choosing only its best-looking point.
7. Explain what would be needed for real dispatch: authentication, access controls, rate limits, retention, monitoring, road data and operational review.
