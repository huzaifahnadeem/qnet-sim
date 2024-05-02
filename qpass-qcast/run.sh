#!/usr/bin/env bash

python main.py --seed=1 --error_model=dephase --error_param=0.25 --error_time_independent=yes | tail -n 14 | head -n 1
python main.py --seed=5 --error_model=dephase --error_param=0.25 --error_time_independent=yes | tail -n 14 | head -n 1

python main.py --seed=0 --error_model=depolar --error_param=0.9 --error_time_independent=yes | tail -n 14 | head -n 1
python main.py --seed=5 --error_model=depolar --error_param=0.9 --error_time_independent=yes | tail -n 14 | head -n 1
python main.py --seed=8 --error_model=depolar --error_param=0.9 --error_time_independent=yes | tail -n 14 | head -n 1

python main.py --seed=8 --error_model=depolar --error_param=0.9 --error_time_independent=yes --network=abilene | tail -n 14 | head -n 1