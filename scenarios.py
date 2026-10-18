"""Reproducible fictional community-pantry deliveries."""
import random

def scenario(seed=0, count=24):
    rng = random.Random(seed)
    jobs = []
    for i in range(count):
        opening = rng.choice([0, 0, 30, 60, 90])
        jobs.append({'id': f'P{i+1:02}', 'name': f'Demo pantry {i+1:02}', 'x': round(rng.uniform(-12, 12), 2), 'y': round(rng.uniform(-12, 12), 2),
                     'boxes': rng.randint(2, 6), 'opens': opening, 'closes': opening + 210, 'service_minutes': rng.randint(3, 7)})
    return {'jobs': jobs, 'fleet': {'vehicles': 4, 'capacity': 30, 'shift_minutes': 360, 'speed_kmh': 30}}

def presets():
    ordinary = scenario(0)
    tight = scenario(7)
    tight['fleet']['vehicles'] = 3
    tight['fleet']['shift_minutes'] = 240
    shortage = scenario(11, 30)
    shortage['fleet']['vehicles'] = 2
    shortage['fleet']['capacity'] = 25
    return [{'id':'community','name':'Community delivery day','description':'24 fictional pantries · 4 vans · timed deliveries','data':ordinary},
            {'id':'tight','name':'Short volunteer shift','description':'24 fictional pantries · 3 vans · four-hour shifts','data':tight},
            {'id':'shortage','name':'Capacity shortage','description':'30 fictional pantries · 2 vans · unassigned work stays visible','data':shortage}]
