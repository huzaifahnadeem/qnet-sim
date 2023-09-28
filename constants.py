# these classes have variables assigned to the exact string values for ease.
    
class toplogies:
    # the input topologies
    att = 'ATT'
    abilene = 'Abilene'
    ibm = 'IBM'
    surfnet = 'SURFnet'
    g_50_p1 = 'G(50, 0.1)'
    g_50_p05 = 'G(50, 0.05)'
    pa_50_2 = 'PA(50, 2)'
    pa_50_2 = 'PA(50, 3)'

class storage_servers_selection:
    manual = 'manual'
    random = 'random'
    degree = 'degree'

class user_pairs_selection:
    manual = 'manual'
    random = 'random'

class graph_layout:
    fruchterman_reingold = 'fruchterman reingold'
    circular = 'circular'
    spectral = 'spectral'
    random = 'random'
    spring = 'spring'
    kamada_kawaii = 'kamada kawai'
    planar = 'planar'
    spiral = 'spiral'
    kk_into_fr = 'kk --> fr' # kamada kawai as inital layout fed into fruchterman reingold