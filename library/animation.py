from library.geometry import Vector
from library.fsm import Fsm


class AnimationKeyFrame:

    def __init__(self, time, value):
        self.time = time
        self.value = value


class AnimationTrack:

    def __init__(self, attribute_path, params):
        self.attribute_path = attribute_path
        self.key_frames = [
            AnimationKeyFrame(0, Vector(0, 0)),
            AnimationKeyFrame(1, Vector(1, 1)),
            AnimationKeyFrame(2, Vector(0, 1))
        ]
        self.params = params

    def update(self, time, obj):
        obj[self.attribute_path] = self.evaluate(time)

# TODO: Оптимизировать взятие значения по времени
    def evaluate(self, time):
        curr_frame = None

        for i in range(len(self.key_frames) - 1):
            curr_frame = self.key_frames[i]
            next_frame = self.key_frames[i + 1]
            if time < next_frame.time:
                break

        if not curr_frame:
            return None

        return curr_frame.value


class AnimationState:

    def __init__(self, name, params):
        self.name = name
        self.tracks = []
        self.params = params

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def update(self, time, obj):
        for track in self.tracks:
            track.update(time, obj)


class Animation:

    def __init__(self):
        self.fsm = Fsm(AnimationState('initial_state', {}))
        self.time = 0

    def update(self, obj):
        self.fsm.current_state.update(self.time, obj)

# TODO: Params: looped, interpolated
