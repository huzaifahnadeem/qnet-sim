class data_directory:
    path = './data'

class graph:
    # name string needs to be exact strings

    # name = 'ATT'
    name = 'Abilene'
    # name = 'IBM'
    # name = 'SURFnet'
    # name = 'G(50,0.1)'
    # name = 'G(50,0.05)'

    node_color = 'blue'
    highlight_color = 'red'

class storage_servers:
    # selection_scheme = 'RANDOM'
    selection_scheme = 'DEGREE'

class user_pairs:
    number = 6 # temp. same value as the QON paper used => presumably because abilene (the smallest graph) can have at most 6 pairs (total 12 nodes)

    # it is unclear how they choose these user pairs in the QON paper so for now going with the only option as randomly choosing the pairs (could potentially add other schemes therefore adding the config variable):
    selection_scheme = 'RANDOM'

class fixed_params: # the parameters that were fixed in Table II in the QON paper
    delta = 20 # Δ = 20 sec = duration of 1 time interval in seconds
    T = set(t for t in range(0, 10*delta, delta))   # |T| = 10

    # c_u_v :  capacity of link (u, v) in EPRs/sec. Values fixed as follows: c(u,v) = Unif[200,1400]
    
    class c_u_v:
        random_start = 200
        random_stop = 1400 

    # Link Fidelity = Unif[0.96,0.99]
    class link_fidelity:
        random_start = 0.96
        random_stop = 0.99

    B_s = 12000 # the capacity of storage servers in no. of EPR pairs (all servers have a fixed value of 12000)

class random_params:
    seed = 0