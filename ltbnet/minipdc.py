"""
tinyPDC will connect to pmu_ip:pmu_port and send request
for header message, configuration and eventually
to start sending measurements.
"""

from synchrophasor.pdc import Pdc
from synchrophasor.frame import DataFrame
from multiprocessing import Process, Pipe, Queue

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

fh = logging.FileHandler('/var/log/minipdc.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


iplist = []
iplist.append('192.168.1.1')
iplist.append('192.168.1.19')
iplist.append('192.168.1.34')
iplist.append('192.168.1.55')
iplist.append('192.168.1.73')
iplist.append('192.168.1.91')
iplist.append('192.168.1.109')
iplist.append('192.168.1.127')
iplist.append('192.168.1.145')
iplist.append('192.168.1.163')
npmu = len(iplist)


if __name__ == "__main__":
    pdc = dict()
    header = dict()
    config = dict()

    for idx, item in enumerate(iplist):
        pmu_idx = int(iplist[idx].split()[3])

        pdc[idx] = Pdc(pdc_id=pmu_idx,
                       pmu_ip=iplist[idx],
                       pmu_port=1410)

        pdc[idx].logger.setLevel("DEBUG")

    for idx, item in pdc.items():  # each item is a PDC

        item.run()   # Connect to PMU

        header[idx] = item.get_header()
        config[idx] = item.get_config()

    for idx, item in pdc.items():  # each item is a PDC
        item.start()  # Request to start sending measurements

    # create result queues

    result_queue = [Queue() for x in range(npmu)]

    # start data acquisition processes
    acq_proc = {}

    for idx, item in pdc.items():
        acq_proc[idx] = Process(target=item.get_msg, args=(result_queue[idx]))

    for idx, item in pdc.items():
        acq_proc[idx].start()

    while True:

        for item in result_queue:
            result = item.get()
            if isinstance(result, DataFrame):
                print(result.get_measurements())



        # Test = []
        #
        # result_queue = Queue()
        # result_queue1 = Queue()
        # result_queue2 = Queue()
        #
        # data1 = Process(target=pdc1.get_msg, args=(result_queue,))
        #
        # data1.start()
        # results = result_queue.get()
        # if type(results) == DataFrame:
        #     print(results.get_measurements())
        # data1.terminate()
        # data1.join()
        #
        # data2 = Process(target=pdc2.get_msg, args=(result_queue1,))
        # data2.start()
        # results1 = result_queue1.get()
        # if type(results1) == DataFrame:
        #     print(results1.get_measurements())
        # data2.terminate()
        # data2.join()
        #
        # data3 = Process(target=pdc3.get_msg, args=(result_queue2,))
        # data3.start()
        # results2 = result_queue2.get()
        # if type(results2) == DataFrame:
        #     print(results2.get_measurements())
        # data3.terminate()
        # data3.join()