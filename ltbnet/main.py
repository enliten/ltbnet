"""Main function of the LTBNet executable"""

import os
import argparse

from ltbnet.network import Network
from ltbnet.parser import parse_config
from ltbnet.graph import make_graph, draw_shortest_path, plt

from mininet import log

from mininet.node import ( Node, Host, OVSKernelSwitch, DefaultController, RemoteController,
                           Controller )

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI


def main(*args, **kwargs):
    """LTBNet Main function"""
    parser = argparse.ArgumentParser(description="CURENT LTB network emulator")
    parser.add_argument('config', help='PMU network configuration file in csv format')
    parser.add_argument('-c', dest='clean', action='store_true',
                        help='clean MiniPMU and Mininet processes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='enable INFO level verbose logging')
    parser.add_argument('--runpmu', help='run LTBPMU processes on the specified PMU hosts',
                        action='store_true')
    parser.add_argument('--graph', help='show graph visualization', action='store_true')
    parser.add_argument('--source_node', help='name of the source node')
    parser.add_argument('--target_node', help='name of the destination node')

    parser.add_argument('--parse_only', help='parse the input file only without '
                                             'creating topology', action='store_true')

    parser.add_argument('--remote', '-r', action='store_true',
                        help='use remote controller (Ryu tested)')

    cli_args = parser.parse_args()

    if cli_args.verbose:
        log.setLogLevel('info')
    if cli_args.clean:
        clean()
        return

    config = parse_config(cli_args.config)
    network = Network().setup(config)

    if cli_args.graph:
        network_graph, node_pos = make_graph(network)
        if cli_args.source_node and cli_args.target_node:
            network_graph = draw_shortest_path(network_graph, node_pos,
                                               cli_args.source_node, cli_args.target_node)
        plt.show()

    if cli_args.parse_only:
        log.debug('Parse input file only. Exiting.')
        return

    if cli_args.remote:
        controller = RemoteController
    else:
        controller = DefaultController

    net = Mininet(topo=network, link=TCLink, controller=controller)

    if network.HwIntf.n:
        network.add_hw_intf(net)
    if network.TCHwIntf.n:
        network.add_tc_hw_intf(net)

    net.start()
    print('LTBNet Ready')
    if cli_args.runpmu:
        network.PMU.run_pmu(net)
    CLI(net)

    print('Stopping MiniPMUs - enter your root password if prompted')
    os.system("sudo pkill minipmu")
    net.stop()


def clean(*args, **kwargs):
    """Clean up MiniPmu processes and Mininet sessions"""
    os.system("sudo mn -c")
    os.system("sudo pkill minipmu")


if __name__ == '__main__':
    main()
