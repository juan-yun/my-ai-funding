import os
import configparser

from log_util import Log

log = Log(__name__).getlog()


class ConfigAgent:
    def __init__(self):
        self.config_path = None
        self.config_parser = configparser.ConfigParser()
        self.sections = []

    def load(self, config_path: str) -> bool:
        config_abs_path = os.path.abspath(config_path)
        if not os.path.exists(config_abs_path):
            log.warning(f"{config_abs_path} doesn't exists, please check it.")
            return False
        try:
            self.config_path = config_abs_path
            self.config_parser.read(self.config_path)
            self.sections = self.config_parser.sections()
        except BaseException as e:
            log.warning(f"load {config_path} failed, due to {e}")
            return False
        return True

    def sections(self) -> []:
        return self.sections

    def get_int(self, section_name: str, key_name: str) -> int:
        if section_name not in self.sections:
            log.warn(
                f"section {section_name} not exists in config:{self.config_path}, please check it."
            )
            return -1
        return int(self.config_parser.getint(section_name, key_name))

    def get_str(self, section_name: str, key_name: str) -> str:
        if section_name not in self.sections:
            log.warn(
                f"section {section_name} not exists in config:{self.config_path}, please check it."
            )
            return -1
        return self.config_parser.get(section_name, key_name)

    def get_float(self, section_name: str, key_name: str) -> float:
        if section_name not in self.sections:
            log.warn(
                f"section {section_name} not exists in config:{self.config_path}, please check it."
            )
            return -1
        return self.config_parser.getfloat(section_name, key_name)

    def get_bool(self, section_name: str, key_name: str) -> bool:
        if section_name not in self.sections:
            log.warn(
                f"section {section_name} not exists in config:{self.config_path}, please check it."
            )
            return -1
        return self.config_parser.getboolean(section_name, key_name)
