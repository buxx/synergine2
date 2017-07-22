# coding: utf-8
import typing

import pyglet

rectangle_positions_type = typing.Union[
    typing.Tuple[
        typing.Tuple[int, int], typing.Tuple[int, int], typing.Tuple[int, int], typing.Tuple[int, int]
    ],
    typing.List[typing.Tuple[int, int]],
]
rgb_type = typing.Tuple[int, int, int]
rgb_alpha_type = typing.Tuple[int, int, int, float]


def draw_rectangle(
    positions: rectangle_positions_type,
    around_color: rgb_type,
    fill_color: typing.Optional[rgb_alpha_type]=None,
):
    """
    A<---D
    |    |
    B--->C
    """
    pyglet.gl.glColor3ub(*around_color)
    pyglet.gl.glBegin(pyglet.gl.GL_LINE_STRIP)
    for v in positions:
        pyglet.gl.glVertex2f(*v)
    pyglet.gl.glVertex2f(*positions[0])
    pyglet.gl.glEnd()

    if fill_color:
        pyglet.gl.glColor4f(*fill_color)
        pyglet.gl.glBegin(pyglet.gl.GL_QUADS)
        pyglet.gl.glVertex3f(positions[0][0], positions[0][1], 0)
        pyglet.gl.glVertex3f(positions[1][0], positions[1][1], 0)
        pyglet.gl.glVertex3f(positions[2][0], positions[2][1], 0)
        pyglet.gl.glVertex3f(positions[3][0], positions[3][1], 0)
        pyglet.gl.glEnd()
