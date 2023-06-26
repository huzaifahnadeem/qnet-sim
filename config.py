class data_directory:
    path = './data'

class graph:
    class layout:
        _choices = [ # name string needs to be exact strings so adding this list:
            'fruchterman reingold', # [0]
            'circular',             # [1]
            'spectral',             # [2]
            'random',               # [3]
            'spring',               # [4]
            'kamada kawai',         # [5]
            'planar',               # [6]
            'spiral',               # [7]
            'kk --> fr',            # [8] # kamada kawai as inital layout feeded into fruchterman reingold
        ]
        # Note: kamada kawai feeding into fruchterman reingold seems the best option. However, both of these have a higher running time so using just kamada kawai layout for now as that seems to be good by itself as well. fruchterman reingold also seems good but not as good as just kamada kawai 
        name = _choices[5] # = 'kamada kawai'
        # name = _choices[8] # = 'kk --> fr'
    
    class nodes:
        class user_pair:
            colors = ['cyan', 'green', 'yellow', 'pink', 'red', 'purple', 'blue', 'indigo']
            size = 700
            shape = 's' # square
            edge_color = 'green'
        
        class storage:
            color = 'gray'
            size = 1000
            shape = '^' # triangle
            edge_color = 'red'
        
        class other:
            color = 'white'
            size = 600
            shape = 'o' # circle
            edge_color = 'black'
    
    class edges:
        arrow_size = 20

class random_params:
    seed = 0