"""Main function of the LTBNet executable"""

import os

import argparse
from ltbnet.network import Network
from ltbnet.parser import parse_config
from mininet.link import TCLink

from mininet.net import Mininet
from mininet.cli import CLI
from mininet import log


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
    cli_args = parser.parse_args()

    if cli_args.verbose:
        log.setLogLevel('info')
    if cli_args.clean:
        clean()
        return

    config = parse_config(cli_args.config)
    network = Network().setup(config)

    net = Mininet(topo=network, link=TCLink)

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
