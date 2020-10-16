from texasholdem import Table
from texasholdem.states import Context, ConcreteState


class TableContext(Context):
    def __init__(self, state_obj: ConcreteState, table: Table):
        super().__init__(state_obj)
        self.table = table

    async def set_state(self, state_obj: ConcreteState):
        self.state = state_obj
        await self.state.notify_current_status(self)

    def get_state(self):
        return self.state.get_concrete_state()

    async def set_table(self, table: Table):
        self.table = table
        await self.state.notify_current_status(self)

    def get_table(self):
        return self.table

    async def handle(self, msg):
        await self.state.handle(self, msg)

    async def notify_current_status(self):
        await self.state.notify_current_status(self)
