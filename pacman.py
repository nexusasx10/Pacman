#!/usr/bin/env python3
import logging
import sys
from argparse import ArgumentParser

from engine.typemap import TypeMap
from library.config import AbstractConfig, ConfigJson
from library.view.debug_view import DebugView
from library.view.sound_engine import SoundEngine
from library.controller import InputSourceTkinter, AbstractInputSource
from library.events import EventDispatcher
from library.interface import Interface, GraphicsTkinter, AbstractGraphics
from library.model.game_driver import GameDriver
from library.resource_manager import ResourceManager
from library.view.game_view import View


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
    services = TypeMap()
    config = ConfigJson()
    services[AbstractConfig] = config
    if not config.read('config.json'):
        logging.info('App terminated')
        return
    args = parse_args()
    config['debug']['is_debug'] |= args.debug
    config_logging(config)
    logging.info('App running')
    if config['debug']['is_debug']:
        logging.info('Debug mode enabled')
    services[EventDispatcher] = EventDispatcher()
    resources = ResourceManager(services)
    services[ResourceManager] = resources
    services[AbstractGraphics] = GraphicsTkinter(services)
    interface = Interface(services)
    services[Interface] = interface
    if not resources.load():
        logging.info('App terminated')
        return
    GameDriver(services)
    View(services, interface.get_canvas())
    if config['debug']['is_debug']:
        DebugView(services, interface.get_canvas())
    if config['view']['sound_enabled']:
        sound_engine = SoundEngine(services)
        sound_engine.initiate()
        sound_engine.run()
    services[AbstractInputSource] = InputSourceTkinter(services)
    interface.run()


if __name__ == '__main__':
    main()
