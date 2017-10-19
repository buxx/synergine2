# coding: utf-8
from enum import Enum


class UserAction(Enum):
    ORDER_MOVE = 'ORDER_MOVE'
    ORDER_MOVE_FAST = 'ORDER_MOVE_FAST'
    ORDER_MOVE_CRAWL = 'ORDER_MOVE_CRAWL'
