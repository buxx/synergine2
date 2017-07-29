# coding: utf-8
import typing

from dijkstar import find_path

from synergine2.config import Config
from synergine2.simulation import SimulationBehaviour
from synergine2.simulation import SubjectBehaviour
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import Intention
from synergine2.simulation import Simulation
from synergine2.simulation import Event
from synergine2_xyz.simulation import XYZSimulation


class MoveToIntention(Intention):
    def __init__(self, move_to: typing.Tuple[int, int]) -> None:
        self.move_to = move_to
        self.path = []  # type: typing.List[typing.Tuple[int, int]]
        self.path_progression = -1  # type: int


class RequestMoveBehaviour(SimulationBehaviour):
    move_intention_class = MoveToIntention

    @classmethod
    def merge_data(cls, new_data, start_data=None):
        # TODO: behaviour/Thing dedicated to Gui -> Simulation ?
        pass  # This behaviour is designed to be launch by terminal

    def __init__(
        self,
        config: Config,
        simulation: Simulation,
    ):
        super().__init__(config, simulation)
        self.simulation = typing.cast(XYZSimulation, self.simulation)

    def run(self, data):
        # TODO: behaviour/Thing dedicated to Gui -> Simulation ?
        pass  # This behaviour is designed to be launch by terminal

    def action(self, data) -> typing.List[Event]:
        subject_id = data['subject_id']
        move_to = data['move_to']

        try:
            subject = self.simulation.subjects.index[subject_id]
            subject.intentions.set(self.move_intention_class(move_to))
        except KeyError:
            # TODO: log error here
            pass

        return []


class MoveToMechanism(SubjectMechanism):
    def run(self):
        # TODO: Si move to: Si nouveau: a*, si bloque, a*, sinon rien
        # TODO: pourquoi un mechanism plutot que dans run du behaviour ? faire en sorte que lorsque on calcule,
        # si un subject est déjà passé par là et qu'il va au même endroit, ne pas recalculer.
        try:
            # TODO: MoveToIntention doit être configurable
            move = self.subject.intentions.get(MoveToIntention)
            move = typing.cast(MoveToIntention, move)
            new_path = None

            if not move.path:
                # TODO: Must be XYZSimulation !
                start = '{}.{}'.format(*self.subject.position)
                end = '{}.{}'.format(*move.move_to)

                found_path = find_path(self.simulation.graph, start, end)
                move.path = []

                for position in found_path[0]:
                    x, y = map(int, position.split('.'))
                    move.path.append((x, y))

                # Note: We are in process, move change will be lost
                new_path = move.path

                # move.path = []
                # new_path = move.path
                # for i in range(20):
                #     move.path.append((
                #         self.subject.position[0],
                #         self.subject.position[1] + i,
                #     ))

            next_move = move.path[move.path_progression + 1]
            # TODO: fin de path
            if not self.simulation.is_possible_position(next_move):
                # TODO: refaire le path
                new_path = ['...']

            return {
                'new_path': new_path,
            }

        except IndexError:  # TODO: Specialize ? No movement left
            return None
        except KeyError:  # TODO: Specialize ? No MoveIntention
            return None


class MoveEvent(Event):
    def __init__(self, subject_id: int, position: tuple, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.position = position

    def repr_debug(self) -> str:
        return '{}: subject_id:{}, position:{}'.format(
            type(self).__name__,
            self.subject_id,
            self.position,
        )


class MoveToBehaviour(SubjectBehaviour):
    use = [MoveToMechanism]
    move_to_mechanism = MoveToMechanism

    def run(self, data):
        # TODO: on fait vraiment rien ici ? Note: meme si il n'y a pas de new_path, l'action doit s'effectuer
        # du moment qu'il y a une intention de move
        move_to_data = data[self.move_to_mechanism]
        if move_to_data:
            return move_to_data
        return False

    def action(self, data) -> [Event]:
        # TODO: effectuer un move vers une nouvelle position ou faire progresser "l'entre-deux"
        new_path = data['new_path']
        try:
            # TODO: MoveToIntention doit être configurable
            move = self.subject.intentions.get(MoveToIntention)
            move = typing.cast(MoveToIntention, move)

            if new_path:
                move.path = new_path
                move.path_progression = -1

            # TODO: progression et lorsque "vraiment avance d'une case" envoyer le Move
            # pour le moment on move direct
            # TODO: fin de path
            move.path_progression += 1
            new_position = move.path[move.path_progression]
            self.subject.position = new_position

            return [MoveEvent(self.subject.id, new_position)]

        except KeyError:
            # TODO: log ? Il devrait y avoir un move puisque data du run/mechanism !
            pass
