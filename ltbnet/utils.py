import re
from mininet import log

from mininet.util import quietRun


def check_intf(intf):
    "Make sure intf exists and is not configured."
    config = quietRun( 'ifconfig %s 2>/dev/null' % intf, shell=True )
    if not config:
        log.error( 'Error:', intf, 'does not exist!\n' )
        exit(1)
    ips = re.findall( r'\d+\.\d+\.\d+\.\d+', config )
    if ips:
        log.error( 'Error:', intf, 'has an IP address,'
               'and is probably in use!\n' )
        exit( 1 )
