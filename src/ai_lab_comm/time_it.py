from functools import wraps
from functools import wraps
from time import time

from log_util import Log

log = Log(__name__).getlog()


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        log.info("func:%r args:[.....] took: %2.4f sec" % (f.__name__, te - ts))
        return result

    return wrap
