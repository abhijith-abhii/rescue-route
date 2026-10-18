"""Capacity and time-window constrained food-delivery planning.

Coordinates are fictional kilometres on a flat grid, not road distances.
The optimizer is a bounded deterministic heuristic, not an exact VRP solver.
"""
from __future__ import annotations
import math

DEPOT = (0.0, 0.0)

def number(value, name, low, high, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a number')
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}')
    if integer and int(value) != value:
        raise ValueError(f'{name} must be an integer')
    return int(value) if integer else float(value)

def validate(payload):
    if not isinstance(payload, dict) or set(payload) != {'jobs', 'fleet'}:
        raise ValueError('Provide jobs and fleet')
    fleet = payload['fleet']
    if not isinstance(fleet, dict) or set(fleet) != {'vehicles', 'capacity', 'shift_minutes', 'speed_kmh'}:
        raise ValueError('Provide vehicles, capacity, shift_minutes and speed_kmh')
    fleet = {key: number(fleet[key], key, *bounds, integer=True) for key, bounds in {
        'vehicles': (1, 6), 'capacity': (1, 200), 'shift_minutes': (30, 600), 'speed_kmh': (5, 80)}.items()}
    if not isinstance(payload['jobs'], list) or not 1 <= len(payload['jobs']) <= 40:
        raise ValueError('Provide 1 to 40 deliveries')
    jobs = []
    for row in payload['jobs']:
        fields = {'id', 'name', 'x', 'y', 'boxes', 'opens', 'closes', 'service_minutes'}
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError('A delivery has missing or unsupported fields')
        if not isinstance(row['id'], str) or not row['id'].isascii() or not row['id'].isalnum() or not 1 <= len(row['id']) <= 24:
            raise ValueError('Delivery IDs must be 1–24 ASCII letters or digits')
        if not isinstance(row['name'], str) or not 1 <= len(row['name'].strip()) <= 80:
            raise ValueError('Delivery names must contain 1–80 characters')
        job = {'id': row['id'], 'name': row['name'].strip()}
        for key, bounds in {'x': (-25, 25), 'y': (-25, 25), 'boxes': (1, 200), 'opens': (0, 600), 'closes': (0, 600), 'service_minutes': (1, 30)}.items():
            job[key] = number(row[key], key, *bounds, integer=key not in ['x', 'y'])
        if job['opens'] + job['service_minutes'] > job['closes']:
            raise ValueError('Delivery window must allow unloading time')
        jobs.append(job)
    if len({j['id'] for j in jobs}) != len(jobs):
        raise ValueError('Delivery IDs must be unique')
    return {'jobs': jobs, 'fleet': fleet}

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def schedule(ids, by_id, fleet):
    """Return full feasible route including depot return, or None."""
    boxes = sum(by_id[i]['boxes'] for i in ids)
    if boxes > fleet['capacity']:
        return None
    point = DEPOT
    elapsed = km = waiting = 0.0
    stops = []
    for ident in ids:
        job = by_id[ident]
        target = (job['x'], job['y'])
        leg = distance(point, target)
        arrival = elapsed + 60 * leg / fleet['speed_kmh']
        start = max(arrival, job['opens'])
        departure = start + job['service_minutes']
        if departure > job['closes'] + 1e-9:
            return None
        waiting += start - arrival
        stops.append({'id': ident, 'arrival': round(arrival, 2), 'start': round(start, 2), 'departure': round(departure, 2)})
        elapsed = departure
        km += leg
        point = target
    back = distance(point, DEPOT)
    elapsed += 60 * back / fleet['speed_kmh']
    km += back
    if elapsed > fleet['shift_minutes'] + 1e-9:
        return None
    return {'ids': list(ids), 'stops': stops, 'distance_km': km, 'minutes': elapsed, 'waiting_minutes': waiting, 'boxes': boxes}

