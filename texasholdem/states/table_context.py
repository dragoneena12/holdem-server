from texasholdem import Table
from texasholdem.states import Context, ConcreteState


class TableContext(Context):
    def __init__(self, state_obj: ConcreteState, table: Table):
        super().__init__(state_obj)
        self.table = table

    def set_state(self, state_obj: ConcreteState):
        self.state = state_obj

    def get_state(self):
        return self.state.get_concrete_state()

    def set_table(self, table: Table):
        self.table = table

    def get_table(self):
        return self.table

    def handle(self, msg):
        self.state.handle(self, msg)
