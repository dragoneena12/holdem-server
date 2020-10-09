from texasholdem.states import ConcreteState


class Context(object):
    def __init__(self, state_obj: ConcreteState):
        self.state = state_obj

    def set_state(self, state_obj: ConcreteState):
        self.state = state_obj

    def handle(self):
        self.state.handle(self)

    def get_state(self):
        return self.state.get_concrete_state()
