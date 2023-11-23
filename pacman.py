#!/usr/bin/env python3
import logging
import sys
from argparse import ArgumentParser
from collections import defaultdict
from configparser import ConfigParser

from library.utils import Services
from library.view.debug_view import DebugView
from library.view.sound_engine import SoundEngine
from library.controller import Controller
from library.event import EventDispatcher
from library.interface import Interface, GraphicsTkinter
from library.model.game_driver import GameDriver
from library.resource_manager import ResourceManager
from library.view.game_view import View


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


def config_logging(config):
    handlers = [logging.StreamHandler(sys.stdout)]
    if config['debug']['is_debug']:
        handlers.append(logging.FileHandler('pacman.log'))
    logging.basicConfig(
        handlers=handlers,
        level=logging.INFO,
        format='[%(asctime)s.%(msecs)d][%(levelname)s] %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    return parser.parse_args()


def main():
    services = Services()
    services.config = Config()
    if not services.config.read('config'):
        logging.info('App terminated')
        return
    args = parse_args()
    services.config['debug']['is_debug'] |= args.debug
    config_logging(services.config)
    logging.info('App running')
    if services.config['debug']['is_debug']:
        logging.info('Debug mode enabled')
    services.event_dispatcher = EventDispatcher()
    services.resources = ResourceManager(services)
    graphics = GraphicsTkinter(services)
    interface = Interface(services, graphics)
    if not services.resources.load():
        logging.info('App terminated')
        return
    GameDriver(services)
    View(services, interface.get_canvas())
    if services.config['debug']['is_debug']:
        DebugView(services, interface.get_canvas())
    if services.config['view']['sound_enabled']:
        sound_engine = SoundEngine(services)
        sound_engine.initiate()
        sound_engine.run()
    Controller(services, interface.get_canvas())
    interface.run()


if __name__ == '__main__':
    main()
