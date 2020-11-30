import time
from collections import defaultdict, deque
from threading import Thread

from library.event import EventArgs, EventId


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
        self._services = services
        self._stopwatch = Stopwatch()
        self.interval_ms = interval_ms
        self.tick_count = 0
        self.running = False
        self._working_thread = Thread(target=self._working_cycle, daemon=True)

    def _working_cycle(self):
        while self.running:
            with self._stopwatch:
                self._services.event_dispatcher.fire(
                    EventId.TICK, EventArgs(self, time=self.tick_count)
                )
            self.tick_count += 1
            interval = self.interval_ms - int(self._stopwatch.result_ms)
            if not self.running:
                break
            if interval > 0:
                time.sleep(interval / 1000)

    def start(self):
        self.running = True
        self._working_thread.start()

    def stop(self):
        self.running = False


class Scheduler:

    def __init__(self, services):
        self._services = services
        self.current_time = 0
        self._planned_events = defaultdict(deque)
        self._services.event_dispatcher.register_handler(
            EventId.TICK, self._on_tick, 0
        )

    def schedule(self, delay, event_id):
        self._planned_events[self.current_time + delay].append(event_id)

    def _on_tick(self, event_args):
        self.current_time = event_args.time
        while self._planned_events[self.current_time]:
            event_id = self._planned_events[self.current_time].popleft()
            self._services.event_dispatcher.fire(event_id, EventArgs(self))

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
