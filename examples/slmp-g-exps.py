import subprocess
import os

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except SystemExit:
        pass

prob_vals_p_q = [('0.6', '1'), ('0.6', '0.9'), ('0.45', '1')]
seed_vals = [str(i) for i in range(10)]
num_ts = 10

def main():
    for p_q in prob_vals_p_q:
        p = p_q[0]
        q = p_q[1]
        for s in seed_vals:
            csv_name = f'exps/p{p}-q{q}-s{s}.csv'
            args_str = f'--seed {s} --num_ts {num_ts} --p_prob {p} --q_prob {q} --csv_name {csv_name}'
            run_command(cmd=f'python slmp_wo_channels.py {args_str}')


if __name__ == '__main__':
    main()