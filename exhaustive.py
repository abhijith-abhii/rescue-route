"""Small, exact single-vehicle reference; deliberately limited to 8 stops.

Enumerating every ordering is factorial work. This is a correctness/benchmark
reference, not an API endpoint and not a production-sized dispatch solver.
"""
from itertools import permutations
from planner import validate, schedule

def exact_route(payload):
    payload = validate(payload)
    if payload['fleet']['vehicles'] != 1 or len(payload['jobs']) > 8:
        raise ValueError('Exhaustive reference supports one vehicle and at most 8 stops')
    by_id = {j['id']: j for j in payload['jobs']}
    if sum(j['boxes'] for j in payload['jobs']) > payload['fleet']['capacity']:
        return {'route': None, 'orders_evaluated': 0}
    best = None
    count = 0
    for order in permutations(sorted(by_id)):
        result = schedule(order, by_id, payload['fleet'])
        count += 1
        if result and (best is None or result['distance_km'] < best['distance_km']):
            best = result
    return {'route': best, 'orders_evaluated': count}
