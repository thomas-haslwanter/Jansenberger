# -*- coding: utf-8 -*-

"""
Jansenberger
"""

import yaml
from guidata.dataset.datatypes import (DataSet, BeginTabGroup, EndTabGroup,
                                       BeginGroup, EndGroup, ObjectItem)
from guidata.dataset.dataitems import (FloatItem, IntItem, BoolItem, ChoiceItem,
                             MultipleChoiceItem, ImageChoiceItem, FilesOpenItem,
                             StringItem, TextItem, ColorItem, FileSaveItem,
                             FileOpenItem, DirectoryItem, FloatArrayItem)

from guidata.dataset.qtwidgets import DataSetEditLayout, DataSetShowLayout
from guidata.dataset.qtitemwidgets import DataSetWidget



class DefaultParameters(DataSet):
    """
    Settings
    Instructions 'comment': <br>Plain text or
    <b>rich text</b> are both supported.
    """
    data_dir = DirectoryItem("Directory",'D:\\Users\\thomas\\Data\\CloudStation\\Projects\\IMUs\\Jansenberger\\data')

    _bg = BeginGroup("Time View")
    acc_limit = FloatItem("Limit [Accelerometer]", default=0.5, min=0, max=3, step=0.01, slider=True)                             
    gyr_limit = FloatItem("Limit [Gyroscope]", default=300, min=100, max=1000, step=1, slider=True)                             
    init_channel = ChoiceItem("Initial Channel", [(16, "acc"), (32, "gyr")], radio=True)
    _eg = EndGroup("Time View")

    _bcolor = BeginGroup("Traffic Light")
    color_top = ColorItem("Top", default="red")
    color_middle = ColorItem("Middle", default="#ffaa00")
    color_bottom  = ColorItem("Bottom", default="#00aa00")
    upper_thresh = FloatItem("Upper Threshold", default=0.7, min=0, max=2, step=0.01, slider=True)                             
    lower_thresh = FloatItem("Lower Threshold", default=0.3, min=0.1, max=1, step=0.01, slider=True)                             
    _ecolor = EndGroup("Colors")


    opening_view = ChoiceItem("Initial View", [(16, 'Time-View'), (32, "xy-View"), (64, 'TrafficLight-View')], radio=True)
    
if __name__ == "__main__":
    # Create QApplication
    import guidata
    _app = guidata.qapplication()
    
    e = DefaultParameters()
    print(e)
    if e.edit():
        defaults = {
        'accLim': e.acc_limit,
        'gyrLim': e.gyr_limit,
        'dataDir': e.data_dir,
        'topColor': e.color_top,
        'middleColor': e.color_middle,
        'bottomColor': e.color_bottom,
        'upper_thresh': e.upper_thresh,
        'lower_thresh': e.lower_thresh,
        'init_channel': e.init_channel,
        'opening_view': e.opening_view
        }
        settings_file = 'settings.yaml'
        with open(settings_file, 'w') as fh:
            yaml.dump(defaults, fh)
        print(f'New settings saved to {settings_file}')
        print(e)
        # e.view()
