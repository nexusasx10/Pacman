from library.event import EventId


class StateDriver:

    def __init__(self, event_dispatcher, current_state, actor_name):
        self._event_dispatcher = event_dispatcher
        self._actor_name = actor_name
        self.current_state = current_state
        self._reset = False

    def add_transition(self, event_id, from_states, to_state, condition=None):
        if not condition:
            def condition(args):
                return True

        def transition(event_args):
            if self._reset:
                return
            if self.current_state in from_states and condition(event_args):
                old_state = self.current_state
                self.current_state = to_state
                self._event_dispatcher.fire(
                    EventId.MODE_CHANGE,
                    self,
                    name=self._actor_name,
                    from_mode=old_state,
                    to_mode=to_state
                )
        self._event_dispatcher.subscribe(event_id, transition)

    def reset(self):
        self._reset = True
