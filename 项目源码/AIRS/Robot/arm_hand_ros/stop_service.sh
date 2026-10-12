#!/bin/bash

rosnode kill /taihu_motor
ps -ef | grep linker_hand_sdk_ros | grep -v grep | awk '{print $2}' | xargs -r kill -9

