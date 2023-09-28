#!/usr/bin/env python

import sys
import traceback

from lib.network import Network

def main():
    network = Network()

    network.visualize()


if __name__ == '__main__':
    try:
        main()
        sys.exit(0) # successful termination
    except SystemExit:
        pass # for successful termination
    except:
        traceback.print_exc()
        sys.exit(1)