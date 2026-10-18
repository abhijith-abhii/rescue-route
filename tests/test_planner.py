import copy
import pytest
from planner import plan, validate, schedule, improve
from scenarios import scenario, presets
from verification import audit

@pytest.mark.parametrize('seed', range(6))
def test_feasible_same_deliveries_nonincreasing_distance(seed):
    result = plan(scenario(seed))
    assert audit(result)
    assert result['optimizer']['accepted_moves'] <= 8

def test_deterministic():
    payload = scenario(3, 8)
    assert plan(payload) == plan(payload)

def test_capacity_shortage_visible():
    result = plan(presets()[2]['data'])
    assert audit(result) and result['optimized']['unassigned']
    assert result['optimized']['boxes'] <= 50

def test_time_window_waiting_and_return():
    job = dict(id='A', name='Demo', x=3, y=4, boxes=2, opens=30, closes=40, service_minutes=5)
    fleet = dict(vehicles=1, capacity=10, shift_minutes=60, speed_kmh=30)
    result = schedule(['A'], {'A': job}, fleet)
    assert result['distance_km'] == 10 and result['minutes'] == 45
    assert result['waiting_minutes'] == 20 and result['stops'][0]['start'] == 30
    assert schedule(['A'], {'A': job}, {**fleet, 'shift_minutes': 44}) is None

def test_unloading_must_finish_within_window():
    payload = scenario(0, 1)
    payload['jobs'][0].update(x=10,y=0,opens=0,closes=20,service_minutes=5)
    result = plan(payload)
    assert result['optimized']['served'] == 0 and audit(result)
    assert 'solo' in result['optimized']['unassigned'][0]['reason']

def test_oversized_delivery_explained():
    payload = scenario(0, 1); payload['jobs'][0]['boxes'] = 31
    result = plan(payload)
    assert result['optimized']['served'] == 0 and 'capacity' in result['optimized']['unassigned'][0]['reason']

def test_two_opt_removes_crossing():
    jobs = {key:dict(id=key,name=key,x=x,y=y,boxes=1,opens=0,closes=600,service_minutes=1) for key,x,y in [('A',1,1),('B',-1,1),('C',1,-1),('D',-1,-1)]}
    fleet = dict(vehicles=1,capacity=10,shift_minutes=600,speed_kmh=30)
    original = [['A','D','B','C']]
    improved,work = improve(original,jobs,fleet)
    assert schedule(improved[0],jobs,fleet)['distance_km'] < schedule(original[0],jobs,fleet)['distance_km']
    assert set(improved[0]) == set(original[0]) and work['accepted_moves'] > 0

def test_validator_catches_tampered_result():
    result = plan(scenario(0,6));result['optimized']['routes'][0]['distance_km'] += 1
    with pytest.raises(AssertionError):audit(result)

@pytest.mark.parametrize('field,value',[('vehicles',0),('vehicles',1.5),('capacity',True),('speed_kmh',0),('shift_minutes',999)])
def test_invalid_fleet(field,value):
    payload=scenario();payload['fleet'][field]=value
    with pytest.raises(ValueError):validate(payload)

@pytest.mark.parametrize('field,value',[('id','bad/id'),('name',''),('x',float('nan')),('y',float('inf')),('boxes',0),('opens',599)])
def test_invalid_delivery(field,value):
    payload=scenario();payload['jobs'][0][field]=value
    with pytest.raises(ValueError):validate(payload)

def test_duplicate_ids_and_job_limit():
    payload=scenario();payload['jobs'][1]['id']=payload['jobs'][0]['id']
    with pytest.raises(ValueError,match='unique'):validate(payload)
    payload=scenario();payload['jobs']*=2
    with pytest.raises(ValueError,match='40'):validate(payload)

def test_payload_not_mutated():
    payload=scenario(0,5);original=copy.deepcopy(payload);plan(payload);assert payload==original
