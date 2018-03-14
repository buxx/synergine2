# coding: utf-8
import typing

from synergine2.simulation import Intention


class MoveToIntention(Intention):
    def __init__(
        self,
        move_to: typing.Tuple[int, int],
        start_time: float,
        gui_action: typing.Any,
        # FIXME: After new move algos, this requires
        from_: typing.Tuple[int, int]=None,
    ) -> None:
        self.move_to = move_to
        self.path = []  # type: typing.List[typing.Tuple[int, int]]
        self.path_progression = -1  # type: int
        self.last_intention_time = start_time
        self.just_reach = False
        self.initial = True
        self.gui_action = gui_action
        self.from_ = from_

    def get_data(self) -> dict:
        return {
            'from': self.from_,
            'to': self.move_to,
            'path': self.path,
        }