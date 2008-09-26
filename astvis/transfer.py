
def externalize(obj):
    data = obj.__class__, obj.externalize()
    return data

def internalize(data):
    clazz, info = data
    return clazz.internalize(info)
