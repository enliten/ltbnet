import sys
import re

from mininet.topo import Topo
from mininet.link import Intf

from mininet import log
from mininet.node import Node

from ltbnet.utils import check_intf
from ltbnet.minipmu import MiniPMU


class Network(Topo):
    """Network configuration class"""
    def __init__(self):
        super(Network, self).__init__()
        self.Region = Region()
        self.Switch = Switch()
        self.PDC = PDC()
        self.Router = Router()
        self.PMU = PMU()
        self.Link = Link()
        self.HwIntf = HwIntf()

        self.components = []

    def add(self, config, **kwargs):
        for item in config:
            ty = item['Type']

            if hasattr(self, ty):
                self.__dict__[ty].add(**item)
                if ty not in self.components:
                    self.components.append(ty)

    def setup(self, config):
        """Convenient function wrapper to setup a network from config"""
        self.add(config)
        self.setup_by_region()
        self.build_mn_name()
        self.assign_ip()
        self.add_node_to_mn()
        self.add_link_to_mn()
        return self

    def dump(self, path=None):
        """Dump the configuration to a csv file"""
        f = open(path, 'w') if path else sys.stdout
        header = ['Idx', 'Type', 'Region', 'Name', 'Longitude', 'Latitude', 'Connections', 'MAC', 'IP']
        f.write(','.join(header))
        f.write('\n')

        for item in self.components:
            f.write(self.__dict__[item].dump())
            f.write('\n')
        f.close()

    def setup_by_region(self):
        """Set up component information in Regions. Store PMU.idx in Region.pmu for each region"""

        for item in self.components:
            if not hasattr(self.Region, item):
                continue

            self.Region.__dict__[item] = [list() for _ in range(self.Region.n)]

            for i in range(self.__dict__[item].n):
                name = self.__dict__[item].name[i]
                idx= self.__dict__[item].idx[i]
                region = self.__dict__[item].region[i]

                if region in self.Region.idx:
                    loc = self.Region.name.index(region)
                else:
                    log.error('Region <{r}> of {comp} <{name}> is undefined.'.format(r=region, comp=item, name=name))
                    continue

                self.Region.__dict__[item][loc].append(idx)

    def build_mn_name(self):
        """Build Mininet node names for the components"""
        for item in self.components:
            self.__dict__[item].build_mn_name()

    def assign_ip(self, base='192.168.1.'):
        """Assign IP address in a LAN"""

        # for item in self.components:
        #     self.__dict__[item].ip = [''] * self.__dict__[item].n

        count = 1

        # for PDCs
        # self.PDC.ip = [''] * self.PDC.n
        for i in range(self.PDC.n):
            count += 1
            if self.PDC.ip[i]:
                continue
            self.PDC.ip[i] = base + str(count)

        # for PMUs
        # self.PMU.ip = [''] * self.PMU.n
        for i in range(self.PMU.n):
            count += 1
            if self.PMU.ip[i]:
                continue

            self.PMU.ip[i] = base + str(count)

    def add_node_to_mn(self):
        for item in self.components:
            # log.info('Adding {n} <{ty}> to the network...'.format(n=self.__dict__[item].n, ty=item))
            self.__dict__[item].add_node_to_mn(self)

    def add_link_to_mn(self):
        for item in self.components:
            # log.info('Adding links to {ty}...'.format(ty=item))
            self.__dict__[item].add_link_to_mn(self)

    def to_canonical(self, idx):
        if idx in self.Switch.idx:
            return self.Switch.mn_name[self.Switch.idx.index(idx)]
        else:
            return idx

    def add_hw_intf(self, net):
        """Add hardware interfaces from Network.HwIntf records"""
        for i, name, connect in zip(range(self.HwIntf.n), self.HwIntf.name, self.HwIntf.connections):
            for c in connect:
                switch_index = self.Switch.lookup_index(c)
                log.info('*** Adding hardware interface', name, 'to switch', c, '\n')
                r = Intf(name, node=net.switches[switch_index])


