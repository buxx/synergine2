# coding: utf-8

"""
WARNING: Do not import cocos/pyglet stuff here: cocos/pyglet modules must be loaded inside gui process.
"""
import typing

from synergine2.simulation import Event


class GuiRequestMoveEvent(Event):
    def __init__(
        self,
        subject_id: int,
        move_to_position: typing.Tuple[int, int],
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.move_to_position = move_to_position
