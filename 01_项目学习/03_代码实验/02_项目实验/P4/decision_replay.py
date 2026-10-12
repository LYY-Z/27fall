"""Rule-based proposals only. No real LLM call or device action."""
import argparse,csv,math
from pathlib import Path
from irrigation_state_machine import irrigation_step
def decision_step(state,event):
    if not isinstance(state,dict) or not isinstance(event,dict):raise ValueError("dict state/event required")
    if state.get("mode") not in ("auto","manual"):raise ValueError("state requires mode auto/manual")
    m=state.get("moisture")
    if not state.get("sensor_fresh") or not isinstance(m,(int,float)) or not math.isfinite(m) or not 0<=m<=100:
        return dict(action="stop",reason="untrusted_sensor",requires_policy_check=True)
    if event.get("manual_request")=="off":return dict(action="stop",reason="manual_off",requires_policy_check=True)
    if m<56:return dict(action="start",reason="dry_rule",requires_policy_check=True)
    if m>65:return dict(action="stop",reason="wet_rule",requires_policy_check=True)
    return dict(action="hold",reason="within_hysteresis_band",requires_policy_check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    cases=[(dict(moisture=40,pump_on=False,mode="auto",sensor_fresh=True),{}),(dict(moisture=40,pump_on=False,mode="manual",sensor_fresh=True),{}),(dict(moisture=40,pump_on=True,mode="manual",sensor_fresh=True),dict(manual_request="off"))]
    with (a.out_dir/"decision_replay.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["case","proposal_action","proposal_reason","requires_policy_check","simulated_pump_on","execution_reason"])
        for i,(state,event) in enumerate(cases):
            proposal=decision_step(state,event)
            # Proposal does not override mode: execution policy remains authoritative.
            pump,reason=irrigation_step(state["mode"],state["moisture"],event.get("manual_request"),state["pump_on"],56,65,state["sensor_fresh"])
            w.writerow([i,proposal["action"],proposal["reason"],proposal["requires_policy_check"],pump,reason])
    print(a.out_dir)
if __name__=="__main__":main()
