"""Teaching event schema differs from the RK source JSON and requires an adapter."""
import argparse,csv,math
from pathlib import Path
def parse_detection_event(payload,now_s,max_age_s,min_confidence):
    if not all(math.isfinite(v) for v in (now_s,max_age_s,min_confidence)) or max_age_s<0 or not 0<=min_confidence<=1:raise ValueError("invalid filter parameters")
    if not isinstance(payload,dict) or not isinstance(payload.get("timestamp_s"),(int,float)) or not isinstance(payload.get("detections"),list):return [],"invalid_schema"
    timestamp=payload["timestamp_s"]
    if not math.isfinite(timestamp):return [],"invalid_timestamp"
    age=now_s-timestamp
    if age<0:return [],"future_timestamp"
    if age>max_age_s:return [],"stale"
    accepted=[]
    for d in payload["detections"]:
        if not isinstance(d,dict) or not isinstance(d.get("class_name"),str) or not d["class_name"]:return [],"invalid_detection"
        conf=d.get("confidence");box=d.get("bbox_xyxy")
        if not isinstance(conf,(int,float)) or not math.isfinite(conf) or not 0<=conf<=1 or not isinstance(box,(list,tuple)) or len(box)!=4 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in box):return [],"invalid_detection"
        x1,y1,x2,y2=box
        if min(x1,y1)<0 or x2<=x1 or y2<=y1:return [],"invalid_bbox"
        if conf>=min_confidence:accepted.append(dict(d))
    return accepted,"accepted" if accepted else "no_detection_above_threshold"
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    detection={"class_name":"leaf_spot","confidence":.9,"bbox_xyxy":[1,2,20,30]}
    cases=[("fresh",{"timestamp_s":9.5,"detections":[detection]}),("stale",{"timestamp_s":8.,"detections":[detection]}),("future",{"timestamp_s":11.,"detections":[detection]}),("bad_box",{"timestamp_s":10.,"detections":[dict(detection,bbox_xyxy=[20,2,1,30])]})]
    with (a.out_dir/"vision_events.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["case","accepted_count","status"])
        for label,event in cases:
            detections,status=parse_detection_event(event,10.,1.,.6);w.writerow([label,len(detections),status])
    print(a.out_dir)
if __name__=="__main__":main()
