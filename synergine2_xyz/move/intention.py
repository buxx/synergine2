# coding: utf-8
import typing

from synergine2.simulation import Intention


class MoveToIntention(Intention):
    def __init__(
        self,
        to: typing.Tuple[int, int],
        gui_action: typing.Any,
    ) -> None:
        self.to = to
        self.gui_action = gui_action
        self.path = None  # type: typing.List[typing.Tuple[int, int]]

    def get_data(self) -> dict:
        return {
            'to': self.to,
            'gui_action': self.gui_action,
            'path': self.path,
        }