def greedy(jobs, fleet):
    """Nearest feasible next stop, vehicle by vehicle; deterministic ties."""
    by_id = {j['id']: j for j in jobs}
    remaining = set(by_id)
    routes = []
    for _ in range(fleet['vehicles']):
        route = []
        while remaining:
            point = (by_id[route[-1]]['x'], by_id[route[-1]]['y']) if route else DEPOT
            candidates = sorted(remaining, key=lambda i: (distance(point, (by_id[i]['x'], by_id[i]['y'])), i))
            choice = next((i for i in candidates if schedule(route + [i], by_id, fleet) is not None), None)
            if choice is None:
                break
            route.append(choice)
            remaining.remove(choice)
        routes.append(route)
    return routes, sorted(remaining)

def improve(initial, by_id, fleet, passes=8):
    """Best-improvement 2-opt + inter-vehicle relocation, with feasibility checks.

    Preserve the served set so distance comparisons cannot hide dropped deliveries.
    """
    routes = [r[:] for r in initial]
    accepted = 0
    evaluated = 0
    for _ in range(passes):
        current = [schedule(r, by_id, fleet) for r in routes]
        best_gain = 1e-8
        best = None
        for index, route in enumerate(routes):
            for a in range(len(route) - 1):
                for b in range(a + 1, len(route)):
                    candidate = route[:a] + route[a:b + 1][::-1] + route[b + 1:]
                    result = schedule(candidate, by_id, fleet)
                    evaluated += 1
                    gain = current[index]['distance_km'] - result['distance_km'] if result else -1
                    if gain > best_gain:
                        best_gain, best = gain, {index: candidate}
            for position, ident in enumerate(route):
                source = route[:position] + route[position + 1:]
                source_result = schedule(source, by_id, fleet)
                if source_result is None:
                    continue
                for other, target in enumerate(routes):
                    if index == other:
                        continue
                    for insert_at in range(len(target) + 1):
                        candidate = target[:insert_at] + [ident] + target[insert_at:]
                        result = schedule(candidate, by_id, fleet)
                        evaluated += 1
                        gain = current[index]['distance_km'] + current[other]['distance_km'] - source_result['distance_km'] - result['distance_km'] if result else -1
                        if gain > best_gain:
                            best_gain, best = gain, {index: source, other: candidate}
        if best is None:
            break
        for index, route in best.items():
            routes[index] = route
        accepted += 1
    return routes, {'accepted_moves': accepted, 'evaluated_moves': evaluated, 'pass_limit': passes}

def summarize(routes, unassigned, by_id, fleet):
    details = []
    for i, route in enumerate(routes):
        result = schedule(route, by_id, fleet)
        if result is None:
            raise RuntimeError('Planner produced an infeasible route')
        details.append({**result, 'vehicle': i + 1})
    reasons = []
    for ident in unassigned:
        job = by_id[ident]
        reason = 'Exceeds one vehicle’s box capacity' if job['boxes'] > fleet['capacity'] else 'Cannot meet window or shift even as a solo trip' if schedule([ident], by_id, fleet) is None else 'Not assigned by the greedy baseline; another plan may serve it'
        reasons.append({'id': ident, 'reason': reason})
    return {'routes': details, 'unassigned': reasons, 'served': sum(len(r) for r in routes), 'boxes': sum(r['boxes'] for r in details),
            'distance_km': sum(r['distance_km'] for r in details), 'vehicle_minutes': sum(r['minutes'] for r in details)}

def plan(payload):
    payload = validate(payload)
    jobs, fleet = payload['jobs'], payload['fleet']
    by_id = {j['id']: j for j in jobs}
    baseline, unassigned = greedy(jobs, fleet)
    optimized, work = improve(baseline, by_id, fleet)
    before, after = summarize(baseline, unassigned, by_id, fleet), summarize(optimized, unassigned, by_id, fleet)
    reduction = 100 * (1 - after['distance_km'] / before['distance_km']) if before['distance_km'] else 0.0
    return {'scenario': payload, 'baseline': before, 'optimized': after, 'distance_reduction_percent': reduction, 'optimizer': work,
            'model': 'Fictional planar kilometres, constant travel speed, all boxes loaded at one depot. Not road navigation or a globally optimal solution.'}
