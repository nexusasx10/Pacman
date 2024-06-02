from engine.actor import Actor


def component_alias(name):
    def wrapper(type_):
        Actor._aliases[name] = type_
        return type_
    return wrapper
