"""教学反馈格式：小端uint32 sequence+float32 value，严格8字节。"""
import argparse
import csv
import math
import struct
from pathlib import Path

def decode_demo_feedback(payload):
    if not isinstance(payload,bytes) or len(payload)!=8:
        raise ValueError('Teaching packet must contain exactly eight bytes')
    sequence,value=struct.unpack('<If',payload)
    if not math.isfinite(value):raise ValueError('Feedback value must be finite')
    return sequence,float(value)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    payload=struct.pack('<If',7,1.25);seq,value=decode_demo_feedback(payload)
    print('Payload hex:',payload.hex(),'sequence:',seq,'value:',value)
    with (args.out_dir/'packet.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['hex','sequence','value']);w.writerow([payload.hex(),seq,value])
    try:decode_demo_feedback(payload[:-1])
    except ValueError as error:print('Expected length rejection:',error)

if __name__=='__main__':main()
