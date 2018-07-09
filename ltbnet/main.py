"""Main function of the LTBNet executable"""

import argparse
from ltbnet.network import Network
from ltbnet.parser import parse_config_csv

from mininet.net import Mininet
from mininet.cli import CLI
from mininet import log


def main(*args, **kwargs):
    """LTBNet Main function"""
    parser = argparse.ArgumentParser(description="CURENT LTB network emulator")
    parser.add_argument('config', help='PMU network configuration file in csv format')
    parser.add_argument('--verbose', '-v', action='store_true', help='enable INFO level verbose logging')
    cli_args = parser.parse_args()

    if cli_args.verbose:
        log.setLogLevel('info')

    config = parse_config_csv(cli_args.config)
    network = Network().setup(config)

    net = Mininet(topo=network)

    if network.HwIntf.n:
        network.add_hw_intf(net)

    net.start()
    print('LTBNet Ready')

    network.PMU.run_pmu(net)

    CLI(net)

    net.stop()


if __name__ == '__main__':
    main()
