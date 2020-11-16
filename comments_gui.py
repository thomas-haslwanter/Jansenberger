import guidata
_app = guidata.qapplication() # not required if a QApplication has already been created

import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di

    
class Processing(dt.DataSet):
    """Example"""
    quality = di.IntItem("Quality (1-3)", min=1, max=3, default=2)

    sel_list = ["very good", "middle", "bad"]
    qual = di.ChoiceItem("Processing algorithm", sel_list, default=1 )

    text = di.TextItem("Text")

param = Processing()
param.edit()

print(param.quality)
print(param.sel_list[param.qual])
print(param.text)

