import configparser
import logging
from itertools import chain
from os import listdir, getcwd, path as paths
from collections import defaultdict

from library.config import Config

try:
    from simpleaudio import WaveObject
except ModuleNotFoundError:
    WaveObject = None
from PIL import Image, ImageTk

from library.exceptions import ResourceLoadingError
from library.geometry import Vector, Direction
from library.graphics import Animation, Sprite
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
        self._config = services[Config]
        self._max_save_count = self._config['common']['max_saves']
        self._max_rating_count = self._config['common']['max_ratings']
        self._grids = {}
        self._sprite = defaultdict(list)
        self._animations = {}
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

    def _get_fallback_sprite(self):
        if not self._fallback_sprite:
            texture_width = self._config['view']['px_per_unit']
            texture_height = self._config['view']['px_per_unit']
            image = Image.new('RGB', (texture_width, texture_height), '#FF0000')
            for i in range(texture_width):
                for j in range(texture_height):
                    if ((i // 8) % 2 == 1) == ((j // 8) % 2 == 1):
                        color = (0, 0, 0)
                    else:
                        color = (255, 0, 255)
                    image.putpixel((i, j), color)

            texture = ImageTk.PhotoImage(image)
            self._fallback_sprite = Sprite(texture)
        return self._fallback_sprite

    _fallback_sprite = None

    def _load_textures(self):
        texture_width = self._config['view']['px_per_unit'] * 2
        texture_height = self._config['view']['px_per_unit'] * 2
        for file_name in listdir(self._texture_path):
            if not file_name.endswith('.png'):
                continue
            try:
                atlas = Image.open(paths.join(self._texture_path, file_name))
            except OSError as exc:
                raise ResourceLoadingError(True, *exc.args)
            for j in range(atlas.height // texture_height):
                for i in range(atlas.width // texture_width):
                    texture = atlas.crop(
                        (
                            i * texture_width,
                            j * texture_height,
                            (i + 1) * texture_width,
                            (j + 1) * texture_height
                        )
                    )
                    name = paths.splitext(paths.basename(file_name))[0]
                    image = ImageTk.PhotoImage(texture)
                    self._sprite[name].append(image)

    def get_sprite(self, name):
        if name in self._sprite:
            return self._sprite[name]
        else:
            return self._get_fallback_sprite()

    def _load_animations(self):
        parser = configparser.ConfigParser(delimiters=('=',))
        read_ok = parser.read(self._animation_path, encoding='utf-8')
        if not read_ok:
            raise ResourceLoadingError(True, 'Can\'t read animation file')
        for section in parser:
            if section == 'DEFAULT':
                continue
            for key in parser[section]:
                value = parser[section][key]
                params = {}
                i = 0
                if value[i] == '[':
                    cur_param_name = ''
                    cur_param_value = ''
                    is_name = True
                    while i < len(value):
                        i += 1
                        match value[i]:
                            case ']':
                                i += 1
                                break
                            case ' ':
                                continue
                            case '=':
                                is_name = False
                            case ',':
                                params[cur_param_name] = cur_param_value
                                cur_param_name = ''
                                cur_param_value = ''
                                is_name = True
                            case _:
                                if is_name:
                                    cur_param_name += value[i]
                                else:
                                    cur_param_value += value[i]
                value = value[i:]
                value.replace(' ', '')
                sequence_raw = value.split(',')
                sequence = []
                for item in sequence_raw:
                    if 'x' in item:
                        item = item.split('x')
                        sequence.extend([int(item[0])] * int(item[1]))
                    else:
                        sequence.append(int(item))
                name = f'{section}/{key}'
                self._animations[name] = Animation(sequence, params)

    _fallback_animation = None

    def _get_fallback_animation(self):
        if not self._fallback_animation:
            self._fallback_animation = Animation((0,), {})
        return self._fallback_animation

    def get_animation(self, name):
        if name in self._animations:
            return self._animations[name]
        return self._get_fallback_animation()

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
            self._grids[file_name] = self._validate_grid_data(data, file_name)
        if not self._grids:
            raise ResourceLoadingError(True, 'Can\'t load grids')

    def _validate_grid_data(self, data, file_name):
        if len(data) == 0:
            raise ResourceLoadingError(False, f'Grid file {file_name} is empty')
        width = -1
        for i, line in enumerate(data):
            if width == -1:
                width = len(line)
                if width == 0:
                    raise ResourceLoadingError(
                        False,
                        f'Bad grid file {file_name}: line {i} is empty'
                    )
            elif len(line) != width:
                raise ResourceLoadingError(
                    False,
                    f'Bad grid file {file_name}: line {i} has different size'
                )
            for j, char in enumerate(line):
                if char not in self._block_types:
                    raise ResourceLoadingError(
                        False,
                        f'Bad grid file {file_name}: unexpected symbol "{char}" at line {i} column {j}: '
                    )
        return data

    def list_grids(self):
        return self._grids.keys()

    def get_grid(self, grid_name):
        data = self._grids[grid_name]
        size = Vector(len(data[0]), len(data))
        grid = Grid({}, size)
        for i, line in enumerate(data):
            for j, char in enumerate(line):
                block_info = self._block_types[char]
                connections = {}
                for direction in Direction:
                    o_x, o_y = direction.get_offset()
                    i_o = (i + o_y) % size.y
                    j_o = (j + o_x) % size.x
                    try:
                        connection = self._block_types[data[i_o][j_o]][2]
                    except:
                        pass
                    connections[direction] = connection
                cell = Vector(j, i)
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
    def get_icon_path():
        return paths.join(getcwd(), 'resources', 'pacman.ico')
