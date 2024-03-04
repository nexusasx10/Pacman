import time
from collections import defaultdict, deque

from engine.events import MultiDelegate
from library.events import EventDispatcher, EventId

sec_to_ms = 1000
ms_to_sec = 0.001


class Stopwatch:

    def __init__(self):
        self._result = None
        self._start_time = None

    def result_ms(self):
        return self._result

    def __enter__(self):
        self._result = None
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.result_ms = (time.time() - self._start_time) * sec_to_ms


class Timer:

    def __init__(self, min_delta_time_ms, stopwatch):
        self._stopwatch = stopwatch
        self._min_delta_time_ms = min_delta_time_ms
        self.tick_event = MultiDelegate()
        self._tick_count = 0
        self._delta_time = None
        self._time_from_start = 0
        self._running = False

    def running(self):
        return self._running

    def tick_count(self):
        return self._tick_count

    def time_from_start(self):
        return self._time_from_start

    def delta_time(self):
        return self._delta_time

    def _mainloop(self):
        while self._running:
            if self._delta_time is None:
                self._delta_time = self._min_delta_time_ms

            with self._stopwatch:
                self.tick_event()
                self._tick_count += 1

            delta_time = self._stopwatch.result_ms
            time_left = self._min_delta_time_ms - delta_time
            if time_left > 0:
                time.sleep(time_left)  # todo is it correct?
                delta_time = self._min_delta_time_ms

            self._delta_time = delta_time
            self._time_from_start += delta_time

    def start(self):
        self._running = True
        self._mainloop()

    def stop(self):
        self._running = False


class Task:

    def is_alive(self):
        pass

    def cancel(self):
        pass


# todo Чтобы разделить преиоритеты, создать несколько шедулеров
class Scheduler:

    def __init__(self):
        pass

    def schedule(self, delay_sec, period_sec, action):
        pass

    def schedule_coroutine(self, routine):
        pass

    def schedule(self, delay, event_id):
        self._planned_events[self.current_time + delay].append(event_id)

    def _on_tick(self, event_args):
        self.current_time = event_args.time
        while self._planned_events[self.current_time]:
            event_id = self._planned_events[self.current_time].popleft()
            self._services[EventDispatcher].fire(event_id, self)

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
