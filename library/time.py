import time
from collections import defaultdict, deque

from library.event import EventId


class Stopwatch:
    """Замеряет время выполнения блока кода."""
    def __init__(self):
        self.result_ms = None
        self.start_time = None

    def __enter__(self):
        self.result_ms = None
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.result_ms = (time.time() - self.start_time) * 1000


class Timer:

    def __init__(self, services, interval_ms):
        self._event_dispatcher = services.event_dispatcher
        self._stopwatch = Stopwatch()
        self.interval_ms = interval_ms
        self.tick_count = 0
        self.running = False
        self._next_frame_time = -1

    def _working_cycle(self):
        while self.running:
            if time.time() < self._next_frame_time:
                continue
            self._next_frame_time = time.time() + self.interval_ms / 1000
            with self._stopwatch:
                self._event_dispatcher.fire(EventId.TICK, self, time=self.tick_count)
            self.tick_count += 1
            if self._stopwatch.result_ms > 0:
                print(1000 / self._stopwatch.result_ms)
            else:
                print('Inf')

    def start(self):
        self.running = True
        self._working_cycle()

    def stop(self):
        self.running = False


class Scheduler:

    def __init__(self, event_dispatcher):
        self._event_dispatcher = event_dispatcher
        self.current_time = 0
        self._planned_events = defaultdict(deque)
        self._event_dispatcher.subscribe(EventId.TICK, self._on_tick, 0)

    def schedule(self, delay, event_id):
        self._planned_events[self.current_time + delay].append(event_id)

    def _on_tick(self, event_args):
        self.current_time = event_args.time
        while self._planned_events[self.current_time]:
            event_id = self._planned_events[self.current_time].popleft()
            self._event_dispatcher.fire(event_id, self)

    def reset(self):
        self._planned_events = defaultdict(deque)

    def store(self):
        result = defaultdict(list)
        for time_ in self._planned_events.keys():
            for planned_event in self._planned_events[time_]:
                result[time_ - self.current_time].append(planned_event.name)
        return result

    def load(self, data):
        for time_ in data:
            for planned_event in data[time_][1:-1].split(', '):
                time_ = int(time_) + self.current_time
                self._planned_events[time_].append(
                    EventId[planned_event[1:-1]]
                )
