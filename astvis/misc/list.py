
from astvis import event

class ObservableList(list):
    def append(self, value):
        list.append(self, value)
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                (None,event.PC_ADDED,value,None), {'index': len(self)-1})

class ObservableDict(dict):
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                (None,event.PC_CHANGED,value,None), {'key': key})
        
if __name__=='__main__':
    d = ObservableDict()
    d[2] = 4
    print d
