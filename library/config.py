import json
import logging
from collections import defaultdict
from configparser import ConfigParser


class AbstractConfig(defaultdict):

    def __init__(self):
        super().__init__(dict)


class ConfigIni(AbstractConfig):

    def read(self, file_path):  # todo
        conf = ConfigParser()
        read = conf.read(file_path, encoding='utf-8')
        if read:
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


class ConfigJson(AbstractConfig):

    def read(self, file_path):
        with open(file_path, 'r') as json_file:
            json_obj = json.loads(json_file.read())
        if json_obj:
            for section in json_obj.keys():
                for key in json_obj[section].keys():
                    self[section][key] = json_obj[section][key]
            return True
        else:
            logging.error('Can\'t read config file')
            return False
