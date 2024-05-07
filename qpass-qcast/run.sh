#!/usr/bin/env bash

# | tail -n 14 | head -n 1

# echo "seed=0, depolar(0)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_noise_model=dephase --qc_noise_param=0 --qc_noise_time_independent

# echo "seed=0, depolar(0.25)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_noise_model=dephase --qc_noise_param=0.25 --qc_noise_time_independent

# echo "seed=0, depolar(0.5)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_noise_model=dephase --qc_noise_param=0.5 --qc_noise_time_independent

# echo "seed=0, depolar(0.75)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_noise_model=dephase --qc_noise_param=0.75 --qc_noise_time_independent

# echo "seed=0, depolar(1.0)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_noise_model=dephase --qc_noise_param=1.0 --qc_noise_time_independent




# echo "seed=0, mem depolar(0)"
# python main.py --seed=0 --alg=SLMPg \
#     --qm_noise_model=depolar --qm_noise_param=0 --qm_noise_time_independent

# echo "seed=0, mem depolar(0.25)"
# python main.py --seed=0 --alg=SLMPg \
#     --qm_noise_model=depolar --qm_noise_param=0.25 --qm_noise_time_independent

# echo "seed=0, mem depolar(0.5)"
# python main.py --seed=0 --alg=SLMPg \
#     --qm_noise_model=depolar --qm_noise_param=0.5 --qm_noise_time_independent

# echo "seed=0, mem depolar(0.75)"
# python main.py --seed=0 --alg=SLMPg \
#     --qm_noise_model=depolar --qm_noise_param=0.75 --qm_noise_time_independent

# echo "seed=0, mem depolar(1.0)"
# python main.py --seed=0 --alg=SLMPg \
#     --qm_noise_model=depolar --qm_noise_param=1.0 --qm_noise_time_independent




# echo "seed=0, mem depolar(0)"
# python main.py --seed=0 --alg=SLMPl \
#     --qm_noise_model=depolar --qm_noise_param=0 --qm_noise_time_independent

# echo "seed=0, mem depolar(0.25)"
# python main.py --seed=0 --alg=SLMPl \
#     --qm_noise_model=depolar --qm_noise_param=0.25 --qm_noise_time_independent

# echo "seed=0, mem depolar(0.5)"
# python main.py --seed=0 --alg=SLMPl \
#     --qm_noise_model=depolar --qm_noise_param=0.5 --qm_noise_time_independent

# echo "seed=0, mem depolar(0.75)"
# python main.py --seed=0 --alg=SLMPl \
#     --qm_noise_model=depolar --qm_noise_param=0.75 --qm_noise_time_independent

# echo "seed=0, mem depolar(1.0)"
# python main.py --seed=0 --alg=SLMPl \
#     --qm_noise_model=depolar --qm_noise_param=1.0 --qm_noise_time_independent





# # echo "seed=0, mem depolar(0)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_loss_model=fibre --qc_p_loss_init=0

# # echo "seed=0, mem depolar(0.25)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_loss_model=fibre --qc_p_loss_init=0.25

# # echo "seed=0, mem depolar(0.5)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_loss_model=fibre --qc_p_loss_init=0.5

# # echo "seed=0, mem depolar(0.75)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_loss_model=fibre --qc_p_loss_init=0.75

# # echo "seed=0, mem depolar(1.0)"
# python main.py --seed=0 --alg=SLMPg \
#     --qc_loss_model=fibre --qc_p_loss_init=1




# echo "seed=0, mem depolar(0)"
python main.py --seed=0 --alg=SLMPg \
    --qc_loss_model=fixed --qc_p_loss_init=0

# echo "seed=0, mem depolar(0.25)"
python main.py --seed=0 --alg=SLMPg \
    --qc_loss_model=fixed --qc_p_loss_init=0.25

# echo "seed=0, mem depolar(0.5)"
python main.py --seed=0 --alg=SLMPg \
    --qc_loss_model=fixed --qc_p_loss_init=0.5

# echo "seed=0, mem depolar(0.75)"
python main.py --seed=0 --alg=SLMPg \
    --qc_loss_model=fixed --qc_p_loss_init=0.75

# echo "seed=0, mem depolar(1.0)"
python main.py --seed=0 --alg=SLMPg \
    --qc_loss_model=fixed --qc_p_loss_init=1




# # echo "seed=0, mem depolar(0)"
# python main.py --seed=0 --alg=SLMPg \
#     --prob_swap_loss=0

# # echo "seed=0, mem depolar(0.25)"
# python main.py --seed=0 --alg=SLMPg \
#     --prob_swap_loss=0.25

# # echo "seed=0, mem depolar(0.5)"
# python main.py --seed=0 --alg=SLMPg \
#     --prob_swap_loss=0.5

# # echo "seed=0, mem depolar(0.75)"
# python main.py --seed=0 --alg=SLMPg \
#     --prob_swap_loss=0.75

# # echo "seed=0, mem depolar(1.0)"
# python main.py --seed=0 --alg=SLMPg \
#     --prob_swap_loss=1