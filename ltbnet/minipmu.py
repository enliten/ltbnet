"""Python module to request PMU data from a running ANDES
"""

import logging
import time
import argparse

from andes.utils.dime import Dime

from numpy import array, ndarray, zeros

from synchrophasor.pmu import Pmu
from synchrophasor.frame import ConfigFrame2, HeaderFrame


def get_logger(name):
    # TODO: set logging level
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    if not logger.handlers:
        # Prevent logging from propagating to the root logger
        logger.propagate = 0
        console = logging.StreamHandler()
        fh = logging.FileHandler('minipmu.log')
        logger.addHandler(console)
        logger.addHandler(fh)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        console.setFormatter(formatter)
        fh.setFormatter(formatter)
    return logger


class MiniPMU(object):

    def __init__(self, name: str='', dime_address: str='ipc:///tmp/dime',
                 pmu_idx: list=list(), max_store: int=1000, pmu_ip: str='0.0.0.0', pmu_port: int=1410,
                 **kwargs):
        """
        Create a MiniPMU instance for PMU data streaming over Mininet.

        Assumptions made for

        Parameters
        ----------
        name
        dime_address
        pmu_idx
        max_store
        pmu_ip
        pmu_port
        kwargs
        """
        assert name, 'PMU Receiver name is empty'
        assert pmu_idx, 'PMU idx is empty'
        self.name = name
        self.dime_address = dime_address
        self.pmu_idx = pmu_idx
        self.max_store = max_store

        self.reset = True
        self.pmu_configured = False
        self.pmu_streaming = False

        self.reset_var()

        self.dimec = Dime(self.name, self.dime_address)
        self.logger = get_logger(self.name)
        self.pmu = Pmu(ip=pmu_ip, port=pmu_port)

    def reset_var(self):
        """
        Reset flags and memory
        :return: None
        """
        if not self.reset:
            return

        self.bus_name = []
        self.var_idx = {'am': [],
                        'vm': [],
                        'w': [],
                        }
        self.Varheader = list()
        self.Idxvgs = dict()
        self.SysParam = dict()
        self.SysName = dict()
        self.Varvgs = ndarray([])

        self.t = ndarray([])
        self.data = ndarray([])
        self.count = 0

        self.last_data = None
        self.last_t = None

    def start_dime(self):
        """
        Starts the dime client stored in `self.dimec`
        """
        self.logger.info('Connecting to server at {}'.format(self.dime_address))
        assert self.dimec.start()

        self.logger.info('DiME client connected')

    def respond_to_sim(self):
        """
        DEPRECIATED: Respond with data streaming configuration to the simulator

        :return: None
        """

        pass

    def get_bus_name(self):
        """
        Return bus names based on ``self.pmu_idx`` and store bus names to ``self.bus_name``

        :return: list of bus names
        """

        # assign generic bus names
        self.bus_name = list(self.pmu_idx)

        for i in range(len(self.bus_name)):
            self.bus_name[i] = 'Bus_' + str(self.bus_name[i])

        # assign names from SysName if present
        if len(self.SysName) > 0:
            for i in range(len(self.bus_name)):
                self.bus_name[i] = self.SysName['Bus'][self.pmu_idx[i] - 1]

        self.logger.debug('PMU names changed to: {}'.format(self.bus_name))
        return self.bus_name

    def config_pmu(self):
        """
        Sets the ConfigFrame2 of the PMU

        :return: None
        """

        self.cfg = ConfigFrame2(self.pmu_idx[0],  # PMU_ID
                           1000000,  # TIME_BASE
                           1,  # Number of PMUs included in data frame
                           self.bus_name[0],  # Station name
                           self.pmu_idx[0],  # Data-stream ID(s)
                           (True, True, True, True),  # Data format - POLAR; PH - REAL; AN - REAL; FREQ - REAL;
                           1,  # Number of phasors
                           1,  # Number of analog values
                           1,  # Number of digital status words
                           ["VA", "ANALOG1", "BREAKER 1 STATUS",
                            "BREAKER 2 STATUS", "BREAKER 3 STATUS", "BREAKER 4 STATUS", "BREAKER 5 STATUS",
                            "BREAKER 6 STATUS", "BREAKER 7 STATUS", "BREAKER 8 STATUS", "BREAKER 9 STATUS",
                            "BREAKER A STATUS", "BREAKER B STATUS", "BREAKER C STATUS", "BREAKER D STATUS",
                            "BREAKER E STATUS", "BREAKER F STATUS", "BREAKER G STATUS"],  # Channel Names
                           [(0, 'v')],  # Conversion factor for phasor channels - (float representation, not important)
                           [(1, 'pow')],  # Conversion factor for analog channels
                           [(0x0000, 0xffff)],  # Mask words for digital status words
                           60,  # Nominal frequency
                           1,  # Configuration change count
                           30)  # Rate of phasor data transmission)

        self.hf = HeaderFrame(self.pmu_idx[0],  # PMU_ID
                              "MiniPMU <{name}> {pmu_idx}".format(name=self.name, pmu_idx = self.pmu_idx))  # Header Message

        self.pmu.set_configuration(self.cfg)
        self.pmu.set_header(self.hf)
        self.pmu.run()

    def find_var_idx(self):
        """
        Returns a dictionary of the indices into Varheader based on
        `self.pmu_idx`. Items in `self.pmu_idx` uses 1-indexing.

        For example, if `self.pmu_idx` == [1, 2], this function will return
        the indices of
         - Idxvgs.Pmu.vm[0] and Idxvgs.Pmu.vm[1] as vm
         - Idxvgs.Pmu.am[0] and Idxvgs.Pmu.am[1] as am
         - Idxvgs.Bus.w_Busfreq[0] and Idxvgs.Bus.w_Busfreq[1] as w
        in the dictionary `self. var_idx` with the above fields.

        :return: ``var_idx`` in ``pmudata``
        """

        self.var_idx['vm'] = [3 * int(i) -3 for i in self.pmu_idx]
        self.var_idx['am'] = [3 * int(i) -2 for i in self.pmu_idx]
        self.var_idx['w'] = [3 * int(i) -1 for i in self.pmu_idx]

    @property
    def vgsvaridx(self):
        return array(self.var_idx['vm'] + self.var_idx['am'] + self.var_idx['w'], dtype=int)

    def init_storage(self):
        """
        Initialize data storage `self.t` and `self.data`

        :return: if the storage has been reset
        """

        if self.count % self.max_store == 0:
            self.t = zeros(shape=(self.max_store, 1), dtype=float)
            self.data = zeros(shape=(self.max_store, len(self.pmu_idx * 3)), dtype=float)
            self.count = 0
            return True
        else:
            return False

    def sync_and_handle(self):
        """
        Sync and call data processing functins

        :return:
        """
        ret = False

        var = self.dimec.sync()

        if var is False or None:
            return ret

        self.logger.debug('variable <{}> synced.'.format(var))
        data = self.dimec.workspace[var]

        if var in ('SysParam', 'Idxvgs', 'Varheader'):
            # only handle these three variables during reset cycle

            if self.reset is True:
                self.__dict__[var] = data
            else:
                self.logger.info('{} not handled outside reset cycle'.format(var))

        elif var == 'pmudata':
            # only handle pmudata during normal cycle
            if self.reset is False:
                self.logger.info('data received at t={}'.format(data['t']))
                self.handle_measurement_data(data)
            else:
                self.logger.info('{} not handled during reset cycle'.format(var))

        # handle SysName any time
        elif var == 'SysName':
            self.__dict__[var] = data
            self.get_bus_name()

        elif var == 'DONE' and data == 1:
            self.reset = True
            self.reset_var()

        else:
            self.logger.info('{} not handled during normal ops'.format(var))

        return var

    def handle_measurement_data(self, data):
        """
        Store synced data into self.data and return in a tuple of (t, values)

        :return: (t, vars)
        """
        self.init_storage()

        self.data[self.count, :] = data['vars'][0, self.vgsvaridx].reshape(-1)
        self.t[self.count, :] = data['t']

        self.count += 1

        self.last_data = data['vars']
        self.last_t = data['t']

        return data['t'], data['vars']

    def run(self):
        """
        Process control function

        :return None
        """
        self.start_dime()

        while True:

            if self.reset is True:
                # receive init and respond
                self.logger.debug('Entering reset mode...')

                while True:
                    var = self.sync_and_handle()

                    if var is False:
                        time.sleep(0.01)

                    if len(self.Varheader) > 0 and len(self.Idxvgs) > 0 and len(self.SysParam) > 0:
                        self.find_var_idx()
                        # attemp to sync SysName
                        var = self.sync_and_handle()
                        break

                self.respond_to_sim()

                if self.pmu_configured is False:
                    self.config_pmu()
                    self.pmu_configured = True

                self.reset = False

            self.logger.debug('Entering sync...')

            var = self.sync_and_handle()
            time.sleep(0.005)

            self.logger.debug('Entering sleep...')

            if var is False:
                continue

            elif var == 'pmudata':
                if self.pmu.clients and not self.reset:

                    try:
                        self.pmu.send_data(phasors=[(int(self.last_data[0, 1]),
                                                     int(self.last_data[0, 0]))],
                                           analog=[9.99],
                                           digital=[0x0001],
                                           freq=self.last_data[0, 2]
                                           )

                    except Exception as e:
                        self.logger.exception(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='MiniPMU', help='PMU instance name', type=str)
    parser.add_argument('-a', '--dime_address', default='ipc:///tmp/dime', help='DiME server address')
    parser.add_argument('pmu_port', help='PMU TCP/IP port', type=int)
    parser.add_argument('pmu_idx', help='PMU indices from ANDES in list', type=str)

    args = parser.parse_args()
    args = vars(args)

    if ',' in args['pmu_idx']:
        args['pmu_idx'] = args['pmu_idx'].split(',')
    else:
        args['pmu_idx'] = [args['pmu_idx']]
    for i in range(len(args['pmu_idx'])):
        args['pmu_idx'][i] = int(args['pmu_idx'][i])

    mini = MiniPMU(**args)
    mini.run()


if __name__ == "__main__":
    main()
