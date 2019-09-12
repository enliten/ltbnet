from andes_addon.dime import Dime

dimec = Dime('ISLANDING', 'tcp://192.168.1.200:5000')
dimec.start()

event = {'id': [143, 146, 135],
         'name': ['Line', 'Line', 'Line'],
         'time': [-1, -1, -1],
         'duration': [0, 0, 0],
         'action': [0, 0, 0]
         }

dimec.send_var('sim', 'Event', event)

dimec.exit()
