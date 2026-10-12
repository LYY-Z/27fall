"""Single-process, single-boot teaching registry. No network or persistent action log."""
import argparse,csv,math
from pathlib import Path
FEEDBACK_TTL_S=1.
def register_device(registry,device_id,capabilities,sequence):
    if not isinstance(device_id,str) or not device_id or not isinstance(sequence,int) or sequence<0 or not isinstance(capabilities,set) or any(not isinstance(c,str) or not c for c in capabilities):raise ValueError("invalid registration")
    if device_id in registry:
        record=registry[device_id]
        if sequence<record["last_sequence"]:return "rejected_old_sequence"
        if sequence==record["last_sequence"]:return "duplicate" if record["capabilities"]==capabilities else "rejected_conflicting_registration"
        record["capabilities"]=set(capabilities);record["last_sequence"]=sequence;record["online"]=False
        return "updated_requires_sync"
    registry[device_id]=dict(capabilities=set(capabilities),last_sequence=sequence,last_feedback_time_s=None,online=False,executed_action_ids=set())
    return "registered_requires_sync"
def update_feedback(registry,device_id,sequence,sampled_at_s,now_s):
    if device_id not in registry:return "unknown_device"
    if not isinstance(sequence,int) or sequence<0 or not all(isinstance(t,(int,float)) and math.isfinite(t) for t in (sampled_at_s,now_s)):return "invalid_feedback"
    record=registry[device_id]
    if sequence<=record["last_sequence"]:return "old_sequence"
    age=now_s-sampled_at_s
    if age<0 or age>FEEDBACK_TTL_S:return "invalid_age"
    record["last_sequence"]=sequence;record["last_feedback_time_s"]=sampled_at_s;record["online"]=True
    return "synchronized"
def dispatch_action(registry,proposal,now_s):
    action_id=proposal.get("action_id","") if isinstance(proposal,dict) else ""
    def reply(status,reason):return dict(action_id=action_id,status=status,reason=reason)
    keys={"action_id","device_id","capability","issued_at_s","max_age_s","value"}
    if not isinstance(proposal,dict) or set(proposal)!=keys or not all(isinstance(proposal.get(k),str) and proposal[k] for k in ("action_id","device_id","capability")):return reply("rejected","invalid_schema")
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (now_s,proposal["issued_at_s"],proposal["max_age_s"],proposal["value"])) or proposal["max_age_s"]<0:return reply("rejected","invalid_numeric_field")
    record=registry.get(proposal["device_id"])
    if record is None:return reply("rejected","unknown_device")
    if action_id in record["executed_action_ids"]:return reply("duplicate","already_executed_in_this_process")
    if proposal["capability"] not in record["capabilities"]:return reply("rejected","unsupported_capability")
    timestamp=record["last_feedback_time_s"]
    if not record["online"] or timestamp is None or not 0<=now_s-timestamp<=FEEDBACK_TTL_S:return reply("rejected","offline_or_stale_feedback")
    if not 0<=now_s-proposal["issued_at_s"]<=proposal["max_age_s"]:return reply("rejected","expired_or_future_proposal")
    if not -1<=proposal["value"]<=1:return reply("rejected","outside_teaching_value_policy")
    # Simulated acceptance/effect only; no hardware and no promise of persistent exactly-once.
    record["executed_action_ids"].add(action_id)
    return reply("executed","simulated_effect")
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    registry={};registration=register_device(registry,"robot",{"move","stop"},1);sync=update_feedback(registry,"robot",2,9.5,10.)
    base=dict(action_id="a1",device_id="robot",capability="move",issued_at_s=9.8,max_age_s=.5,value=.5)
    proposals=[base,base,dict(base,action_id="a2",capability="fly"),dict(base,action_id="a3",issued_at_s=8),dict(base,action_id="a4",value=2)]
    with (a.out_dir/"dispatch.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["action_id","status","reason","registration","synchronization"])
        for proposal in proposals:
            result=dispatch_action(registry,proposal,10.);w.writerow([result["action_id"],result["status"],result["reason"],registration,sync])
    print(a.out_dir)
if __name__=="__main__":main()
