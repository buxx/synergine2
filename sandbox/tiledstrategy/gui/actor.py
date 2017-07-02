# coding: utf-8
import typing

import pyglet

from sandbox.tiledstrategy.gui.animation import ANIMATION_WALK
from synergine2_cocos2d.actor import Actor


class Man(Actor):
    animation_image_paths = {
        ANIMATION_WALK: [
            'actors/man.png',
            'actors/man_w1.png',
            'actors/man_w2.png',
            'actors/man_w3.png',
            'actors/man_w4.png',
            'actors/man_w5.png',
            'actors/man_w6.png',
            'actors/man_w7.png',
            'actors/man_w8.png',
            'actors/man_w9.png',
            'actors/man_w10.png',
        ]
    }

    def __init__(self):
        super().__init__(pyglet.resource.image('actors/man.png'))
