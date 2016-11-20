
from synergine2.terminals import Terminal


class CocosTerminal(Terminal):
    def __init__(self):
        super().__init__()
        self.subjects = None

    def receive(self, value):
        pass

    def run(self):
        import cocos
        import pyglet
        from cocos.actions import ScaleBy, Reverse, Repeat

        class KeyDisplay(cocos.layer.Layer):
            # If you want that your layer receives director.window events
            # you must set this variable to 'True'
            is_event_handler = True

            def __init__(self):
                super(KeyDisplay, self).__init__()

                self.text = cocos.text.Label("", x=100, y=280)

                # To keep track of which keys are pressed:
                self.keys_pressed = set()
                self.update_text()
                self.add(self.text)

            def update_text(self):
                key_names = [pyglet.window.key.symbol_string(k) for k in self.keys_pressed]
                text = 'Keys: ' + ','.join(key_names)
                # Update self.text
                self.text.element.text = text

            def on_key_press(self, key, modifiers):
                """This function is called when a key is pressed.
                'key' is a constant indicating which key was pressed.
                'modifiers' is a bitwise or of several constants indicating which
                    modifiers are active at the time of the press (ctrl, shift, capslock, etc.)
                """

                self.keys_pressed.add(key)
                self.update_text()

            def on_key_release(self, key, modifiers):
                """This function is called when a key is released.

                'key' is a constant indicating which key was pressed.
                'modifiers' is a bitwise or of several constants indicating which
                    modifiers are active at the time of the press (ctrl, shift, capslock, etc.)

                Constants are the ones from pyglet.window.key
                """

                self.keys_pressed.remove(key)
                self.update_text()

            def update_text(self):
                key_names = [pyglet.window.key.symbol_string(k) for k in self.keys_pressed]
                text = 'Keys: ' + ','.join(key_names)
                # Update self.text
                self.text.element.text = text

        class MouseDisplay(cocos.layer.Layer):
            is_event_handler = True  #: enable director.window events

            def __init__(self):
                super(MouseDisplay, self).__init__()

                self.posx = 100
                self.posy = 240
                self.text = cocos.text.Label('No mouse events yet', font_size=18, x=self.posx, y=self.posy)
                self.add(self.text)

            def update_text(self, x, y):
                text = 'Mouse @ %d,%d' % (x, y)
                self.text.element.text = text
                self.text.element.x = self.posx
                self.text.element.y = self.posy

            def on_mouse_motion(self, x, y, dx, dy):
                """Called when the mouse moves over the app window with no button pressed

                (x, y) are the physical coordinates of the mouse
                (dx, dy) is the distance vector covered by the mouse pointer since the
                  last call.
                """
                self.update_text(x, y)

            def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
                """Called when the mouse moves over the app window with some button(s) pressed

                (x, y) are the physical coordinates of the mouse
                (dx, dy) is the distance vector covered by the mouse pointer since the
                  last call.
                'buttons' is a bitwise or of pyglet.window.mouse constants LEFT, MIDDLE, RIGHT
                'modifiers' is a bitwise or of pyglet.window.key modifier constants
                   (values like 'SHIFT', 'OPTION', 'ALT')
                """
                self.update_text(x, y)

            def on_mouse_press(self, x, y, buttons, modifiers):
                """This function is called when any mouse button is pressed

                (x, y) are the physical coordinates of the mouse
                'buttons' is a bitwise or of pyglet.window.mouse constants LEFT, MIDDLE, RIGHT
                'modifiers' is a bitwise or of pyglet.window.key modifier constants
                   (values like 'SHIFT', 'OPTION', 'ALT')
                """
                self.posx, self.posy = cocos.director.get_virtual_coordinates(x, y)
                self.update_text(x, y)

        class HelloWorld(cocos.layer.Layer):
            def __init__(self):
                super().__init__()

                label = cocos.text.Label(
                    'Hello, world',
                    font_name='Times New Roman',
                    font_size=32,
                    anchor_x='center', anchor_y='center'
                )
                label.position = 320, 240
                self.add(label)
                scale = ScaleBy(3, duration=0.250)
                label.do(Repeat(scale + Reverse(scale)))

        cocos.director.director.init(resizable=True)
        #hello_layer = HelloWorld()
        main_scene = cocos.scene.Scene(KeyDisplay(), MouseDisplay())
        cocos.director.director.run(main_scene)
