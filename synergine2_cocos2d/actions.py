# coding: utf-8
from cocos.actions import MoveTo as BaseMoveTo


class MoveTo(BaseMoveTo):
    def update(self, t):
        super().update(t)
        self.target.need_update_cshape = True
