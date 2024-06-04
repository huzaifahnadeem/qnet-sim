#!/usr/bin/env python

import subprocess
import os
import multiprocessing

NUM_POOL = 4

# OUTPUT_DIRECTORY = "./experiments-results/"
CMD_PREFIX = 'python main.py '

def run_command(cmds):
    cmd, exp_name = cmds
    print(f'\nSTARTING EXP < {exp_name} > AS: " {cmd} " ... ')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"< {exp_name} > process returned")
        print(result.stdout)
        print(result.stderr)
    except SystemExit:
        pass

    return 1

def main():
    # if not os.path.exists(f"./{OUTPUT_DIRECTORY}/"):
    #     os.makedirs(f"./{OUTPUT_DIRECTORY}/")

    cmds = []
    cmds_name = []

    # SLMP experiments repeat:
    seeds = range(0, 20)
    # qs = ['0', '0.1']
    # ps = ['0.4', '0.55']
    pqs = [('0.55', '0'), ('0.4', '0.1'), ('0.4', '0')]
    # x_dists = range(1, 11)

    exp_counter = 0
    # total_exps = len(list(seeds))*len(list(x_dists))*len(pqs)
    total_exps = len(list(seeds))*len(pqs)
    # for x in x_dists:
    for p, q in pqs:
        for s in seeds:
            exp_counter += 1
            cmds_name.append(f'exp_num {exp_counter} out of {total_exps}')
            cmds.append(
                # CMD_PREFIX + f"--one_sided_epr --num_ts=10 --traffic_matrix=file --tm_file=./sample_tm_file.json --alg=SLMPg --network=grid_2d --grid_dim=11 --qc_loss_model=fixed --seed={str(s)} --qc_p_loss_init={p} --prob_swap_loss={q} --x_dist_gte={str(x)} --x_dist_lte={str(x)} --y_dist_gte={str(x)} --y_dist_lte={str(x)}" #  --max_sd=10 --min_sd=10
                CMD_PREFIX + f"--one_sided_epr --num_ts=10 --traffic_matrix=file --tm_file=/home/hun13/qnet-sim/src/sample_tm_file.json --alg=SLMPg --network=grid_2d --grid_dim=20 --qc_loss_model=fixed --seed={str(s)} --qc_p_loss_init={p} --prob_swap_loss={q}"
            )

    args = []
    for idx, c in enumerate(cmds):
        this_exp_name = cmds_name[idx]
        this_cmd = c
        args.append((this_cmd, this_exp_name))
        
    pool = multiprocessing.Pool(NUM_POOL)
    result = pool.map(run_command, args)
    pool.terminate()
    print(result)

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()