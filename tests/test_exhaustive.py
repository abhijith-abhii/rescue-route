import pytest
from exhaustive import exact_route
from planner import plan
from scenarios import scenario
from verification import audit

def small(seed=0,count=5):
    p=scenario(seed,count);p['fleet'].update(vehicles=1,capacity=200,shift_minutes=600)
    for job in p['jobs']:job.update(opens=0,closes=600)
    return p

def test_exact_enumerates_all_orderings_and_bounds_heuristic():
    p=small();exact=exact_route(p);result=plan(p)
    assert exact['orders_evaluated']==120
    assert exact['route']['distance_km'] <= result['optimized']['distance_km'] + 1e-9
    assert audit(result) and result['optimized']['served']==5

@pytest.mark.parametrize('payload',[scenario(0,9),scenario(0,4)])
def test_expensive_reference_bounded(payload):
    with pytest.raises(ValueError,match='one vehicle'):exact_route(payload)

def test_infeasible_exact_has_no_solution():
    p=small();p['fleet']['capacity']=1
    assert exact_route(p)=={'route':None,'orders_evaluated':0}
