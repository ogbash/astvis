
def hashable(obj):
    try:
        hash(obj)
        return True
    except TypeError, e:
        return False
