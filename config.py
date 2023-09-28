import constants

class data_directory:
    path = './data'

class graph:
    class layout:
        # kamada kawai feeding into fruchterman reingold seems the best option. However, both of these have a higher running time so using just kamada kawai layout for now as that seems to be good by itself as well. fruchterman reingold also seems good but not as good as just kamada kawai 
        name = constants.graph_layout.kamada_kawaii
    
    class nodes:
        class user_pair:
            colors = ['cyan', 'green', 'yellow', 'pink', 'red', 'purple', 'blue', 'indigo']
            size = 700
            shape = 'o' # circle
            edge_color = 'black'
        
        class storage:
            color = 'gray'
            size = 700
            shape = 's' # square
            edge_color = 'red'
        
        class other:
            color = 'white'
            size = 700
            shape = 'o' # circle
            edge_color = 'black'
    
    class edges:
        arrow_size = 20
        # possible styles: ‘-’, ‘–’, ‘-.’, ‘:’ or words like ‘solid’ or ‘dashed’ 
        style_non_virtual = 'solid'
        style_virtual = '-.'

        color_non_virtual = 'black'
        color_virtual = 'red'
    
    class plot:
        # 'width' x 'height' in inches s.t. each 1 inch is equal to 'dpi' pixels
        width, height, dpi = 15, 9.75, 80

class random_params:
    # None can be used to use system time for as seed
    seed = 0