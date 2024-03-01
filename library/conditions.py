from library.triggerable_condition import TriggerableCondition, try_subscribe, try_unsubscribe


class ConditionAlwaysTrue(TriggerableCondition):

    def _is_passed_now(self):
        return True


class ConditionEvent(TriggerableCondition):

    def __init__(self, event_dispatcher, event_id):
        super().__init__()
        self._event_dispatcher = event_dispatcher
        self.event_id = event_id

    def subscribe(self):
        super().subscribe()
        self._event_dispatcher.subscribe(self.event_id, self._update)

    def unsubscribe(self):
        self._event_dispatcher.unsubscribe(self.event_id, self._update)

    def _is_passed_now(self):
        return False

    def _handle_event(self):
        self._set_is_passed(True)
        self._set_is_passed(False)


class ConditionAll(TriggerableCondition):

    def __init__(self, *conditions):
        super().__init__()
        self.conditions = conditions

    def subscribe(self):
        super().subscribe()
        for condition in self.conditions:
            if condition is None:
                condition = ConditionAlwaysTrue()
            try_subscribe(condition, self._update, self._set_is_passed_false)

    def unsubscribe(self):
        for condition in self.conditions:
            if condition is None:
                condition = ConditionAlwaysTrue()
            try_unsubscribe(condition, self._update, self._set_is_passed_false)

    def _is_passed_now(self):
        for condition in self.conditions:
            if not condition():
                return False
        return True