class Record(object):
    """Base class for config.csv records"""
    def __init__(self):
        self._name = type(self).__name__

        self.n = 0
        self.idx = []
        self.name = []
        self.coords = []
        self.mac = []
        self.pmu_idx = []
        self.delay = []
        self.bw = []
        self.jitter = []
        self.loss = []
        self.ip = []
        self.region = []
        self.prefix = ''
        self.connections = []
        self.mn_name = []
        self.mn_object = []

        self.build()

    def build(self):
        """Custom build function"""
        pass

    def add(self, Type=None, Longitude=None, Latitude=None, MAC=None,
            Idx=None, Name='', Region='', Links='', IP='',
            PMU_IDX='', Delay='', BW='', Loss='', Jitter='', **kwargs):

        if not self._name:
            log.error('Device name not initialized')
            return

        if Type != self._name:
            return

        mac = None if MAC == 'None' else MAC
        idx = self._name + '_' + str(self.n) if not Idx else Idx
        pmu_idx = None if PMU_IDX == 'None' else int(PMU_IDX)

        if idx in self.idx:
            log.error('PMU Idx <{i}> conflict.'.format(i=idx))

        conn = None if Links == 'None' else Links.split()
        delay = None if Delay == 'None' else Delay.split()
        bw = None if BW == 'None' else BW.split()
        loss = None if Loss == 'None' else Loss.split()
        jitter = None if Jitter == 'None' else Jitter.split()

        if conn is not None:
            if delay is None:
                delay = [None] * len(conn)
            if bw is None:
                bw = [None] * len(conn)
            if loss is None:
                loss = [None] * len(conn)
            if jitter is None:
                jitter = [None] * len(conn)

            assert len(conn) == len(delay), "{}: len(Links)={} does not match len(delay)={}".format(idx, len(conn), len(delay))
            assert len(conn) == len(bw), "{}: len(Links)={} does not match len(bw)={}".format(idx, len(conn), len(bw))
            assert len(conn) == len(loss), "{}: len(Links)={} does not match len(loss)={}".format(idx, len(conn), len(loss))
            assert len(conn) == len(jitter), "{}: len(Links)={} does not match len(jitter)={}".format(idx, len(conn), len(jitter))

        self.name.append(Name)
        self.region.append(Region)
        self.coords.append((float(Latitude), float(Longitude)))
        self.ip.append(IP)

        self.mac.append(mac)
        self.idx.append(idx)
        self.connections.append(conn)
        self.pmu_idx.append(pmu_idx)
        self.delay.append(delay)
        self.bw.append(bw)
        self.loss.append(loss)
        self.jitter.append(jitter)

        self.n += 1

    def lookup_index(self, idx, canonical=False):
        """Return the numerical index of the the element `idx`"""
        records = self.idx
        if canonical:
            records = self.mn_name

        if idx not in records:
            return -1
        return records.index(idx)

    def dump(self):
        """Return a string of the dumped records in csv format"""
        ret = []

        for i in range(self.n):
            conn = self.connections[i]
            if isinstance(conn, list):
                conn = ' '.join(conn)

            line = [self.idx[i],
                    self._name,
                    self.region[i],
                    self.name[i],
                    str(self.coords[i][1]),
                    str(self.coords[i][0]),
                    conn if conn else 'None',
                    self.mac[i] if self.mac[i] else 'None',
                    self.ip[i] if self.ip[i] else 'None',
                    self.pmu_idx[i] if self.pmu_idx[i] else 'None',
                    ]
            ret.append(','.join(line))

        return '\n'.join(ret)

    def build_mn_name(self):
        """Build names to be used in Mininet"""
        self.mn_name = [''] * self.n
        for i in range(self.n):
            self.mn_name[i] = self.prefix + self.idx[i]

    def check_consistency(self):
        """Check consistency of Region definitions"""
        pass

    def add_node_to_mn(self, network):
        """Method to add all elements to a Mininet Topology"""
        if self._name not in ('Switch', 'Router', 'PDC', 'PMU'):
            return

        for i, name, ip in zip(range(self.n), self.mn_name, self.ip):
            if self._name == 'Switch':
                n = network.addSwitch(name)
                self.mn_object.append(n)
            else:
                n = network.addHost(name, ip=ip)
                self.mn_object.append(n)
                # log.debug('Adding {ty} <{n}, {ip}> to network.'.format(ty=self._name, n=name, ip=ip))

    def add_link_to_mn(self, network):
        """Method to add links from each element to the connections"""

        for i, name, connect, delay, bw, loss, jitter in \
                zip(range(self.n), self.mn_name, self.connections, self.delay, self.bw, self.loss, self.jitter):

            if not connect:
                continue

            for i, c in enumerate(connect):
                # if c is a switch, look up its canonical name
                c = network.to_canonical(c)

                # check for optional link configs
                d = delay[i]
                b = float(bw[i]) if bw[i] is not None else None
                l = float(loss[i]) if loss[i] is not None else None
                j = float(jitter[i]) if jitter[i] is not None else None

                if not network.Link.exist_undirectioned(name, c):
                    r = network.addLink(name, c, delay=d, bw=b, loss=l, jitter=j)
                    # register the link element to the LTBNet object
                    network.Link.add(name, c, r)
                    # log.debug('Adding link <{fr}> to <{to}>.'.format(fr=name, to=c))
                else:
                    continue


class Region(Record):
    """Data streaming Region class"""
    def build(self):
        self.Switch = []  # list of network switches
        self.Router = []  # list of network routers
        self.PMU = []
        self.PDC = []


class PMU(Record):
    """Data streaming PMU node class"""
    def run_pmu(self, network):
        """Run pyPMU on the defined PMU nodes"""
        print(self.name)
        run_minipmu = 'minipmu {port} {pmu_idx} -n={name}'
        for i in range(self.n):
            name = self.mn_name[i]
            node = network.get(name)
            pmu_name = self.name[i]
            pmu_idx = self.pmu_idx[i]

            if pmu_name[:4] != 'PMU_':
                pmu_name = 'PMU_' + name
            call_str = run_minipmu.format(port=1410,
                                          pmu_idx=pmu_idx,
                                          name=pmu_name,
                                          )

            node.popen(call_str)  # TODO: Get bus idx by PMU name


class PDC(Record):
    """Data streaming PDC class"""
    pass


class Switch(Record):
    """Data streaming network switch class"""

    def build_mn_name(self):
        """Build canonical switch name such as `s23`"""
        self.mn_name = [''] * self.n
        for i in range(self.n):
            self.mn_name[i] = 's' + str(i)


class Router(Record):
    """Data streaming network router class"""
    pass


class Link(object):
    """Link storage"""
    def __init__(self):
        self.links = []
        self.idx = []

    def add(self, fr, to, idx):
        self.links.append((fr, to))
        self.idx.append(idx)

    def exist_undirectioned(self, fr, to):
        """Check if the undirectional path from `fr` to `to` exists"""

        if self.exist_directioned(fr, to) or self.exist_directioned(to, fr):
            return True
        else:
            return False

    def exist_directioned(self, fr, to):
        """Check if the directional path from `fr` to `to` exists"""
        ret = False
        if (fr, to) in self.links:
            ret = True

        return ret


class HwIntf(Record):
    """Hardware Interface class"""
    def add_link_to_mn(self, network):
        pass
