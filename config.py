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
        name = _choices[5] # kamada kawai seems best for our use. fruchterman reingold also seems good
    
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