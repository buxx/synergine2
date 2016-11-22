from multiprocessing import Queue
from multiprocessing import Process
from queue import Empty

import time
from pyglet.clock import schedule


def start_cocos(input_queue: Queue):
    ######
    # CODE INSIDE SUBPROCESS
    import cocos
    from cocos.actions import Repeat, ScaleBy, Reverse

    class HelloWorld(cocos.layer.Layer):
        is_event_handler = True

        def tick(self):
            self.dispatch_event('on_update')

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
            self.label.do(Repeat(scale + Reverse(scale)))
            self.add(self.label)

    cocos.director.director.init()
    hello_layer = HelloWorld()

    def read_queue():
        while True:
            try:
                print('hook ' + str(time.time()))
                new_label_text = input_queue.get(block=False, timeout=None)
                hello_layer.label.element.text = new_label_text
                pass
            except Empty:
                return  # Finished to read Queue

    main_scene = cocos.scene.Scene(hello_layer)

    # TODO: Ecrire un code de demo sans la queue/process
    # qui doit effectuer un truc toutes les secondes (changer texte de pyglet)
    # Et demader si c la bonne marche a suivre)

    def toto(ts, *args, **kwargs):
        read_queue()
    schedule(toto)

    cocos.director.director.run(main_scene)
    # END OF SUBPROCESS CODE
    ###########


output_queue = Queue()
process = Process(target=start_cocos, kwargs=dict(
    input_queue=output_queue,
))
process.start()

for i in range(40):
    time.sleep(1)
    output_queue.put(str(i))
