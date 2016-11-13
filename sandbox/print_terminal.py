import time
import sys

sys.path.append('../')

from synergine2.terminals import Terminal, TerminalPackage, TerminalManager


class PrintTerminal(Terminal):
    def receive(self, package: TerminalPackage):
        print(package.value)
        sys.stdout.flush()

    def run(self):
        while self.read():
            print('Hello world')
            sys.stdout.flush()
            time.sleep(1)


terminals_manager = TerminalManager(terminals=[PrintTerminal()])
terminals_manager.start()
for i in range(3):
    time.sleep(2)
    terminals_manager.send(TerminalPackage('Just print me'))

terminals_manager.stop()
