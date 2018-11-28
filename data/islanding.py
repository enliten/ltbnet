"""
tinyPDC will connect to pmu_ip:pmu_port and send request
for header message, configuration and eventually
to start sending measurements.
"""


from synchrophasor.pdc import Pdc
from synchrophasor.frame import DataFrame, HeaderFrame, \
        ConfigFrame1, ConfigFrame2, ConfigFrame3
from multiprocessing import Queue

import time
import logging

import numpy as np
import matplotlib.pyplot as plt

from andes_addon.dime import Dime

h1, = plt.plot([], [], linewidth=6, label='Frequency Deviation')
h2, = plt.plot([], [], linewidth=6, label='Separation Threshold')
mng = plt.get_current_fig_manager()
mng.full_screen_toggle()

ca = plt.gca()
ca.legend(fontsize=30)
ca.xaxis.set_tick_params(labelsize=30)
ca.yaxis.set_tick_params(labelsize=30)

plt.ion()
plt.show()
plt.pause(0.1)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

fh = logging.FileHandler('/var/log/minipdc.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

dimec = Dime('ISLANDING', 'tcp://192.168.1.200:5000')

ISLANDING = {'vgsvaridx': np.array([1, 2])}
ISLANDING_idx = {'fdev': np.array([1]), 'thresh': np.array([2])}
ISLANDING_vars = {'t': 0, 'vars': np.array([0, 0.4])}
ISLANDING_header = ['fdev_WECC', 'thresh_WECC']
ISLANDING_info = ''


class MiniPDC(object):
    """A MiniPDC connecting to multiple PMUs and a DiME server
    """
    def __init__(self, name, dime_address, ip_list, port_list=None,
                 loglevel=logging.INFO):
        self._name = name
        self._dime_address = dime_address
        self._loglevel = loglevel

        self.dimec = Dime(name, dime_address)
        self.ip_list = ip_list
        self.port_list = port_list  # not being used now

        # check if the lengths of `ip_list` and `port_list` match

        self.pdc = {}
        self.header = {}
        self.config = {}

        self.last_var = None
        # state flags
        self.andes_online = False
        # self.pdc_started = False

    @property
    def npmu(self):
        return len(self.ip_list)

    def initialize(self):
        """
        Reset or initialize, it is the same thing
        Returns
        -------

        """
        pass

    def sync_and_handle(self):
        """ Sync from DiME and handle the received data
        """
        self.last_var = self.dimec.sync()
        val = None

        if self.last_var not in (None, False):
            val = self.dimec.workspace[self.last_var]
        else:
            return

        if self.last_var == 'DONE' and int(val) == 1:
            self.andes_online = False
            self.initialize()
            pass
        return self.last_var

    def start_dime(self):
        logger.info('Connecting to DiME at {}'.format(self._dime_address))
        self.dimec.start()
        try:
            self.dimec.exit()
        except:
            pass
        self.dimec.start()
        logger.info('DiME connected')

    def init_pdc(self):

        for idx, item in enumerate(self.ip_list):
            pmu_idx = int(item.split('.')[3])

            self.pdc[idx] = Pdc(pdc_id=pmu_idx,
                                pmu_ip=self.ip_list[idx],
                                pmu_port=1410)

            self.pdc[idx].logger.setLevel("INFO")
        logger.info('PDC initialized')

    def get_header_config(self):
        for idx, item in self.pdc.items():  # each item is a PDC
            item.run()  # Connect to PMU

            self.header[idx] = item.get_header()
            self.config[idx] = item.get_config()

        for idx, item in self.pdc.items():  # each item is a PDC
            item.start()  # Request to start sending measurements
            self.pdc_started = True

        logger.info('PMU Header and ConfigFrame received')

    def collect_data(self):
        pass

    def process_data(self):
        pass

    def run(self):
        pass


class Islanding(MiniPDC):
    """System islanding class
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.result_queue = []
        self.result_dict = {}
        self.freq = {}
        self.freq_diff = 0

        self.freq_diff_array = np.array([0, 0.4])
        self.t_array = np.array([0])

        self.time_detect = 0
        self.detected = False
        self.islanded = False

        self.islanding_delay = 7
        self.event = {'id': [143, 146, 135],
                      'name': ['Line', 'Line', 'Line'],
                      'time': [-1, -1, -1],
                      'duration': [0, 0, 0],
                      'action': [0, 0, 0]
                      }

    def initialize(self):
        super(Islanding, self).initialize()
        self.result_queue = [Queue() for x in range(self.npmu)]
        self.result_dict = {}
        self.freq = {}
        self.freq_diff = 0
        self.time_detect = 0
        self.detected = False
        self.islanded = False

    def sync_and_handle(self):
        super(Islanding, self).sync_and_handle()

        if self.last_var == 'SysParam':
            val = self.dimec.workspace[self.last_var]
            if val is not None:
                self.andes_online = True
                self.dimec.send_var('sim', 'ISLANDING', ISLANDING)
                # self.dimec.broadcast('ISLANDING_idx', ISLANDING_idx)
                # self.dimec.broadcast('ISLANDING_header', ISLANDING_header)
            self.initialize()
        elif self.last_var == 'Varvgs':
            print(self.dimec.workspace['Varvgs']['t'])
        return self.last_var

    def update_draw(self, xdata, ydata):
        # TODO: remove the *2 in xdata
        h1.set_data(xdata * 2, ydata[:, 0])
        h2.set_data(xdata * 2, ydata[:, 1])

        ca.relim()
        ca.autoscale_view()

        plt.draw()
        plt.pause(0.0001)
        plt.show()

    def run(self):
        super(Islanding, self).run()
        self.start_dime()
        self.initialize()
        print('PDC and Islanding running.. Waiting for ANDES')
        while True:

            sf = self.sync_and_handle()

            # only start if ANDES is connected
            if self.andes_online is False:
                continue
            else:
                if len(self.config) == 0:
                    time.sleep(0.5)
                    self.init_pdc()
                    self.get_header_config()

            # retrieve all measurements from the PDCs
            for idx, item in self.pdc.items():
                item.get_msg(self.result_queue[idx])

            # for each PDC, retrieve the frequency
            for idx, item in enumerate(self.result_queue):

                self.result_dict[idx] = item.get()

                if self.result_dict[idx] is None:
                    self.freq[idx] = 60
                    continue

                frame = self.result_dict[idx]

                if isinstance(frame, HeaderFrame):
                    self.header[idx] = frame
                    continue

                elif isinstance(frame, (ConfigFrame3, ConfigFrame2, ConfigFrame1)):
                    self.config[idx] = frame
                    continue

                elif isinstance(frame, DataFrame):
                    measurements = frame.get_measurements()
                    if isinstance(measurements, dict):
                        self.freq[idx] = (measurements['measurements'][0]['frequency'] - 60) * 1000
                        # only the data received here goes to processing
                    else:
                        print('Unknown measurement type {}, continue'.format(type(measurements)))
                        continue

                else:
                    logger.info('ignored {} data'.format(type(frame)))
                    continue

            # detect frequency deviation

            if len(self.freq) == 0:
                continue

            self.freq_diff = max(self.freq.values()) - min(self.freq.values())
            if abs(self.freq_diff) < 1:
                print('Frequency difference = {}'.format(self.freq_diff))
            else:
                self.freq_diff = 0
                continue

            if self.detected is False:
                if self.freq_diff >= 0.4:
                    # record the *initial* time when frequency divergence is detected
                    self.detected = True
                    self.time_detect = time.time()
                    print('--> Frequency divergence detected. Islanding will happen in {}s'.format(self.islanding_delay))

            # impose a delay before islanding by comparing time() and time_detect

            elif self.detected and (not self.islanded):
                if time.time() - self.time_detect >= self.islanding_delay:
                    self.dimec.send_var('sim', 'Event', self.event)
                    print('--> Islanding initiated!!!')
                    self.islanded = True

            if sf == 'Varvgs':
                self.freq_diff_array = np.vstack((self.freq_diff_array,
                                                  np.array([[self.freq_diff, 0.4
                                                          ]]))
                          )
                self.t_array = np.hstack((self.t_array, self.dimec.workspace[sf]['t']))

                self.update_draw(self.t_array, self.freq_diff_array)

                ISLANDING_vars['t'] = self.dimec.workspace[sf]['t']
                ISLANDING_vars['vars'][0] = self.freq_diff
                # self.dimec.send_var('geovis', 'ISLANDING_vars', ISLANDING_vars)
                # print('ISLANDING_vars df={df} sent to geovis at t={t}'.format(df=self.freq_diff,
                #                                                               t=ISLANDING_vars['t']))


def run():
    ip_list = [#'192.168.1.1',
               #'192.168.1.19',
               '192.168.1.34',
               '192.168.1.55',
               #'192.168.1.73',
               #'192.168.1.91',
               #'192.168.1.109',
               #'192.168.1.127',
               #'192.168.1.145',
               #'192.168.1.163',
               ]
    islanding = Islanding(name='ISLANDING',
                          dime_address='tcp://192.168.1.200:5000',
                          ip_list=ip_list)

    islanding.run()


if __name__ == '__main__':
    run()
