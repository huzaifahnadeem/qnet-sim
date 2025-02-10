# import globals
from src.entities import NIS
import netsquid as ns

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities import NodeEntity

def setup():
    from src import setup
    
    setup.get_args()
    setup.apply_args()

def main() -> None:
    setup() 
    
    from src.network import Network # this has to be here since it needs to be imported after set up sets some things up
    # create network object. (entities are part of each node property in the network object)
    nw = Network()
    node_names = [n for n in nw.node_names()]

    # create the network information server / controller entity:
    nis = NIS(nw)

    # set the nis entity and node entites properties for the node entities:
    node_entities = []
    for n_name in node_names:
        n_entity: 'NodeEntity' = nw.get_node(n_name).entity
        n_entity.set_nis_entity(nis)
        n_entity.set_network(nw)
        node_entities.append(n_entity)

    ne: 'NodeEntity'
    for ne in node_entities:
        ne.start() # let all the nodes be ready before the nis starts the first timeslot event.

    # start the controller/nis
    nis.start()

    # start the simulation
    run_stats = ns.sim_run()
    # nis.epr_track_print()
    nis.save_exp_results()
    print(run_stats)

if __name__ == '__main__':
    main()