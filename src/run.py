#!/usr/bin/env python

import subprocess
import multiprocessing
import argparse
import yaml

class defaults:
    num_pool = 5

def get_args():
    parser = argparse.ArgumentParser(description="Tool to run main.py multiple times with different params for experiments.")
    parser.add_argument('--num_pool', required=False, default=defaults.num_pool, type=int, help=f'To set the number of pools for parallel processing. Default set to {defaults.num_pool}')
    parser.add_argument('--runfile', required=True, type=str, help=f'Path to the runfile to use. Sample runfile available in ./runfiles/sample_run.yaml')

    return parser.parse_args()

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
    except Exception as e:
        return e

    return 1

def main():
    args = get_args()
    
    runfile = None
    with open(args.runfile) as stream:
        runfile = yaml.safe_load(stream)
    
    # create the command prefix using 'python main.py' and the static args:
    cmd = 'python main.py'
    for arg in runfile['static'].keys():
        val = runfile['static'][arg]
        cmd += f" --{arg}{'' if val is None else f'={str(val)}'}" # for binary flag args like --one_sided_epr, val is stored as None
    cmd_prefix = cmd

    # handle loopfor args:
    seeds, probs = None, None
    for arg in runfile['loopfor'].keys():
        if arg == 'seed':
            keyword = list(runfile['loopfor']['seed'].keys())[0]
            if keyword == 'range':
                seeds = list(range(runfile['loopfor']['seed']['range'][0], runfile['loopfor']['seed']['range'][1]))
            if keyword == 'list':
                seeds = runfile['loopfor']['seed']['list']
        elif arg == 'probs':
            ps = runfile['loopfor']['probs']['p']
            qs = runfile['loopfor']['probs']['q']
            p_isof_success, q_isof_success = None, None
            if 'p_isof_success' in runfile['loopfor']['probs'].keys():
                p_isof_success = runfile['loopfor']['probs']['p_isof_success']
            else:
                p_isof_success = False
            if 'q_isof_success' in runfile['loopfor']['probs'].keys():
                q_isof_success = runfile['loopfor']['probs']['q_isof_success']
            else:
                q_isof_success = False
            ps = [1-p for p in ps] if p_isof_success else ps
            qs = [1-q for q in qs] if q_isof_success else qs
            if runfile['loopfor']['probs']['iszip']:
                probs = zip(ps, qs)
            else:
                probs = []
                for p in ps:
                    for q in qs:
                        probs.append((p, q))
        else:
            raise ValueError # unknown arg
    
    cmds = []
    for seed in seeds:
        s = str(seed)
        for prob_p, prob_q in probs:
            p = str(prob_p)
            q = str(prob_q)
            this_cmd = f"{cmd_prefix} --seed={s} --qc_p_loss_init={p} --prob_swap_loss={q}"
            cmds.append(this_cmd)
    total_num_cmds = len(cmds)

    args_run_command_fn = []
    for idx, cmd in enumerate(cmds):
        exp_name = f"# {idx + 1} out of {total_num_cmds}"
        args_run_command_fn.append((cmd, exp_name))
    pool = multiprocessing.Pool(args.num_pool)
    result = pool.map(run_command, args_run_command_fn)
    pool.terminate()
    print(result)

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()