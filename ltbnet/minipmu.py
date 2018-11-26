"""Python module to request PMU data from a running ANDES
"""

import logging
import time
import argparse
import numpy as np

from math import pi
from enum import Enum

from andes_addon.dime import Dime

from numpy import array, ndarray, zeros

from synchrophasor.pmu import Pmu
from synchrophasor.frame import ConfigFrame2, HeaderFrame

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

fh = logging.FileHandler('/var/log/minipmu.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

# ---- logging to console blocks MiniPMU when if in Mininet
# console = logging.StreamHandler()
# console.setFormatter(formatter)
# logger.addHandler(console)
# -----------------------------


class RecordState(Enum):
    """PMU record-replay state"""
    IDLE = 0
    RECORDING = 1
    RECORDED = 2
    REPLAYING = 3


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

        # for recording
        self.max_store_record = 30 * 600  # 600 seconds

        self.reset = True
        self.pmu_configured = False
        self.pmu_streaming = False

        self.reset_var()

        self.dimec = Dime(self.name, self.dime_address)
        self.pmu = Pmu(ip=pmu_ip, port=pmu_port)

    def reset_var(self, retain_data=False):
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

        self.fn = 60
        self.Vn = []

        self.Varheader = list()
        self.Idxvgs = dict()
        self.SysParam = dict()
        self.SysName = dict()
        self.Varvgs = ndarray([])

        self.t = ndarray([])
        self.data = ndarray([])
        self.count = 0

        # recording storage
        if not retain_data:
            self.t_record = ndarray([])
            self.data_record = ndarray([])
            self.count_record = 0
            self.counter_replay = 0  # replay index into `data_record` and `t_record`
            self.record_state = RecordState.IDLE

        self.last_data = None
        self.last_t = None

    def start_dime(self):
        """
        Starts the dime client stored in `self.dimec`
        """
        logger.info('Connecting to server at {}'.format(self.dime_address))
        assert self.dimec.start()

        logger.info('DiME client connected')

    def respond_to_sim(self):
        """
        DEPRECIATED: Respond with data streaming configuration to the simulator

        :return: None
        """
        pass

    def get_bus_name(self):
        """
        Return bus names based on ``self.pmu_idx`` and store bus names to
        ``self.bus_name``

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

        logger.debug('PMU names changed to: {}'.format(self.bus_name))
        return self.bus_name

    def get_bus_Vn(self):
        """
        Retrieve Bus.Vn

        Returns
        -------

        """
        self.Vn = [1] * len(self.pmu_idx)

        for i, idx in enumerate(self.pmu_idx):
            self.Vn[i] = self.SysParam['Bus'][idx][1] * 1000  # get Vn

        logger.info('Retrieved bus Vn {}'.format(self.Vn))

    def config_pmu(self):
        """
        Sets the ConfigFrame2 of the PMU

        :return: None
        """

        self.cfg = ConfigFrame2(pmu_id_code=self.pmu_idx[0],  # PMU_ID
                           time_base=1000000,  # TIME_BASE
                           num_pmu=1,  # Number of PMUs included in data frame
                           station_name=self.bus_name[0],  # Station name
                           id_code=self.pmu_idx[0],  # Data-stream ID(s)
                           data_format=(True, True, True, True),  # Data format - POLAR; PH - REAL; AN - REAL; FREQ - REAL;
                           phasor_num=1,  # Number of phasors
                           analog_num=1,  # Number of analog values
                           digital_num=1,  # Number of digital status words
                            channel_names=["V_PHASOR", "ANALOG1", "BREAKER 1 STATUS",
                            "BREAKER 2 STATUS", "BREAKER 3 STATUS", "BREAKER 4 STATUS", "BREAKER 5 STATUS",
                            "BREAKER 6 STATUS", "BREAKER 7 STATUS", "BREAKER 8 STATUS", "BREAKER 9 STATUS",
                            "BREAKER A STATUS", "BREAKER B STATUS", "BREAKER C STATUS", "BREAKER D STATUS",
                            "BREAKER E STATUS", "BREAKER F STATUS", "BREAKER G STATUS"],  # Channel Names
                           ph_units=[(0, 'v')],  # Conversion factor for phasor channels - (float representation, not important)
                           an_units=[(1, 'pow')],  # Conversion factor for analog channels
                           dig_units=[(0x0000, 0xffff)],  # Mask words for digital status words
                           f_nom=60.0,  # Nominal frequency
                           cfg_count=1,  # Configuration change count
                           data_rate=30)  # Rate of phasor data transmission)

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
        npmu = len(self.Idxvgs['Pmu']['vm'][0])

        self.var_idx['vm'] = [int(i) - 1 for i in self.pmu_idx]
        self.var_idx['am'] = [npmu + int(i) - 1 for i in self.pmu_idx]
        self.var_idx['w'] = [2 * npmu + int(i) - 1 for i in self.pmu_idx]

    @property
    def vgsvaridx(self):
        return array(self.var_idx['vm'] +
                     self.var_idx['am'] +
                     self.var_idx['w'], dtype=int)

    def init_storage(self, flush=False):
        """
        Initialize data storage `self.t` and `self.data`

        :return: if the storage has been reset
        """
        ret = False

        if self.count % self.max_store == 0:
            self.t = zeros(shape=(self.max_store, 1), dtype=float)
            self.data = zeros(shape=(self.max_store, len(self.pmu_idx * 3)),
                              dtype=float)
            self.count = 0
            ret = True
        else:
            ret = False

        if (self.count_record % self.max_store_record == 0) or (flush is True):
            self.t_record = zeros(shape=(self.max_store_record, 1),
                                  dtype=float)
            self.data_record = zeros(shape=(self.max_store_record,
                                     len(self.pmu_idx * 3)), dtype=float)
            self.count_record = 0
            self.counter_replay = 0

            ret = ret and True
        else:
            ret = False

        return ret

    def sync_and_handle(self):
        """
        Sync and call data processing functins

        :return:
        """
        ret = False

        var = self.dimec.sync()

        if var is False or None:
            return ret

        if self.reset is True:
            logger.info('[{name}] variable <{var}> synced.'
                        .format(name=self.name, var=var))

        data = self.dimec.workspace[var]

        if var in ('SysParam', 'Idxvgs', 'Varheader'):
            # only handle these three variables during reset cycle

            if self.reset is True:
                self.__dict__[var] = data
            else:
                logger.info('{} not handled outside reset cycle'.format(var))

        elif var == 'pmudata':
            # only handle pmudata during normal cycle
            if self.reset is False:
                # logger.info('In, t={:.4f}'.format(data['t']))
                self.handle_measurement_data(data)
            else:
                logger.info('{} not handled during reset cycle'.format(var))

        # handle SysName any time
        elif var == 'SysName':
            self.__dict__[var] = data
            self.get_bus_name()

        elif var == 'DONE' and data == 1:
            self.reset = True
            self.reset_var(retain_data=True)

        elif var == 'pmucmd' and isinstance(data, dict):
            cmd = ''
            if data.get('record', 0) == 1:
                # start recording
                if self.record_state == RecordState.IDLE \
                        or self.record_state == RecordState.RECORDED:

                    self.record_state = RecordState.RECORDING
                    cmd = 'start recording'
                else:
                    logger.warning('cannot start recording in state {}'
                                   .format(self.record_state))

            elif data.get('record', 0) == 2:
                # stop recording if started
                if self.record_state == RecordState.RECORDING:
                    cmd = 'stop recording'
                    self.record_state = RecordState.RECORDED
                else:
                    logger.warning('cannot stop recording in state {}'
                                   .format(self.record_state))

            if data.get('replay', 0) == 1:
                # start replay
                if self.record_state == RecordState.RECORDED:
                    cmd = 'start replay'
                    self.record_state = RecordState.REPLAYING
                else:
                    logger.warning('cannot start replaying in state {}'
                                   .format(self.record_state))
            if data.get('replay', 0) == 2:
                # stop replay but retain the saved data
                if self.record_state == RecordState.REPLAYING:
                    cmd = 'stop replay'
                    self.record_state = RecordState.RECORDED
                else:
                    logger.warning('cannot stop replaying in state {}'
                                   .format(self.record_state))
            if data.get('flush', 0) == 1:
                # flush storage
                cmd = 'flush storage'
                self.init_storage(flush=True)
                self.record_state = RecordState.IDLE

            if cmd:
                logger.info('[{name}] <{cmd}>'.format(name=self.name, cmd=cmd))

        else:
            logger.info('[{name}] {cmd} not handled during normal ops'
                        .format(name=self.name, cmd=var))

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

        # record
        if self.record_state == RecordState.RECORDING:
            self.data_record[self.count_record, :] = \
                    data['vars'][0, self.vgsvaridx].reshape(-1)

            self.t_record[self.count_record, :] = data['t']
            self.count_record += 1

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
                logger.info('[{name}] Entering reset mode..'
                            .format(name=self.name))

                while True:
                    var = self.sync_and_handle()

                    if var is False:
                        time.sleep(0.01)

                    if len(self.Varheader) > 0\
                            and len(self.Idxvgs) > 0\
                            and len(self.SysParam) > 0 \
                            and len(self.SysName) > 0:

                        self.find_var_idx()
                        self.get_bus_Vn()

                        break

                self.respond_to_sim()

                if self.pmu_configured is False:
                    self.config_pmu()
                    self.pmu_configured = True

                self.reset = False

            # logger.debug('Entering sync and short sleep...')

            var = self.sync_and_handle()
            time.sleep(0.001)

            if var is False:
                continue

            elif var == 'pmudata':
                if self.pmu.clients and not self.reset:

                    if self.record_state == RecordState.REPLAYING:
                        # prepare recorded data
                        npmu = len(self.pmu_idx)
                        v_mag = self.data_record[self.counter_replay, :npmu] * self.Vn[0]
                        v_ang = wrap_angle(self.data_record[self.counter_replay, npmu:2*npmu])
                        v_freq = self.data_record[self.counter_replay, 2*npmu:3*npmu] * self.fn
                        self.counter_replay += 1

                        # at the end of replay, reset
                        if self.counter_replay == self.count_record:
                            self.counter_replay = 0
                            self.record_state = RecordState.RECORDED

                    else:
                        # use fresh data
                        v_mag = self.last_data[0, self.var_idx['vm']] * self.Vn[0]
                        v_ang = wrap_angle(self.last_data[0, self.var_idx['am']])
                        v_freq = self.last_data[0, self.var_idx['w']] * self.fn

                    # TODO: add noise to data

                    try:
                        # TODO: fix multiple measurement (multi-bus -> one PMU case)
                        self.pmu.send_data(phasors=[(v_mag, v_ang)],
                                           analog=[9.99],
                                           digital=[0x0001],
                                           #freq=(v_freq-60)*1000
                                           freq = v_freq
                                           )

                        # logger.info('Out, f={f:.5f}, vm={vm:.1f}, am={am:.2f}'.format(f=v_freq[0], vm=v_mag[0], am=v_ang[0]))

                    except Exception as e:
                        logger.exception(e)


def wrap_angle(a):
    """
    Wrap angle to within [-pi, pi]

    Parameters
    ----------
    a : float
        angle value in radian

    Returns
    -------

    """
    while a > pi:
        a -= pi

    while a < -pi:
        a += pi

    return a


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='MiniPMU',
                        help='PMU instance name', type=str)
    parser.add_argument('-a', '--dime_address',
                        default='tcp://192.168.1.200:5000',
                        help='DiME server address')
    parser.add_argument('--fn', default=60,
                        help='nominal frequency (Hz)', type=int)
    parser.add_argument('--vn', default=1, help='voltage base (kV)')
    parser.add_argument('--noise', default=0, help='noise level', type=int)
    parser.add_argument('pmu_port', help='PMU TCP/IP port', type=int)
    parser.add_argument('pmu_idx',
                        help='PMU indices from ANDES in list', type=str)

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
