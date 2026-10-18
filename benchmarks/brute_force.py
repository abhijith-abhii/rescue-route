"""Exact 8-stop search vs nearest-feasible plus bounded route improvement."""
import datetime,json,pathlib,platform,statistics,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from exhaustive import exact_route
from planner import plan
from scenarios import scenario
from verification import audit

def main():
    rows=[]
    for seed in range(10):
        payload=scenario(seed,8);payload['fleet'].update(vehicles=1,capacity=200,shift_minutes=600)
        for job in payload['jobs']:job.update(opens=0,closes=600)
        timings={'exact':[],'heuristic':[]}
        for trial in range(3):
            for mode in (['exact','heuristic'] if (seed+trial)%2==0 else ['heuristic','exact']):
                start=time.perf_counter()
                if mode=='exact':exact=exact_route(payload)
                else:result=plan(payload)
                timings[mode].append((time.perf_counter()-start)*1000)
        assert audit(result) and result['optimized']['served']==8 and exact['route']
        gap=100*(result['optimized']['distance_km']/exact['route']['distance_km']-1)
        assert gap >= -1e-7 and exact['orders_evaluated']==40320
        rows.append({'seed':seed,'stops':8,'exact_orders_evaluated':40320,'exact_median_ms':statistics.median(timings['exact']),
          'heuristic_median_ms':statistics.median(timings['heuristic']),'exact_modelled_km':exact['route']['distance_km'],
          'heuristic_modelled_km':result['optimized']['distance_km'],'distance_gap_percent':max(0,gap),
          'paired_timings_ms':timings,'feasibility':'independent audit passed'})
    before=statistics.median(r['exact_median_ms'] for r in rows);after=statistics.median(r['heuristic_median_ms'] for r in rows)
    summary={'exact_median_of_case_medians_ms':before,'heuristic_median_of_case_medians_ms':after,'runtime_reduction_percent':100*(1-after/before),
      'runtime_ratio':before/after,'mean_distance_gap_percent':statistics.mean(r['distance_gap_percent'] for r in rows),
      'maximum_distance_gap_percent':max(r['distance_gap_percent'] for r in rows),'cases_matching_optimum':sum(r['distance_gap_percent']<1e-7 for r in rows),'case_count':10}
    out={'measured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'environment':{'python':platform.python_version(),'system':platform.system(),'architecture':platform.machine()},
      'workload':'All seeds 0–9, 8 fictional stops, 1 vehicle, broad windows, 3 paired trials per seed with alternating order. Same data, distance model and schedule feasibility checks. Heuristic timer includes baseline plus improvement. In-process, no HTTP.',
      'summary':summary,'cases':rows,'limits':'Exhaustive is optimal for the bounded single-vehicle case; heuristic is not guaranteed optimal. Report route-quality gaps alongside speed. Not an exact multi-vehicle solver or measured road, fuel, revenue or production outcome.'}
    (ROOT/'benchmarks/brute-force-results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
