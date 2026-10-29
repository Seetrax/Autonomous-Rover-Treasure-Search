#!/bin/bash
source install/setup.sh 
source /cs-share/pradalier/venv/tf-cpu-ros2/bin/activate
python3 src/tensorflow_models_base/tensorflow_models_base/train.py \
    --val_file ./data/arm_observe/train/labels.txt \
    --val_root ./data/arm_observe/train/ \
    --train_file ./data/arm_observe/train/labels.txt \
    --train_root ./data/arm_observe/train \
    --learning_rate 0.0001 \
    --batch_size 32 \
    --iter 3000 \
    --dropout 0.5 \
    --classes 9 \
    --output ./output
