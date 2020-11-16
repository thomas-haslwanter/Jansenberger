import guidata
_app = guidata.qapplication() # not required if a QApplication has already been created

import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di

class Subjects(dt.DataSet):
    test_list = ['a', 'bc', 'de']
    
    exp_nr = di.ChoiceItem("Experimentors", test_list)
    sub_nr = di.ChoiceItem("Subjects", test_list)
    
    
class Processing(dt.DataSet):
    """Example"""
    a = di.FloatItem("Parameter #1", default=2.3)
    b = di.IntItem("Parameter #2", min=0, max=10, default=5)
    sel_list = ["type 1", "type 2", "type 3"]
    type = di.ChoiceItem("Processing algorithm", sel_list )

param = Processing()
param.edit()

print(param.a)
print(param.sel_list[param.type])

p = Subjects()      # "p" for "persons"
p.edit()
