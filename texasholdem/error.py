import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class NotEnoughPlayerError(object):
    pass


class PlayerLimitExceededError(object):
    pass


class OutOfBuyInRangeError(object):
    pass


class NotEnoughPlayerBankrollError(object):
    pass


class OccupiedSeatError(object):
    pass
