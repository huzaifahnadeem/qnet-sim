import networkx as nx
class layout:
    def _kk_into_fr(G):
        # kamada kawai layout for initial pos feed into fruchterman reingold. 
        # ref: https://en.wikipedia.org/wiki/Force-directed_graph_drawing#:~:text=A%20combined%20application%20of%20different%20algorithms%20is%20helpful%20to%20solve%20this%20problem.%5B10%5D%20For%20example%2C%20using%20the%20Kamada%E2%80%93Kawai%20algorithm%5B11%5D%20to%20quickly%20generate%20a%20reasonable%20initial%20layout%20and%20then%20the%20Fruchterman%E2%80%93Reingold%20algorithm%5B12%5D%20to%20improve%20the%20placement%20of%20neighbouring%20nodes.
        inital_pos = nx.kamada_kawai_layout(G)
        final_pos = nx.fruchterman_reingold_layout(G, pos = inital_pos)
        return final_pos
    
    'fruchterman reingold'
    'circular'
    'spectral': nx.random_layout,
    'random': nx.spectral_layout,
    'spring': nx.spring_layout, # internally in networkx is equal to 'fruchterman reingold'
    'kamada kawai': nx.kamada_kawai_layout,
    'planar': nx.planar_layout,
    'spiral': nx.spiral_layout,
    'kk --> fr'

    _function_for = {
        'fruchterman reingold': nx.fruchterman_reingold_layout,
        'circular': nx.circular_layout,
        'spectral': nx.random_layout,
        'random': nx.spectral_layout,
        'spring': nx.spring_layout, # internally in networkx is equal to 'fruchterman reingold'
        'kamada kawai': nx.kamada_kawai_layout,
        'planar': nx.planar_layout,
        'spiral': nx.spiral_layout,
        'kk --> fr': _kk_into_fr,
        }
        
        function = _function_for[self.config.graph.layout.name]