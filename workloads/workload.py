class graph:
    _choices = [ # name string needs to be exact strings so adding this list:
        'ATT',          # [0]
        'Abilene',      # [1]
        'IBM',          # [2]
        'SURFnet',      # [3]
        'G(50, 0.1)',   # [4]
        'G(50, 0.05)',  # [5]
        'PA(50, 2)',    # [6]
        'PA(50, 3)',    # [7]
    ]
    name = _choices[1]

class storage_servers:
    _choices = [
        'manual',   # [0] # for testing
        'random',   # [1] 
        'degree',   # [2]
    ]
    selection_scheme = _choices[2]
    
    num_servers = 3 # how many servers should there be. use any negative number for random number of servers. for manual selection scheme this number is not taken into account, only the list 'manual_storage_servers' is taken into account. is num_servers > total number of nodes then undefined behavior
    
    manual_storage_servers = ['NYCMng'] # this is only used when selection_scheme = 'manual'. storage servers are specified by node names. This is useful for testing purposes.

class user_pairs:
    # number of user pairs:
    number = 6 # temp. same value as the QON paper used => presumably because abilene (the smallest graph) can have at most 6 pairs (total 12 nodes)

    # number of user pairs that can have a spike in their demand at each time interval:
    num_pairs_with_spikes = 3 # fixed as 3 in the QON paper

    # it is unclear how they choose these user pairs in the QON paper so for now going with the only option as randomly choosing the pairs (could potentially add other schemes therefore adding it as:
    _choices = [
        'manual',   # [0] # for testing
        'random',   # [1]
    ]
    selection_scheme = _choices[1]
    # placeholder:
    manual_user_pairs = [('ATLA-M5', 'WASHng'), ('LOSAng', 'KSCYng'), ('STTLng', 'CHINng'), ('NYCMng', 'ATLAng')] # this is only used when selection_scheme = 'manual'. pairs are specified by tuple of node names. This is useful for testing purposes.

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
