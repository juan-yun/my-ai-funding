from functools import wraps
from functools import wraps
from time import time

from ai_lab_comm.log_util import log


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        log.info("func:%r args:[.....] took: %2.4f sec" % (f.__name__, te - ts))
        return result

    return wrap
