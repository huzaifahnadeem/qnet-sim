#!/usr/bin/env python

import subprocess
import os
import multiprocessing

# OUTPUT_DIRECTORY = "./experiments-results/"
CMD_PREFIX = 'python main.py '

def run_command(cmd, exp_name):
    print(f'\nSTARTING EXP < {exp_name} > AS: " {cmd} " ... ')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"< {exp_name} > process returned")
        print(result.stdout)
        print(result.stderr)
    except SystemExit:
        pass

def main():
    # if not os.path.exists(f"./{OUTPUT_DIRECTORY}/"):
    #     os.makedirs(f"./{OUTPUT_DIRECTORY}/")

    cmds = []
    cmds_name = []

    # SLMP experiments repeat:
    seeds = range(0, 10)
    qs = ['0', '0.1', '0.5']
    ps = ['0.4', '0.55', '0.7']

    for p in ps:
        for q in qs:
            for s in seeds:
                cmds_name.append(f'seed={str(s)}, p={p}, q={q}')
                cmds.append(
                    CMD_PREFIX + f"--seed={str(s)} --alg=SLMPg --network=grid_2d --grid_dim=10 --prob_swap_loss={q} --qc_loss_model=fixed --qc_p_loss_init={p}"
                )
    
    procs = []
    for idx, c in enumerate(cmds):
        this_exp_name = cmds_name[idx]
        this_cmd = c
        this_proc = multiprocessing.Process(target=run_command, args=[this_cmd, this_exp_name], name=this_exp_name)
        procs.append(this_proc)
    for p in procs:
        p.start()
    for p in procs:
        p.join()

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()