# LTBNet - Network Emulation and PMU Streaming

## Introduction

LTBNet is communication network emulator for power system applications. It 
can be used to a) define the topology of a communication network, b)stream 
measurement data between hosts, and c) stream power system control commands.

The LTBNet configuration links the communication network components with the 
power system measurement devices. Components in the communication network, 
including hosts, links, switches and routers define the network topology, 
while the PMU and PDC hosts define the measurement data streaming hierarchy.

## Installation

Recommended Environment:
  - Ubuntu 16.04.5 with Python 3.5
  - [Mininet Fork](https://github.com/cuihantao/mininet/tree/py3) 
  - [PyPMU Fork](https://github.com/cuihantao/pypmu)

LTBNet is built on top of Mininet and PyPMU. It is recommended to install the 
provided forks. Note that the earlier versions of Mininet without Python 3 
support will not work. The PyPMU fork also have some important changes.

Mininet can only run on Linux systems. We recommend Ubuntu 16.04.5 LTS. 
Follow the 
[instructions here (Option 2)](http://mininet.org/download/#option-2-native-installation-from-source)
to install Mininet on a fresh environment. You will need superuser access to 
install and run Mininet.

PyPMU can be installed by running `pip install .` in the PyPMU project 
directory. PyPMU only works in Python 3.

Finally, LTBNet can be installed with `pip install .` in the LTBNet project 
directory. The installation will attempt to create two console entry points: 
`ltbnet` and `minipmu`.

`ltbnet` is the main program to create a communication network topology and 
instantiate PMU instances. `minipmu` is an independent program to create a 
PMU instance that a) receives data from [ANDES](https://github.com/cuihantao/andes)
through DiME, and b) implements the IEEE C37.118-2011 protocol for data 
streaming over TCP/IP.

## Configuration Files
Example configuration files can be found in the folder `data`. A 
configuration file defines how the network should be created. 

### File format
Two formats are currently supported: CSV and JSON. We are migrating from CSV 
to JSON as the latter offers more flexibility. 

The fields in the CSV or the JSON file annotates the components. For each 
component, `Type` is an identifier of the type of the device. Supported 
values for `Type` and their meaning are the follows:

 - Region: power system region, which generally contains one PDC and 
 multiple PMUs
 - Switch: network switch
 - Router: network router
 - PMU: phasor data concentrator. A PDC concentrates data within the region 
 and sends data to other PDCs when requested
 - PMU: phasor measurement unit. A PMU measures the bus voltage, frequency 
 (and possibly but not implemented, current)at the given bus (es)
 - HwIntf: hardware interface. Allow to attach hardware interface to the 
 emulated network

A complete table of the supported fields for each type of component is listed 
below.

|           | Region            | Switch                    | Router | PMU                  | PDC | HwIntf            |
|-----------|-------------------|---------------------------|--------|----------------------|-----|-------------------|
| Idx       | unique identifier | <                         | <      | <                    | <   | <                 |
| Region    | region name       | <                         | <      | <                    | <   | <                 |
| Name      | instance name     | <                         | <      | <                    | <   | ifconfig NIC name |
| Longitude | longitude value   | <                         | <      | <                    | <   | <                 |
| Latitude  | Latitude value    | <                         | <      | <                    | <   | <                 |
| Links     | -                 | space-sep Idx of upstream | <      | <                    | <   | <                 |
| MAC       | -                 | MAC address               | <      | <                    | <   | -                 |
| IP        | -                 | IP address                | <      | <                    | <   | -                 |
| PMU_IDX   | -                 | -                         | -      | idx of the ANDES PMU | -   | -                 |
| Delay     | -                 | delay on the links        | <      | <                    | <   | <                 |
| BW        | -                 | bandwidth in Mbps         | <      | <                    | <   | <                 |
| Loss      | -                 | data loss rate in %       | <      | <                    | <   | <                 |
| Jitter    | -                 | jitter rate in %          | <      | <                    | <   | <                 |

Note:
 - `<` means the same as the left
 - `-` means not applicable. In CSV files, the field should be filled with 
 literal `None`
 - `Links` specifies the names of the linked components, separated by space. 
 For example, if switch `s1` has `Links="s0 s2"`, it means switch `s1` is 
 connected to `s0` and `s2`
 - The fields `Delay`, `BW`, `Loss` and `Jitter` applies wherever `Links` is 
 not empty. Use literal `None` if not specified. Use space to separate the 
 same number of data as in `Links`.
 - `Delay` is a string with a value and a unit. For example, a 5 millisecond 
 delay is represented as `5ms`  

### Using the config file
The config file is to be used by the `ltbnet` command-line program. To start 
a network using config file `config_9pmu.json`, run the following:

```bash
sudo ltbnet config_9pmu.json -v
```

This enables the verbose mode of LTBNet.

> $ sudo ltbnet config_9pmu.csv -v
>
> *** Creating network
>
> *** Adding controller
>
> *** Adding hosts:
>
> C_AESO C_BCTC DEVERS1 DEVERS2 DEVERS3 DEVERS4 DEVERS5 DEVERS6 DEVERS7 DEVERS8 DEVERS9 
>
> *** Adding switches:
>
> s0 s1 
>
> *** Adding links:
>
> (C_AESO, s0) (C_BCTC, s1) (DEVERS1, s0) (DEVERS2, s0) (DEVERS3, s0) (DEVERS4, s0) (DEVERS5, s0) (DEVERS6, s0) (DEVERS7, s0) (DEVERS8, s0) (DEVERS9, s0) (10.00Mbit) (10.00Mbit) (s1, s0) 
>
> *** Configuring hosts
>
> C_AESO C_BCTC DEVERS1 DEVERS2 DEVERS3 DEVERS4 DEVERS5 DEVERS6 DEVERS7 DEVERS8 DEVERS9 
>
> *** Adding hardware interface enp4s0f0 to switch S_BCTC 
>
> *** Starting controller
>
> c0 
>
> *** Starting 2 switches
>
> s0 s1 ...(10.00Mbit) (10.00Mbit) 
>
> LTBNet Ready
>
> ['DEVERS1', 'DEVERS2', 'DEVERS3', 'DEVERS4', 'DEVERS5', 'DEVERS6', 'DEVERS7', 'DEVERS8', 'DEVERS9']
>
> *** Starting CLI:

To exit, run `exit()` in the Mininet command line window:

> mininet> exit()
>
> *** Stopping 1 controllers
>
> c0 
>
> *** Stopping 12 links
>
> ............
>
> *** Stopping 2 switches
>
> s0 s1 
>
> *** Stopping 11 hosts
>
> C_AESO C_BCTC DEVERS1 DEVERS2 DEVERS3 DEVERS4 DEVERS5 DEVERS6 DEVERS7 DEVERS8 DEVERS9 
>
> *** Done

To run a MiniPMU in standalone mode, please refer to `minipmu -h`.

## Package Structure

The LTBNet package is structured as follows:

 * [bin](./bin)
   * [python3-sudo.sh](./bin/python3-sudo.sh) sudo python for debugging
 * [data](./data)
   * [config_9pmu.csv](./data/config_9pmu.csv)
   * [config_9pmu.json](./data/config_9pmu.json)
   * [config_wecc.csv](./data/config_wecc.csv)
   * [config_wecc.json](./data/config_wecc.json)
 * [ltbnet](./ltbnet)
   * [main.py](./ltbnet/main.py) main orchestrator script
   * [minipmu.py](./ltbnet/minipmu.py) minipmu program for creating PMU instances
   * [network.py](./ltbnet/network.py) LTBNet topology manager
   * [parser.py](./ltbnet/parser.py) data parser
   * [utils.py](./ltbnet/utils.py) utility functions

## License, Authors, Contributors and Acknowledgement
LTBNet is released under GNU General Public License 3. See LICENSE.

Author: Hantao Cui (hcui7@utk.edu)

Contributors: Kellen Oleksak

This work was supported in part by the Engineering Research Center Program of 
the National Science Foundation and the Department of Energy under NSF 
Award Number EEC-1041877 and the CURENT Industry Partnership Program.
