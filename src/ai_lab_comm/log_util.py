import os
import time
import logging


class Log(object):
    def __init__(self, logger=None, log_cate='search'):
        # 创建一个logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            formatter = logging.Formatter(
                '[%(asctime)s] %(filename)s:%(lineno)d process:%(process)d:%(threadName)s [%(levelname)s]%(message)s')
            ch.setFormatter(formatter)

            self.logger.addHandler(ch)
            ch.close()
        self.logger.propagate = False

    def getlog(self):
        return self.logger

log = Log(__name__).getlog()    