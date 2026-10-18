"""Independent feasibility audit; does not call the planner's schedule function."""
import math

def audit(result):
    source = {j['id']: j for j in result['scenario']['jobs']}
    fleet = result['scenario']['fleet']
    served_sets = []
    for mode in ['baseline', 'optimized']:
        plan = result[mode]
        seen = []
        total_distance = total_minutes = 0.0
        for route in plan['routes']:
            assert len(route['ids']) == len(route['stops'])
            assert sum(source[i]['boxes'] for i in route['ids']) <= fleet['capacity']
            elapsed = length = 0.0
            x = y = 0.0
            for ident, stop in zip(route['ids'], route['stops']):
                assert ident == stop['id'] and ident in source
                job = source[ident]
                leg = math.sqrt((job['x']-x)**2 + (job['y']-y)**2)
                length += leg
                arrival = elapsed + leg / fleet['speed_kmh'] * 60
                start = max(arrival, job['opens'])
                elapsed = start + job['service_minutes']
                assert elapsed <= job['closes'] + 1e-7
                assert abs(stop['arrival'] - arrival) <= .011
                assert abs(stop['start'] - start) <= .011
                assert abs(stop['departure'] - elapsed) <= .011
                x, y = job['x'], job['y']
                seen.append(ident)
            length += math.sqrt(x*x+y*y)
            elapsed += math.sqrt(x*x+y*y) / fleet['speed_kmh'] * 60
            assert elapsed <= fleet['shift_minutes'] + 1e-7
            assert abs(length-route['distance_km']) < 1e-7
            assert abs(elapsed-route['minutes']) < 1e-7
            total_distance += length
            total_minutes += elapsed
        unassigned = [j['id'] for j in plan['unassigned']]
        assert len(plan['routes']) == fleet['vehicles']
        assert len(seen) == len(set(seen)) == plan['served']
        assert len(unassigned) == len(set(unassigned))
        assert set(seen).isdisjoint(unassigned)
        assert set(seen) | set(unassigned) == set(source)
        assert abs(total_distance-plan['distance_km']) < 1e-7
        assert abs(total_minutes-plan['vehicle_minutes']) < 1e-7
        assert plan['boxes'] == sum(source[i]['boxes'] for i in seen)
        served_sets.append(set(seen))
    assert served_sets[0] == served_sets[1]
    assert result['optimized']['distance_km'] <= result['baseline']['distance_km'] + 1e-7
    return True
