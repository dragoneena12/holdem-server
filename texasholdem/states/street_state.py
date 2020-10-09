from abc import abstractmethod
import logging
from texasholdem.states import TableContext, ConcreteState

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StreetState(ConcreteState):
    @abstractmethod
    def handle(self, table_context: TableContext):
        pass


class PreflopStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("Pre-Flop State"))
        table_context.set_state(FlopStreetState())


class FlopStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("Flop State"))
        table_context.set_state(TurnStreetState())


class TurnStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("Turn State"))
        table_context.set_state(RiverStreetState())


class RiverStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("River State"))
