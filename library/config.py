import logging
from collections import defaultdict
from configparser import ConfigParser


class Config(defaultdict):
    def __init__(self):
        super().__init__(dict)

    def read(self, *file_paths):  # todo
        conf = ConfigParser()
        read = conf.read(file_paths, encoding='utf-8')
        if len(read) == len(file_paths):
            for section in conf.keys():
                for key in conf[section].keys():
                    for met in (conf.getint, conf.getfloat, conf.getboolean):
                        try:
                            value = met(section, key)
                            break
                        except ValueError:
                            continue
                    else:
                        value = conf.get(section, key)
                    self[section][key] = value
            return True
        else:
            logging.error('Can\'t read config file')
            return False
