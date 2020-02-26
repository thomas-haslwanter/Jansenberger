"""
Sensor-simulation

"""

# author:   Thomas Haslwanter & Seb Madgewick (code for data processing)
# date:     Jan-2020

import numpy as np


class Sensor():
    
    def __init__(self, port=8030, timeout=5, debug_flag=False):
        self.packetsize = 0
        self.address = (0,0)
        self.socket = 0
        self.messages = 0
        
    def close(self):
        return
    
    
    def get_data(self, selection):
        """Get the data from the NGIMU

        Parameters
        ----------
        selection : string
                    Must be one of the following:
                    * data : time, plus all measurement data (11,)
                    * gyr  : gyroscope [deg/s] (3,)
                    * acc  : accelerometer [g] (3,)
                    * mag  : magnetic field [uT] (3,)
                    * bar  : barometer [hPa] (1,)
                    * quat : quaternions (4,)
                    * dat_quat : data + quaternions (15,)
        Returns
        -------
        data : ndarray
               Row-vector, shape as indicated under "Parameters"
        """

                
        # from '/sensors'
        if selection[:3] == 'dat':
            data = np.random.randn(11)
        elif selection == 'gyr':
            data = np.random.randn(3)
        elif selection == 'acc':
            data = np.random.randn(3)
        elif selection == 'mag':
            data = np.random.randn(3)
        elif selection == 'bar':
            data = np.random.randn(1)
        elif selection == 'quat':
            # from '/quaternion'
            data = np.random.randn(4)
        else:
            raise TypeError(f'Do not know selection type {selection}')
        
        if selection == 'dat_quat':
            data = np.random.randn(15)

        return data
