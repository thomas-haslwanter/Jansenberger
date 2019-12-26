import socket
import ngimu

def test_init():
    sensor = ngimu.NGIMU()
    sensor.close()
    assert(sensor.address[1] == 9000)    
    
def test_getData():
    sensor = ngimu.NGIMU()
    lengths = [10, 3, 3, 3, 1, 4]
    selection_types = ['data', 'acc', 'gyr', 'mag', 'bar', 'quat']
    for length, selection in zip(lengths, selection_types):
        measurement = sensor.get_data(selection)
        assert( len(measurement) == length )
    sensor.close()
    
