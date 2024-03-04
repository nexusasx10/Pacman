

class ComponentContainer:

    def __init__(self):
        self._components = {}

    def add_component(self, component_type: type):
        # todo а если несколько компонентов с наследующимися типами?
        component = component_type(self)
        self._components[component_type] = component
        return component

    def get_component(self, component_type: type):
        # todo type check
        component = self._components.get(component_type)
        if component is not None:
            return component

        # todo better performance, measure
        for cur_component_type, cur_component in self._components.items():
            if issubclass(cur_component_type, component_type):
                return cur_component

    def remove_component(self, type_):
        raise NotImplementedError()


class Component:

    def __init__(self, owner: ComponentContainer):
        # todo weak ref or custom destroy method
        self._owner = owner

    def __repr__(self):
        return f'{type(self).__name__} component of {self._owner}'

    def owner(self):
        return self._owner
