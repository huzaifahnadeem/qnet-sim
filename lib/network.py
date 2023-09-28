import networkx as nx
import matplotlib.pyplot as plt

import config
import constants

class Network:
    def __init__(self) -> None:
        # self.graph = nx.Graph()
        self._graph = nx.grid_2d_graph(5, 5)
    
    def visualize(self) -> None:
        # plt figure size:
        plt.figure(
            figsize = (
                config.plot.width, 
                config.plot.height
                ), 
                dpi = config.plot.dpi
                ) # 'width' x 'height' in inches s.t. each 1 inch is equal to 'dpi' pixels

        # set up node positions in the graph:
        layout_fn = constants.layout
        pos = layout_fn(self._graph)

        # set up node positions in the graph:
        pos = config.layout.function(self._nx_graph)
