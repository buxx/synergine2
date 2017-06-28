# coding: utf-8
import weakref

import cocos
import pyglet
from pyglet.window import key as wkey, mouse

from cocos import collision_model, euclid
from cocos.director import director
from cocos.layer import ScrollableLayer, Layer
from cocos.sprite import Sprite

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.layer import LayerManager
from synergine2_cocos2d.middleware import TMXMiddleware


class GridManager(object):
    def __init__(
        self,
        layer: Layer,
        square_width: int,
        border: int=0,
    ):
        self.layer = layer
        self.square_width = square_width
        self.border = border

    @property
    def final_width(self):
        return self.square_width + self.border

    def scale_sprite(self, sprite: Sprite):
        sprite.scale_x = self.final_width / sprite.image.width
        sprite.scale_y = self.final_width / sprite.image.height

    def position_sprite(self, sprite: Sprite, grid_position):
        grid_x = grid_position[0]
        grid_y = grid_position[1]
        sprite.position = grid_x * self.final_width, grid_y * self.final_width

    def get_window_position(self, grid_position_x, grid_position_y):
        grid_x = grid_position_x
        grid_y = grid_position_y
        return grid_x * self.final_width, grid_y * self.final_width

    def get_grid_position(self, window_x, window_y, z=0) -> tuple:
        window_size = director.get_window_size()

        window_center_x = window_size[0] // 2
        window_center_y = window_size[1] // 2

        window_relative_x = window_x - window_center_x
        window_relative_y = window_y - window_center_y

        real_width = self.final_width * self.layer.scale

        return int(window_relative_x // real_width),\
               int(window_relative_y // real_width),\
               z


class GridLayerMixin(object):
    def __init__(self, *args, **kwargs):
        square_width = kwargs.pop('square_width', 32)
        square_border = kwargs.pop('square_border', 2)
        self.grid_manager = GridManager(
            self,
            square_width=square_width,
            border=square_border,
        )
        super().__init__(*args, **kwargs)


class ProbeQuad(cocos.cocosnode.CocosNode):

    def __init__(self, r, color4):
        super(ProbeQuad, self).__init__()
        self.color4 = color4
        self.vertexes = [(r, 0, 0), (0, r, 0), (-r, 0, 0), (0, -r, 0)]

    def draw(self):
        pyglet.gl.glPushMatrix()
        self.transform()
        pyglet.gl.glBegin(pyglet.gl.GL_QUADS)
        pyglet.gl.glColor4ub(*self.color4)
        for v in self.vertexes:
            pyglet.gl.glVertex3i(*v)
        pyglet.gl.glEnd()
        pyglet.gl.glPopMatrix()


class MinMaxRect(cocos.cocosnode.CocosNode):
    def __init__(self, layer_manager: LayerManager):
        super(MinMaxRect, self).__init__()
        self.layer_manager = layer_manager
        self.color3 = (0, 0, 255)
        self.vertexes = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
        self.visible = False

    def adjust_from_w_minmax(self, wminx, wmaxx, wminy, wmaxy):
        # asumes world to screen preserves order
        sminx, sminy = self.layer_manager.scrolling_manager.world_to_screen(wminx, wminy)
        smaxx, smaxy = self.layer_manager.scrolling_manager.world_to_screen(wmaxx, wmaxy)
        self.vertexes = [(sminx, sminy), (sminx, smaxy), (smaxx, smaxy), (smaxx, sminy)]


class EditLayer(cocos.layer.Layer):
    is_event_handler = True

    def __init__(
        self,
        layer_manager: LayerManager,
        worldview,
        bindings=None,
        fastness=None,
        autoscroll_border=10,
        autoscroll_fastness=None,
        wheel_multiplier=None,
        zoom_min=None,
        zoom_max=None,
        zoom_fastness=None,
        mod_modify_selection=None,
        mod_restricted_mov=None,
    ):
        super(EditLayer, self).__init__()

        self.layer_manager = layer_manager
        self.bindings = bindings
        buttons = {}
        modifiers = {}
        for k in bindings:
            buttons[bindings[k]] = 0
            modifiers[bindings[k]] = 0
        self.buttons = buttons
        self.modifiers = modifiers

        self.fastness = fastness
        self.autoscroll_border = autoscroll_border
        self.autoscroll_fastness = autoscroll_fastness
        self.wheel_multiplier = wheel_multiplier
        self.zoom_min = zoom_min
        self.zoom_max = zoom_max
        self.zoom_fastness = zoom_fastness
        self.mod_modify_selection = mod_modify_selection
        self.mod_restricted_mov = mod_restricted_mov

        self.weak_scroller = weakref.ref(self.layer_manager.scrolling_manager)
        self.weak_worldview = weakref.ref(worldview)
        self.wwidth = worldview.width
        self.wheight = worldview.height

        self.autoscrolling = False
        self.drag_selecting = False
        self.drag_moving = False
        self.restricted_mov = False
        self.wheel = 0
        self.dragging = False
        self.keyscrolling = False
        self.keyscrolling_descriptor = (0, 0)
        self.wdrag_start_point = (0, 0)
        self.elastic_box = None  # type: MinMaxRect
        self.elastic_box_wminmax = 0, 0, 0, 0
        self.mouse_mark = None  # type: ProbeQuad
        self.selection = {}
        self.screen_mouse = (0, 0)
        self.world_mouse = (0, 0)
        self.sleft = None
        self.sright = None
        self.sbottom = None
        self.s_top = None

        # opers that change cshape must ensure it goes to False,
        # selection opers must ensure it goes to True
        self.selection_in_collman = True
        # TODO: Hardcoded here, should be obtained from level properties or calc
        # from available actors or current actors in worldview
        gsize = 32 * 1.25
        self.collman = collision_model.CollisionManagerGrid(
            -gsize,
            self.wwidth + gsize,
            -gsize,
            self.wheight + gsize,
            gsize,
            gsize,
        )
        for actor in worldview.actors:
            self.collman.add(actor)

        self.schedule(self.update)

    def on_enter(self):
        super(EditLayer, self).on_enter()
        scene = self.get_ancestor(cocos.scene.Scene)
        if self.elastic_box is None:
            self.elastic_box = MinMaxRect(self.layer_manager)
            scene.add(self.elastic_box, z=10)
        if self.mouse_mark is None:
            self.mouse_mark = ProbeQuad(4, (0, 0, 0, 255))
            scene.add(self.mouse_mark, z=11)

    def update(self, dt):
        mx = self.buttons['right'] - self.buttons['left']
        my = self.buttons['up'] - self.buttons['down']
        dz = self.buttons['zoomin'] - self.buttons['zoomout']

        # scroll
        if self.autoscrolling:
            self.update_autoscroll(dt)
        else:
            # care for keyscrolling
            new_keyscrolling = ((len(self.selection) == 0) and
                                (mx != 0 or my != 0))
            new_keyscrolling_descriptor = (mx, my)
            if ((new_keyscrolling != self.keyscrolling) or
                (new_keyscrolling_descriptor != self.keyscrolling_descriptor)):
                self.keyscrolling = new_keyscrolling
                self.keyscrolling_descriptor = new_keyscrolling_descriptor
                fastness = 1.0
                if mx != 0 and my != 0:
                    fastness *= 0.707106  # 1/sqrt(2)
                self.autoscrolling_sdelta = (0.5 * fastness * mx, 0.5 * fastness * my)
            if self.keyscrolling:
                self.update_autoscroll(dt)

        # selection move
        if self.drag_moving:
            # update positions
            wx, wy = self.world_mouse
            dx = wx - self.wdrag_start_point[0]
            dy = wy - self.wdrag_start_point[1]
            if self.restricted_mov:
                if abs(dy) > abs(dx):
                    dx = 0
                else:
                    dy = 0
            dpos = euclid.Vector2(dx, dy)
            for actor in self.selection:
                old_pos = self.selection[actor].center
                new_pos = old_pos + dpos
                # TODO: clamp new_pos so actor into world boundaries ?
                actor.update_position(new_pos)

        scroller = self.weak_scroller()

        # zoom
        zoom_change = (dz != 0 or self.wheel != 0)
        if zoom_change:
            if self.mouse_into_world():
                wzoom_center = self.world_mouse
                szoom_center = self.screen_mouse
            else:
                # decay to scroller unadorned
                wzoom_center = None
            if self.wheel != 0:
                dt_dz = 0.01666666 * self.wheel
                self.wheel = 0
            else:
                dt_dz = dt * dz
            zoom = scroller.scale + dt_dz * self.zoom_fastness
            if zoom < self.zoom_min:
                zoom = self.zoom_min
            elif zoom > self.zoom_max:
                zoom = self.zoom_max
            scroller.scale = zoom
            if wzoom_center is not None:
                # postprocess toward 'world point under mouse the same before
                # and after zoom' ; other restrictions may prevent fully comply
                wx1, wy1 = self.layer_manager.scrolling_manager.screen_to_world(*szoom_center)
                fx = scroller.restricted_fx + (wzoom_center[0] - wx1)
                fy = scroller.restricted_fy + (wzoom_center[1] - wy1)
                scroller.set_focus(fx, fy)

    def update_mouse_position(self, sx, sy):
        self.screen_mouse = sx, sy
        self.world_mouse = self.layer_manager.scrolling_manager.screen_to_world(sx, sy)
        # handle autoscroll
        border = self.autoscroll_border
        if border is not None:
            # sleft and companions includes the border
            scroller = self.weak_scroller()
            self.update_view_bounds()
            sdx = 0.0
            if sx < self.sleft:
                sdx = sx - self.sleft
            elif sx > self.sright:
                sdx = sx - self.sright
            sdy = 0.0
            if sy < self.sbottom:
                sdy = sy - self.sbottom
            elif sy > self.s_top:
                sdy = sy - self.s_top
            self.autoscrolling = sdx != 0.0 or sdy != 0.0
            if self.autoscrolling:
                self.autoscrolling_sdelta = (sdx / border, sdy / border)
        self.mouse_mark.position = self.layer_manager.scrolling_manager.world_to_screen(*self.world_mouse)

    def update_autoscroll(self, dt):
        fraction_sdx, fraction_sdy = self.autoscrolling_sdelta
        scroller = self.weak_scroller()
        worldview = self.weak_worldview()
        f = self.autoscroll_fastness
        wdx = (fraction_sdx * f * dt) / scroller.scale / worldview.scale
        wdy = (fraction_sdy * f * dt) / scroller.scale / worldview.scale
        # ask scroller to try scroll (wdx, wdy)
        fx = scroller.restricted_fx + wdx
        fy = scroller.restricted_fy + wdy
        scroller.set_focus(fx, fy)
        self.world_mouse = self.layer_manager.scrolling_manager.screen_to_world(*self.screen_mouse)
        self.adjust_elastic_box()
        # self.update_view_bounds()

    def update_view_bounds(self):
        scroller = self.weak_scroller()
        scx, scy = self.layer_manager.scrolling_manager.world_to_screen(
            scroller.restricted_fx,
            scroller.restricted_fy,
        )
        hw = scroller.view_w / 2.0
        hh = scroller.view_h / 2.0
        border = self.autoscroll_border
        self.sleft = scx - hw + border
        self.sright = scx + hw - border
        self.sbottom = scy - hh + border
        self.s_top = scy + hh - border

    def mouse_into_world(self):
        worldview = self.weak_worldview()
        # TODO: allow lower limits != 0 ?
        return ((0 <= self.world_mouse[0] <= worldview.width) and
               (0 <= self.world_mouse[1] <= worldview.height))

    def on_key_press(self, k, m):
        binds = self.bindings
        if k in binds:
            self.buttons[binds[k]] = 1
            self.modifiers[binds[k]] = 1
            return True
        return False

    def on_key_release(self, k, m):
        binds = self.bindings
        if k in binds:
            self.buttons[binds[k]] = 0
            self.modifiers[binds[k]] = 0
            return True
        return False

    def on_mouse_motion(self, sx, sy, dx, dy):
        self.update_mouse_position(sx, sy)

    def on_mouse_leave(self, sx, sy):
        self.autoscrolling = False

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def on_mouse_release(self, sx, sy, button, modifiers):
        # should we handle here mod_restricted_mov ?
        wx, wy = self.layer_manager.scrolling_manager.screen_to_world(sx, sy)
        modify_selection = modifiers & self.mod_modify_selection
        if self.dragging:
            # ignore all buttons except left button
            if button != mouse.LEFT:
                return
            if self.drag_selecting:
                self.end_drag_selection(wx, wy, modify_selection)
            elif self.drag_moving:
                self.end_drag_move(wx, wy)
            self.dragging = False
        else:
            if button == mouse.LEFT:
                self.end_click_selection(wx, wy, modify_selection)

    def end_click_selection(self, wx, wy, modify_selection):
        under_mouse_unique = self.single_actor_from_mouse()
        if modify_selection:
            # toggle selected status for unique
            if under_mouse_unique in self.selection:
                self.selection_remove(under_mouse_unique)
            elif under_mouse_unique is not None:
                self.selection_add(under_mouse_unique)
        else:
            # new_selected becomes the current selected
            self.selection.clear()
            if under_mouse_unique is not None:
                self.selection_add(under_mouse_unique)

    def selection_add(self, actor):
        self.selection[actor] = actor.cshape.copy()

    def selection_remove(self, actor):
        del self.selection[actor]

    def end_drag_selection(self, wx, wy, modify_selection):
        new_selection = self.collman.objs_into_box(*self.elastic_box_wminmax)
        if not modify_selection:
            # new_selected becomes the current selected
            self.selection.clear()
        for actor in new_selection:
            self.selection_add(actor)

        self.elastic_box.visible = False
        self.drag_selecting = False

    def on_mouse_drag(self, sx, sy, dx, dy, buttons, modifiers):
        # TODO: inhibir esta llamada si estamos fuera de la client area / viewport
        self.update_mouse_position(sx, sy)
        if not buttons & mouse.LEFT:
            # ignore except for left-btn-drag
            return

        if not self.dragging:
            print("begin drag")
            self.begin_drag()
            return

        if self.drag_selecting:
            # update elastic box
            self.adjust_elastic_box()
        elif self.drag_moving:
            self.restricted_mov = (modifiers & self.mod_restricted_mov)

    def adjust_elastic_box(self):
        # when elastic_box visible this method needs to be called any time
        # world_mouse changes or screen_to_world results changes (scroll, etc)
        wx0, wy0 = self.wdrag_start_point
        wx1, wy1 = self.world_mouse
        wminx = min(wx0, wx1)
        wmaxx = max(wx0, wx1)
        wminy = min(wy0, wy1)
        wmaxy = max(wy0, wy1)
        self.elastic_box_wminmax = wminx, wmaxx, wminy, wmaxy
        self.elastic_box.adjust_from_w_minmax(*self.elastic_box_wminmax)

    def begin_drag(self):
        self.dragging = True
        self.wdrag_start_point = self.world_mouse
        under_mouse_unique = self.single_actor_from_mouse()
        if under_mouse_unique is None:
            # begin drag selection
            self.drag_selecting = True
            self.adjust_elastic_box()
            self.elastic_box.visible = True
            print("begin drag selection: drag_selecting, drag_moving",
                  self.drag_selecting, self.drag_moving)

        else:
            # want drag move
            if under_mouse_unique in self.selection:
                # want to move current selection
                pass
            else:
                # change selection before moving
                self.selection.clear()
                self.selection_add(under_mouse_unique)
            self.begin_drag_move()

    def begin_drag_move(self):
        # begin drag move
        self.drag_moving = True

        # how-to update collman: remove/add vs clear/add all
        # when total number of actors is low anyone will be fine,
        # with high numbers, most probably we move only a small fraction
        # For simplicity I choose remove/add, albeit a hybrid aproach
        # can be implemented later
        self.set_selection_in_collman(False)
#        print "begin drag: drag_selecting, drag_moving", self.drag_selecting, self.drag_moving

    def end_drag_move(self, wx, wy):
        self.set_selection_in_collman(True)
        for actor in self.selection:
            self.selection[actor] = actor.cshape.copy()

        self.drag_moving = False

    def single_actor_from_mouse(self):
        under_mouse = self.collman.objs_touching_point(*self.world_mouse)
        if len(under_mouse) == 0:
            return None
        # return the one with the center most near to mouse, if tie then
        # an arbitrary in the tie
        nearest = None
        near_d = None
        p = euclid.Vector2(*self.world_mouse)
        for actor in under_mouse:
            d = (actor.cshape.center - p).magnitude_squared()
            if nearest is None or (d < near_d):
                nearest = actor
                near_d = d
        return nearest

    def set_selection_in_collman(self, bool_value):
        if self.selection_in_collman == bool_value:
            return
        self.selection_in_collman = bool_value
        if bool_value:
            for actor in self.selection:
                self.collman.add(actor)
        else:
            for actor in self.selection:
                self.collman.remove_tricky(actor)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        # TODO: check if mouse over scroller viewport?
        self.wheel += scroll_y * self.wheel_multiplier


class MainLayer(ScrollableLayer):
    is_event_handler = True

    def __init__(
        self,
        layer_manager: LayerManager,
        width: int,
        height: int,
        scroll_step: int=100,
    ) -> None:
        super().__init__()
        self.layer_manager = layer_manager
        self.scroll_step = scroll_step
        self.grid_manager = GridManager(self, 32, border=2)

        self.actors = []  # TODO type list of ? Sprite ?
        self.width = width
        self.height = height
        self.px_width = width
        self.px_height = height

        # Set scene center on center of screen
        window_size = director.get_window_size()
        self.position = window_size[0] // 2, window_size[1] // 2

    def on_key_press(self, key, modifiers):
        if key == wkey.LEFT:
            self.position = (self.position[0] + self.scroll_step, self.position[1])

        if key == wkey.RIGHT:
            self.position = (self.position[0] - self.scroll_step, self.position[1])

        if key == wkey.UP:
            self.position = (self.position[0], self.position[1] - self.scroll_step)

        if key == wkey.DOWN:
            self.position = (self.position[0], self.position[1] + self.scroll_step)

        if key == wkey.A:
            if self.scale >= 0.3:
                self.scale -= 0.2

        if key == wkey.Z:
            if self.scale <= 4:
                self.scale += 0.2


class Gui(object):
    def __init__(
            self,
            config: Config,
            logger: SynergineLogger,
            terminal: Terminal,
            read_queue_interval: float= 1/60.0,
    ):
        self.config = config
        self.logger = logger
        self._read_queue_interval = read_queue_interval
        self.terminal = terminal
        self.cycle_duration = self.config.core.cycle_duration
        cocos.director.director.init(
            width=640,
            height=480,
            vsync=True,
            resizable=True,
        )

    def run(self):
        self.before_run()
        pyglet.clock.schedule_interval(
            lambda *_, **__: self.terminal.read(),
            self._read_queue_interval,
        )
        cocos.director.director.run(self.get_main_scene())

    def before_run(self) -> None:
        pass

    def get_main_scene(self) -> cocos.cocosnode.CocosNode:
        raise NotImplementedError()

    def before_received(self, package: TerminalPackage):
        pass

    def after_received(self, package: TerminalPackage):
        pass


class TMXGui(Gui):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        terminal: Terminal,
        read_queue_interval: float = 1 / 60.0,
        map_dir_path: str=None,
    ):
        assert map_dir_path
        super(TMXGui, self).__init__(
            config,
            logger,
            terminal,
            read_queue_interval,
        )
        self.map_dir_path = map_dir_path
        self.layer_manager = LayerManager(
            self.config,
            self.logger,
            middleware=TMXMiddleware(
                self.config,
                self.logger,
                self.map_dir_path,
            ),
        )
        self.layer_manager.init()
        self.layer_manager.center()

    def get_main_scene(self) -> cocos.cocosnode.CocosNode:
        return self.layer_manager.main_scene
