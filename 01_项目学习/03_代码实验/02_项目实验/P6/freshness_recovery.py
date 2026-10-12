"""Single-boot sequence/freshness replay. Recovery requires synchronized feedback."""
import argparse,csv
from pathlib import Path
from capability_dispatch import register_device,update_feedback,dispatch_action
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    registry={};register_device(registry,"robot",{"move"},1)
    events=[(2,.1,.1),(1,.2,.2),(3,.2,2.),(4,2.,2.)]
    with (a.out_dir/"recovery.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["incoming_sequence","sample_time_s","now_s","feedback_status","action_status","reason"])
        for sequence,sample,now in events:
            status=update_feedback(registry,"robot",sequence,sample,now)
            proposal=dict(action_id=f"a{sequence}_{now}",device_id="robot",capability="move",issued_at_s=now,max_age_s=.2,value=.2)
            result=dispatch_action(registry,proposal,now);w.writerow([sequence,sample,now,status,result["status"],result["reason"]])
    print(a.out_dir)
if __name__=="__main__":main()
