
def hashable(obj):
    try:
        hash(obj)
        return True
    except TypeError, e:
        return False

class _Hasher:
    def __init__(self, obj):
        self.__obj = obj
        
    def __hash__(self):
        return object.__hash__(self)
        
    def __eq__(self, other):
        return object.__eq__(self, other)
    
def makeHashable(obj):
    if hashable(obj):
        return obj
    
    
if __name__=="__main__":
    a = [3,5]
    ha1 = makeHashable(a)
    ha2 = makeHashable(a)
    d = dict()
    d[ha1] = 6
    d[4] = 7
    print d[ha2]

