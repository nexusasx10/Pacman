from collections import defaultdict
from enum import Enum
from threading import Thread, Lock

import time

from library.event import EventId, EventDispatcher
from library.model.actor import Enemy, Pacman
from library.model.field import Block
from library.model.game_driver import GameDriver
from library.resource_manager import ResourceManager


class SoundEngine:

    class Action(Enum):
        REPLACE = 0
        INTERRUPT = 1
        REMOVE = 2

    def __init__(self, services):
        self._services = services
        self._channels = defaultdict(list)
        self._working_thread = Thread(target=self._working_cycle, daemon=True)
        self.running = False
        self._model = None
        self._lock = Lock()
        self._services[EventDispatcher].subscribe(EventId.MODEL_UPDATE, self._on_model_update)

    def _on_model_update(self, event_args):
        self._model = event_args.model

    def initiate(self):
        self._register_handler(
            EventId.GAME_INIT,
            None,
            self.Action.REPLACE,
            'start',
            'top',
            False
        )
        self._register_handler(
            EventId.GAME_START,
            None,
            self.Action.REPLACE,
            'siren1',
            'background',
            True
        )
        self._register_handler(
            EventId.PICKUP,
            lambda a: a.pickup == Block.Content.ENERGIZER,
            self.Action.REPLACE,
            'powermode',
            'background',
            True
        )
        self._register_handler(
            EventId.ENERGIZER_TIMEOUT,
            None,
            self.Action.REPLACE,
            'siren1',
            'background',
            True
        )
        # self._register_handler(
        #     EventId.GAME_START,
        #     None,
        #     self.Action.REPLACE,
        #     'eatcycle',
        #     'effect',
        #     True
        # )
        # self._register_handler(
        #     EventId.MODE_CHANGE,
        #     lambda a: a.to_mode == Pacman.Mode.WAITING,
        #     self.Action.REMOVE,
        #     None,
        #     'effect',
        #     None
        # )
        # self._register_handler(
        #     EventId.MODE_CHANGE,
        #     lambda a: a.to_mode == Pacman.Mode.WALKING,
        #     self.Action.REPLACE,
        #     'eatcycle',
        #     'effect',
        #     True
        # )
        self._register_handler(
            EventId.MODE_CHANGE,
            lambda a: a.to_mode == Enemy.Mode.DEAD,
            self.Action.INTERRUPT,
            'eatghost',
            'effect',
            False
        )
        self._register_handler(
            EventId.MODE_CHANGE,
            lambda a: (
                a.name == 'pacman' and
                a.to_mode == Pacman.Mode.DEAD
            ),
            self.Action.INTERRUPT,
            'die',
            'effect',
            False
        )

    def _register_handler(self, event_id, condition, action,
                          sound_id, channel_id, repeat):
        def handler(event_args):
            if not condition or condition(event_args):
                self.play(sound_id, channel_id, repeat, action)
        self._services[EventDispatcher].subscribe(event_id, handler)

    def _working_cycle(self):
        while self.running:
            # без задержки _working_thread отбирает рабочее время у остальных
            time.sleep(0.2)  # todo вынести в config
            if not self._model:
                continue
            with self._lock:
                if self._model.mode not in (
                        GameDriver.Mode.PLAY, GameDriver.Mode.FREE
                ):
                    for channel_id in self._channels.keys():
                        if channel_id == 'top':
                            continue
                        channel_stack = self._channels[channel_id]
                        if channel_stack:
                            channel_stack[-1][1].stop()
                    self._update_channel('top')
                    continue
                for channel_id in self._channels.keys():
                    self._update_channel(channel_id)

    def _update_channel(self, channel_id):
        channel_stack = self._channels[channel_id]
        if not channel_stack:
            return
        sound_id, play_obj, repeat = channel_stack[-1]
        if play_obj.is_playing():
            return
        if not repeat:
            channel_stack.pop()
            return
        sound = self._services[ResourceManager].get_sound(sound_id)
        if not sound:
            return
        play_obj = sound.play()
        self._channels[channel_id][-1] = sound_id, play_obj, repeat

    def play(self, sound_id, channel_id, repeat, action):
        if action == self.Action.REMOVE:
            if self._channels[channel_id]:
                self._channels[channel_id][-1][1].stop()
                self._channels[channel_id].clear()
        sound = self._services[ResourceManager].get_sound(sound_id)
        if not sound:
            return
        play_obj = sound.play()
        if channel_id in self._channels and self._channels[channel_id]:
            self._channels[channel_id][-1][1].stop()
        if action == self.Action.INTERRUPT:
            self._channels[channel_id].append((sound_id, play_obj, repeat))
        elif action == self.Action.REPLACE:
            if self._channels[channel_id]:
                self._channels[channel_id][-1] = sound_id, play_obj, repeat
            else:
                self._channels[channel_id].append((sound_id, play_obj, repeat))

    def run(self):
        self.running = True
        self._working_thread.start()

    def stop(self):
        self.running = False
