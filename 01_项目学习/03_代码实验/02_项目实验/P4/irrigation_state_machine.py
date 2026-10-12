"""Deterministic teaching policy. Invalid/stale sensor -> pump off, including manual on."""
import argparse,csv,math
from pathlib import Path
def irrigation_step(mode,moisture,manual_request,pump_on,start_threshold,stop_threshold,sensor_fresh):
    if mode not in ("auto","manual") or manual_request not in ("on","off",None):raise ValueError("invalid mode/request")
    if not all(math.isfinite(v) for v in (start_threshold,stop_threshold)) or not 0<=start_threshold<stop_threshold<=100:raise ValueError("0<=start<stop<=100 required")
    if manual_request=="off":return False,"manual_off"
    if not sensor_fresh or moisture is None or not isinstance(moisture,(int,float)) or not math.isfinite(moisture) or not 0<=moisture<=100:return False,"invalid_or_stale_sensor"
    if mode=="manual":
        return (True,"manual_on") if manual_request=="on" else (bool(pump_on),"manual_hold")
    if manual_request=="on":return bool(pump_on),"manual_on_requires_manual_mode"
    if moisture<start_threshold:return True,"below_start"
    if moisture>stop_threshold:return False,"above_stop"
    return bool(pump_on),"hysteresis_hold"
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    cases=[("auto",55,None,True),("auto",60,None,True),("auto",64,None,True),("auto",66,None,True),("auto",60,None,True),("manual",40,"on",True),("manual",40,"off",True),("auto",40,None,False)]
    pump=False
    with (a.out_dir/"irrigation.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["index","mode","moisture_percent","manual_request","sensor_fresh","pump_on","reason"])
        for i,(mode,m,request,fresh) in enumerate(cases):
            pump,reason=irrigation_step(mode,m,request,pump,56,65,fresh);w.writerow([i,mode,m,request,fresh,pump,reason])
    print(a.out_dir)
if __name__=="__main__":main()
