"""教学NMS与对称INT8量化，不运行YOLO或生成RKNN模型。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def nms(boxes,scores,iou_threshold):
    boxes,scores=np.asarray(boxes,float),np.asarray(scores,float)
    if boxes.ndim!=2 or boxes.shape[1]!=4 or scores.shape!=(len(boxes),) or not 0<=iou_threshold<=1:
        raise ValueError('Expected N xyxy boxes, N scores and threshold in [0,1]')
    if not np.isfinite(boxes).all() or not np.isfinite(scores).all() or np.any(boxes[:,2:]<=boxes[:,:2]):
        raise ValueError('Boxes/scores must be finite; x2>x1 and y2>y1 (positive area)')
    order=np.argsort(-scores,kind='stable');kept=[]
    area=(boxes[:,2]-boxes[:,0])*(boxes[:,3]-boxes[:,1])
    while len(order):
        i=int(order[0]);kept.append(i);rest=order[1:]
        intersection_min=np.maximum(boxes[i,:2],boxes[rest,:2])
        intersection_max=np.minimum(boxes[i,2:],boxes[rest,2:])
        sizes=np.maximum(0,intersection_max-intersection_min)
        intersection=sizes[:,0]*sizes[:,1]
        union=area[i]+area[rest]-intersection
        iou=np.divide(intersection,union,out=np.zeros_like(intersection),where=union>0)
        order=rest[iou<=iou_threshold]
    return kept

def quantize_symmetric(values,scale):
    values=np.asarray(values,float)
    if not np.isfinite(scale) or scale<=0 or not np.isfinite(values).all():
        raise ValueError('Scale must be finite positive and values finite')
    return np.clip(np.rint(values/scale),-127,127).astype(np.int8)

def dequantize_symmetric(values,scale):
    values=np.asarray(values)
    if values.dtype!=np.int8 or not np.isfinite(scale) or scale<=0:
        raise ValueError('Expected int8 values and positive finite scale')
    return values.astype(float)*scale

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    boxes=np.array([[0,0,2,2],[0,0,2,2],[3,3,4,4]],float);scores=np.array([.9,.8,.7])
    kept=nms(boxes,scores,.5);print('Kept box indices:',kept)
    values=np.array([-.26,.04,.26,13.]);scale=.1
    q=quantize_symmetric(values,scale);restored=dequantize_symmetric(q,scale)
    with (args.out_dir/'quantization.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['original','int8','reconstructed','error','clipped'])
        w.writerows(zip(values,q,restored,restored-values,abs(values/scale)>127))
    with (args.out_dir/'nms.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['index','x1_px','y1_px','x2_px','y2_px','score','kept'])
        w.writerows((i,*box,scores[i],int(i in kept)) for i,box in enumerate(boxes))

if __name__=='__main__':main()
