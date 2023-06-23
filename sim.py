#!/usr/bin/env python 

import sys
import traceback
from lib.graphs import QONgraph as graphs
from types import ModuleType
import argparse
import importlib

def get_args(argv):
    # parser initialization:
    parser = argparse.ArgumentParser(description="QON Simulator")

    # parameter for config file
    parser.add_argument('-c', '--config', required=False, default='config', type=str)

    args = parser.parse_args()

    return args

def main(argv):
    # parse command-line args
    args = get_args(argv)   
    
    graph = graphs(args.config)
    
    # graph.save_graph()
    graph.show_graph()

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
        sys.exit(0) # successful termination
    except SystemExit:
        pass # for successful termination
    except:
        traceback.print_exc()
        sys.exit(1)