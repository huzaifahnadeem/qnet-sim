#!/usr/bin/env bash

# | tail -n 14 | head -n 1

python main.py --seed=0 \
    --qc_noise_model=depolar --qc_noise_param=0.333 #--error_time_independent=yes --qc_noise_time_independent