from collections import defaultdict

from library.conditions import ConditionAll, ConditionEvent
from library.delegate import Delegate
from library.triggerable_condition import try_subscribe, try_unsubscribe


class Fsm:

    def __init__(self, initial_state):
        self.initial_state = initial_state
        self.current_state = self.initial_state
        self.states = []
        self.transitions = defaultdict(list)
        self.on_transition = Delegate()

    def add_state(self, state):
        self.states.append(state)

    def add_transition(self, from_state, to_state, condition=None):
        def handler():
            if from_state == self.current_state:
                self._go_to_state(to_state)

        try_subscribe(condition, handler)
        self.transitions[from_state].append((condition, to_state, handler))

    def update(self):
        for condition, to_state, _ in self.transitions[self.current_state]:
            if not condition or condition():
                self._go_to_state(to_state)
                break

    def reset(self):
        self.current_state = self.initial_state

    def terminate(self):
        for from_state, (condition, to_state, handler) in self.transitions:
            try_unsubscribe(condition, handler)
        self.transitions.clear()

    def _go_to_state(self, state):
        prev_state = self.current_state
        self.current_state = state
        self.on_transition(prev_state, self.current_state)


class EventDrivenFSM:

    def __init__(self, event_dispatcher, initial_state, actor_name):
        self._fsm = Fsm(initial_state)
        self._event_dispatcher = event_dispatcher
        self.on_transition = Delegate()
        self._fsm.on_transition += self.on_transition

    def add_transition(self, event_id, from_states, to_state, condition=None):
        condition = ConditionAll(condition, ConditionEvent(self._event_dispatcher, event_id))
        for from_state in from_states:
            self._fsm.add_transition(from_state, to_state, condition)

    def reset(self):
        self._fsm.reset()

    def terminate(self):
        self._fsm.on_transition -= self.on_transition
        self._fsm.terminate()
