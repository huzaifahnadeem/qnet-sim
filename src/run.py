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
    seeds = range(0, 10)
    qs = ['0', '0.1']
    ps = ['0.4', '0.55']
    x_dists = range(1, 11)

    for x in x_dists:
        for p in ps:
            for q in qs:
                for s in seeds:
                    cmds_name.append(f'seed={str(s)}, p={p}, q={q}')
                    cmds.append(
                        CMD_PREFIX + f"--seed={str(s)} --alg=SLMPg --network=grid_2d --grid_dim=11 --prob_swap_loss={q} --qc_loss_model=fixed --qc_p_loss_init={p} --x_dist_gte={str(x)} --x_dist_lte={str(x)} --y_dist_gte={str(x)} --y_dist_lte={str(x)} --max_sd=10 --min_sd=10"
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