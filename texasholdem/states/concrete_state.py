from texasholdem.states import State


class ConcreteState(State):
    def __init__(self, state: State):
        self.state = state

    def get_concrete_state(self):
        return self.state
