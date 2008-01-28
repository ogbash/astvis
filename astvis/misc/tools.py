
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
        return object.__hash__(self.__obj)
        
    def __eq__(self, other):
        if isinstance(other, _Hasher):
            return self.__obj is other.__obj
        return self is other
        
    def __str__(self):
        return "Hasher{%s}" % self.__obj
    
def makeHashable(obj):
    if hashable(obj):
        return obj
    return _Hasher(obj)
    
    
if __name__=="__main__":
    a = [3,5]
    ha1 = makeHashable(a)
    ha2 = makeHashable(a)
    d = dict()
    d[ha1] = 6
    d[4] = 7
    print d[ha2]

