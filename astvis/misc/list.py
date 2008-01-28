
from astvis import event

class ObservableList(list):
    def append(self, value):
        list.append(self, value)
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                (None,event.PC_ADDED,value,None), {'index': len(self)-1})

