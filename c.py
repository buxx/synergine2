from multiprocessing import Queue
from multiprocessing import Process
from queue import Empty

import time


def start_cocos(input_queue: Queue):
    import cocos
    import pyglet
    from pyglet.event import EVENT_HANDLED
    from cocos.actions import Repeat, ScaleBy, Reverse
    from pyglet.app.xlib import NotificationDevice


    class HelloWorld(cocos.layer.Layer):
        def __init__(self):
            super().__init__()

            self.label = cocos.text.Label(
                '...',
                font_name='Times New Roman',
                font_size=32,
                anchor_x='center', anchor_y='center'
            )
            self.label.position = 320, 240
            scale = ScaleBy(3, duration=5)
            self.label.do( Repeat( scale + Reverse( scale) ) )
            self.add(self.label)

    # class FakeEvent(pyglet.event.EventDispatcher):
    #     pass
    #
    # # following lines register the events that Bunker instances can emit
    # FakeEvent.register_event_type('on_data_received')
    # fake_event = FakeEvent()
    #
    # class Foo(object):
    #     def __init__(self):
    #         fake_event.push_handlers(self)
    #
    #     def on_data_received(self, new_label_text):
    #         hello_layer.label.element.text = new_label_text
    #         return EVENT_HANDLED

    cocos.director.director.init()
    hello_layer = HelloWorld()
    # foo = Foo()

    def loop_hook(director):
        while True:
            try:
                print('hook ' + str(time.time()))
                new_label_text = input_queue.get(block=False, timeout=None)
                hello_layer.label.element.text = new_label_text
                # fake_event.dispatch_event('on_data_received', new_label_text)
                pass
            except Empty:
                return  # Finished to read Queue

    # from pyglet.app import EventLoop
    # old_idle = EventLoop.idle
    #
    # def idle(self):
    #     old_idle(self)
    #     loop_hook(None)
    # EventLoop.idle = idle

    class MyFakeNotif(NotificationDevice):
        def __init__(self, wait_interval=0.100):
            """

            :param wait_interval: MUST BE INFERIOR TO SIMULATION TICK
            :return:
            """
            super().__init__()
            self.wait_interval = wait_interval
            self.last_check = None

        def poll(self):
            if self.last_check is None:
                self.last_check = time.time()
                return True

            elapsed_from_last_check = time.time() - self.last_check
            if elapsed_from_last_check >= self.wait_interval:
                self.last_check = time.time()
                return True

            return False

        def select(self):
            loop_hook(None)

    # Monkey patching
    from pyglet.app import platform_event_loop
    platform_event_loop._select_devices.add(MyFakeNotif())

    main_scene = cocos.scene.Scene(hello_layer)
    cocos.director.director.run(main_scene)


output_queue = Queue()
process = Process(target=start_cocos, kwargs=dict(
    input_queue=output_queue,
))
process.start()

for i in range(20):
    time.sleep(1)
    output_queue.put(str(i))
