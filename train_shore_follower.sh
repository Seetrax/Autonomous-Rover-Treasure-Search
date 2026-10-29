#!/bin/bash
source install/setup.sh 
source /cs-share/pradalier/venv/tf-cpu-ros2/bin/activate
python3 src/tensorflow_models_base/tensorflow_models_base/train.py \
    --val_file ./data/shore_follower/val/labels.txt \
    --val_root ./data/shore_follower/val/ \
    --train_file ./data/shore_follower/train/labels.txt \
    --train_root ./data/shore_follower/train \
    --learning_rate 0.0001 \
    --batch_size 32 \
    --iter 3000 \
    --dropout 0.5 \
    --classes 3 \
    --output ./output
