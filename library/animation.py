from engine.transform import Transform2Component
from library.fsm import Fsm


class AnimationKeyFrame:

    def __init__(self, time, value):
        self.time = time
        self.value = value


class AnimationStateParams:

    def __init__(self, is_looped, duration):
        self.is_looped = is_looped
        self.duration = duration


class AnimationTrackParams:

    def __init__(self, is_interpolated):
        self.is_interpolated = is_interpolated


class AnimationTrack:

    def __init__(self, attribute_path, key_frames, params):
        self.attribute_path = list(map(lambda x: x.split('.'), attribute_path.split('/')))
        self.key_frames = key_frames
        self.params = params

    def update(self, time, obj):
        if len(self.attribute_path) > 1:
            for actor_name in self.attribute_path[:-1]:
                obj = obj[Transform2Component].find_child(actor_name).owner
        field_path = self.attribute_path[-1]
        if len(field_path) > 1:
            for field_name in field_path:
                obj = obj.__getattr__[field_name]
        value = self.evaluate(time)
        if value is not None:
            obj.__setattr__(field_path[-1], value)

# TODO: Оптимизировать взятие значения по времени (хотя на наших данных эта оптимизация ничего не даст)
    def evaluate(self, time):
        curr_frame = None

        for frame in self.key_frames:
            if frame.time < time:
                curr_frame = frame
            else:
                break

        if not curr_frame:
            return None

        return curr_frame.value


class AnimationState:

    def __init__(self, name, tracks, params):
        self.name = name
        self.tracks = tracks
        self.params = params

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def update(self, time, obj):
        if self.params.is_looped:
            time = time % self.params.duration

        for track in self.tracks:
            track.update(time, obj)


class Animation:

    def __init__(self, states, initial_state, transitions):
        self.states = states
        self.initial_state = initial_state
        self.transitions = transitions

    def create_context(self):
        initial_state = None
        for state in self.states:
            if state.name == self.initial_state:
                initial_state = state

        return AnimationContext(0, self.states, initial_state, initial_state)


class AnimationContext:

    def __init__(self, time, states, initial_state, current_state):
        self.time = time
        self._fsm = Fsm(initial_state)
        for state in states:
            self._fsm.add_state(state)
        self._fsm.current_state = current_state

    def update(self, obj):
        self._fsm.current_state.update(self.time, obj)
