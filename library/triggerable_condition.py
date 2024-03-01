from library.delegate import Delegate
from library.utils import try_call


class TriggerableCondition:

    def __init__(self):
        self.on_update = Delegate()
        self._is_passed = self._is_passed_now()
        self.on_update(self._is_passed)

    def __call__(self, *args, **kwargs):
        return self._is_passed

    def subscribe(self):
        self._update()

    def unsubscribe(self):
        pass

    def _is_passed_now(self):
        return None

    def _set_is_passed(self, value):
        self._is_passed = value
        self.on_update(self._is_passed)

    def _set_is_passed_false(self):
        self._set_is_passed(False)

    def _set_is_passed_true(self):
        self._set_is_passed(True)

    def _update(self):
        is_passed = self._is_passed_now()
        self._set_is_passed(is_passed)


def is_triggerable(condition):
    return isinstance(condition, TriggerableCondition)


class UpdateHandler:

    def __init__(self, callback_true, callback_false):
        self.callback_true = callback_true
        self.callback_false = callback_false

    def __call__(self, *args, **kwargs):
        is_passed = args[0]
        if is_passed:
            try_call(self.callback_true)
        else:
            try_call(self.callback_false)

    def __eq__(self, other):
        return self.callback_true == other.callback_true and self.callback_false == other.callback_false

    def __hash__(self):
        return hash(self.callback_true) ^ hash(self.callback_false)


def try_subscribe(condition, callback_true=None, callback_false=None):
    if not is_triggerable(condition):
        return

    condition.on_update += UpdateHandler(callback_true, callback_false)


def try_unsubscribe(condition, callback_true=None, callback_false=None):
    if not is_triggerable(condition):
        return

    condition.on_update -= UpdateHandler(callback_true, callback_false)
