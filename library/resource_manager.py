import configparser
import logging
from itertools import chain
from os import listdir, getcwd, path as paths
from collections import defaultdict

try:
    from simpleaudio import WaveObject
except ModuleNotFoundError:
    WaveObject = None
from PIL import Image, ImageTk

from library.exceptions import ResourceLoadingError
from library.geometry import Point, Direction
from library.graphics import Animation
from library.model.field import Block, Grid


# todo проверка на существование нектритических ресурсов
class ResourceManager:

    _resource_path = paths.join(getcwd(), 'resources')
    _grid_path = paths.join(_resource_path, 'grids')
    _texture_path = paths.join(_resource_path, 'textures')
    _animation_path = paths.join(_resource_path, 'animations')
    _sound_path = paths.join(_resource_path, 'sounds')
    _data_path = paths.join(getcwd(), 'data')
    _ratings_path = paths.join(_data_path, 'ratings')
    _saves_path = paths.join(_data_path, 'saves')

    _block_types = {
        # content, anchor, can enter
        '_': (Block.Content.EMPTY, None, True),
        'E': (Block.Content.WALL, 'enemies', False),
        'P': (Block.Content.EMPTY, 'pacman', True),
        '#': (Block.Content.WALL, None, False),
        '=': (Block.Content.DOOR, None, False),
        '.': (Block.Content.DOT, None, True),
        '0': (Block.Content.ENERGIZER, None, True),
        'F': (Block.Content.EMPTY, 'fruit', True)
    }

    def __init__(self, services):
        self._services = services
        self._max_save_count = self._services.config['common']['max_saves']
        self._max_rating_count = self._services.config['common']['max_ratings']
        self._grids = {}
        self._textures = defaultdict(list)
        self._animations = defaultdict(dict)
        self._sounds = {}
        self._ratings = []
        self._saves = {
            key: defaultdict(dict)
            for key in chain(range(self._max_save_count), ('quick',))
        }

    def load(self):
        loads = (
            self._load_grids,
            self._load_textures,
            self._load_animations,
            self._load_sounds,
            self._load_ratings,
            self._load_saves,
        )
        for load in loads:
            try:
                load()
            except ResourceLoadingError as exc:  # todo
                logging.error(exc)
                if exc.critical:
                    return False
        return True

    def _load_textures(self):
        texture_width = self._services.config['view']['texture_width']
        texture_height = self._services.config['view']['texture_height']
        for file_name in listdir(self._texture_path):
            if not file_name.endswith('.png'):
                continue
            try:
                image = Image.open(paths.join(self._texture_path, file_name))
            except OSError as exc:
                raise ResourceLoadingError(True, *exc.args)
            for j in range(image.height // texture_height):
                for i in range(image.width // texture_width):
                    texture = image.crop(
                        (
                            i * texture_width,
                            j * texture_height,
                            (i + 1) * texture_width,
                            (j + 1) * texture_height
                        )
                    )
                    name = paths.splitext(paths.basename(file_name))[0]
                    self._textures[name].append(ImageTk.PhotoImage(texture))

    def get_texture(self, name, index):
        return self._textures[name][index]

    def _load_animations(self):
        parser = configparser.ConfigParser(delimiters=('=',))
        read_ok = parser.read(self._animation_path, encoding='utf-8')
        if not read_ok:
            raise ResourceLoadingError(True, 'Can\'t read animation file')
        for section in parser:
            if section == 'DEFAULT':
                continue
            file = None
            for key in parser[section]:
                if key == 'file':
                    file = parser[section][key]
                    continue
                value = parser[section][key]
                repeat = value.startswith('R')
                if repeat:
                    value = value[1:]
                sequence = value.split(',')
                animation = []
                for item in sequence:
                    if 'x' in item:
                        item = item.split('x')
                        animation.extend([int(item[0])] * int(item[1]))
                    else:
                        animation.append(int(item))
                self._animations[section][key] = file, animation, repeat

    def get_animation(self, section, key):
        if section in self._animations and key in self._animations[section]:
            return Animation(self._services, *self._animations[section][key])

    def _load_sounds(self):
        if not WaveObject:
            raise ResourceLoadingError(False)

        for file_name in listdir(self._sound_path):
            if not file_name.endswith('.wav'):
                continue
            file_name = paths.join(self._sound_path, file_name)
            name = paths.splitext(paths.basename(file_name))[0]
            try:
                self._sounds[name] = WaveObject.from_wave_file(file_name)
            except OSError as exc:
                raise ResourceLoadingError(False, *exc.args)

    def get_sound(self, sound_id):
        return self._sounds.get(sound_id, None)

    def _load_grids(self):
        for file_name in listdir(self._grid_path):
            path = paths.join(self._grid_path, file_name)
            try:
                with open(path, encoding='utf-8') as fd:
                    content = fd.read()
            except OSError as exc:
                raise ResourceLoadingError(False, *exc.args)
            data = content.split('\n')
            self._grids[file_name] = self._validate_grid_data(data)
        if not self._grids:
            raise ResourceLoadingError(True, 'Can\'t load grids')

    def _validate_grid_data(self, data):
        if len(data) != Grid.size.height:
            raise ResourceLoadingError(False, 'Grid file is corrupted')
        for line in data:
            if len(line) != Grid.size.width:
                raise ResourceLoadingError(False, 'Grid file is corrupted')
            for char in line:
                if char not in self._block_types:
                    raise ResourceLoadingError(
                        False, 'Unexpected symbol in grid file: ' + char
                    )
        return data

    def list_grids(self):
        return self._grids.keys()

    def get_grid(self, grid_name):
        data = self._grids[grid_name]
        grid = Grid({})
        for i, line in enumerate(data):
            for j, char in enumerate(line):
                block_info = self._block_types[char]
                connections = {}
                for direction in Direction:
                    o_x, o_y = direction.get_offset()
                    i_o = (i + o_y) % Grid.size.height
                    j_o = (j + o_x) % Grid.size.width
                    connection = self._block_types[data[i_o][j_o]][2]
                    connections[direction] = connection
                cell = Point(j, i)
                grid[cell] = Block(cell, block_info[0], connections)
                if block_info[1]:
                    grid.anchors[block_info[1]] = cell
        return grid

    # todo max_ratings_count check and max_name_length
    def _load_ratings(self):
        parser = configparser.ConfigParser()
        read_ok = parser.read(self._ratings_path, encoding='utf-8')
        if not read_ok:
            raise ResourceLoadingError(False, 'Can\'t read ratings file')
        for key in parser['DEFAULT']:
            try:
                self._ratings.append((key, parser.getint('DEFAULT', key)))
            except ValueError:
                raise ResourceLoadingError(False, 'Can\'t read ratings file')
        self._ratings.sort(key=lambda x: -x[1])
        self._ratings = self._ratings[:self._max_rating_count]
        # todo exc
        # todo если ресурс критический - корректно завершаем прогу,
        # todo инача пользуемся значениями по-умолчанию, прописанными в init

    def list_ratings(self):
        return self._ratings

    def add_rating(self, name, rating):
        parser = configparser.ConfigParser()
        self._ratings.append((name, rating))
        self._ratings.sort(key=lambda x: -x[1])
        self._ratings = self._ratings[:10]
        for rating in self._ratings:
            parser.set('DEFAULT', str(rating[0]), str(rating[1]))
        try:
            with open(self._ratings_path, 'w', encoding='utf-8') as fd:
                parser.write(fd)
        except OSError as exc:
            logging.error(exc)

    def _load_saves(self):  # todo validate save and maybe others
        for save_index in chain(range(self._max_save_count), ('quick',)):
            path = paths.join(self._saves_path, 'save_' + str(save_index))
            if not paths.exists(path):
                continue
            parser = configparser.ConfigParser()
            read_ok = parser.read(path, encoding='utf-8')
            if not read_ok:
                raise ResourceLoadingError(False, 'Can\'t read save file')
            for section in parser:
                if section == 'DEFAULT':
                    continue
                for key in parser[section]:
                    for method in (parser.getint, parser.getfloat,
                                   parser.getboolean):
                        try:
                            value = method(section, key)
                            break
                        except ValueError:
                            continue
                    else:
                        value = parser.get(section, key)
                    self._saves[save_index][section][key] = value

    def list_saves(self):
        return [
            (index, self._saves[index])
            for index in chain(range(self._max_save_count), ('quick',))
        ]

    def get_save(self, index):
        return self._saves[index]

    def add_save(self, index, save):
        parser = configparser.ConfigParser()
        parser.read_dict(save)
        path = paths.join(self._saves_path, 'save_' + str(index))
        try:
            with open(path, 'w', encoding='utf-8') as fd:
                parser.write(fd)
        except OSError as exc:
            logging.error(exc)
        self._load_saves()

    @staticmethod
    def get_icon():
        return paths.join(getcwd(), 'resources', 'pacman.ico')
