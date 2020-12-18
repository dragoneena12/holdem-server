from abc import ABCMeta, abstractmethod


class State(metaclass=ABCMeta):
    @abstractmethod
    async def handle(self, context, msg: dict):
        pass

    @abstractmethod
    async def notify_current_status(self, context):
        pass

    @abstractmethod
    async def next_round(self, context):
        pass
