"""Compare nearest-feasible routes and bounded optimization on ALL seeds 0–19."""
import datetime,json,pathlib,platform,statistics,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scenarios import scenario
from planner import plan
from verification import audit

def main():
    results=[]
    for seed in range(20):
        payload=scenario(seed,24);start=time.perf_counter();result=plan(payload);elapsed=(time.perf_counter()-start)*1000
        assert audit(result)
        before,after=result['baseline'],result['optimized']
        results.append({'seed':seed,'deliveries':24,'served_before':before['served'],'served_after':after['served'],
            'unassigned':len(after['unassigned']),'baseline_modelled_km':before['distance_km'],'optimized_modelled_km':after['distance_km'],
            'distance_reduction_percent':result['distance_reduction_percent'],'accepted_moves':result['optimizer']['accepted_moves'],
            'comparison_runtime_ms':elapsed,'independent_feasibility_audit':'passed'})
    before=sum(r['baseline_modelled_km'] for r in results);after=sum(r['optimized_modelled_km'] for r in results)
    output={'measured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'environment':{'python':platform.python_version(),'system':platform.system(),'architecture':platform.machine()},
      'workload':{'seeds':list(range(20)),'scenarios':20,'deliveries_per_scenario':24,'vehicles':4,'capacity_per_vehicle_boxes':30,'shift_minutes':360,'speed_kmh':30,'optimization_pass_limit':8},
      'summary':{'baseline_total_modelled_km':before,'optimized_total_modelled_km':after,'aggregate_distance_reduction_percent':100*(1-after/before),
          'median_scenario_reduction_percent':statistics.median(r['distance_reduction_percent'] for r in results),
          'scenarios_improved':sum(r['distance_reduction_percent']>1e-7 for r in results),'scenarios_unchanged':sum(r['distance_reduction_percent']<=1e-7 for r in results),
          'served_in_each_variant':sum(r['served_before'] for r in results),'requested_deliveries':480,
          'median_comparison_runtime_ms':statistics.median(r['comparison_runtime_ms'] for r in results)},
      'cases':results,'limits':'Synthetic planar distance, not roads or actual vehicle mileage. Every scenario is included. Both variants retain the same served set and feasible capacity, unloading windows and depot-return limits. Heuristic, not globally optimal. No measured fuel, emissions, money, beneficiary impact or production scale.'}
    (ROOT/'benchmarks/results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output['summary'],indent=2))
if __name__=='__main__':main()
