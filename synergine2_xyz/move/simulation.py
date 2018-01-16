# coding: utf-8
import time
import typing

from synergine2.config import Config
from synergine2.simulation import SimulationBehaviour
from synergine2.simulation import Simulation
from synergine2.simulation import Event
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import SubjectBehaviour
from synergine2_xyz.move.intention import MoveToIntention
from synergine2_xyz.simulation import XYZSimulation


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
            subject.intentions.set(self.move_intention_class(
                move_to,
                start_time=time.time(),
                gui_action=data['gui_action'],
            ))
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
                move.path = self.simulation.physics.found_path(
                    start=self.subject.position,
                    end=move.move_to,
                    subject=self.subject,
                )

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
                'last_intention_time': move.last_intention_time,
                'just_reach': move.just_reach,
                'initial': move.initial,
                'gui_action': move.gui_action,
            }

        except IndexError:  # TODO: Specialize ? No movement left
            return {
                'finished': True,
            }
        except KeyError:  # TODO: Specialize ? No MoveIntention
            return None


class FinishMoveEvent(Event):
    def __init__(
        self,
        subject_id: int,
        from_position: typing.Tuple[int, int],
        to_position: typing.Tuple[int, int],
        gui_action: typing.Any,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.from_position = from_position
        self.to_position = to_position
        self.gui_action = gui_action

    def repr_debug(self) -> str:
        return '{}: subject_id:{}, from_position:{} to_position: {}'.format(
            type(self).__name__,
            self.subject_id,
            self.from_position,
            self.to_position,
        )


class StartMoveEvent(Event):
    def __init__(
        self,
        subject_id: int,
        from_position: typing.Tuple[int, int],
        to_position: typing.Tuple[int, int],
        gui_action: typing.Any,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.from_position = from_position
        self.to_position = to_position
        self.gui_action = gui_action

    def repr_debug(self) -> str:
        return '{}: subject_id:{}, from_position:{} to_position: {}'.format(
            type(self).__name__,
            self.subject_id,
            self.from_position,
            self.to_position,
        )


class MoveToBehaviour(SubjectBehaviour):
    move_to_mechanism = MoveToMechanism
    use = [move_to_mechanism]

    def run(self, data):
        move_to_data = data[self.move_to_mechanism]
        if move_to_data:
            if move_to_data.get('finished'):
                return move_to_data

            if self._can_move_to_next_step(move_to_data):
                move_to_data['reach_next'] = True
                return move_to_data

            if self._is_fresh_new_step(move_to_data):
                move_to_data['reach_next'] = False
                return move_to_data

        return False

    def _can_move_to_next_step(self, move_to_data: dict) -> bool:
        raise NotImplementedError()

    def _is_fresh_new_step(self, move_to_data: dict) -> bool:
        return move_to_data['just_reach'] or move_to_data['initial']

    def action(self, data) -> [Event]:
        # TODO: MoveToIntention doit être configurable
        try:
            if data.get('finished'):
                self.subject.intentions.remove(MoveToIntention)
                return []
            move = self.subject.intentions.get(MoveToIntention)
        except KeyError:  # TODO: Specialize exception
            # Action don't exist anymore
            return []

        move = typing.cast(MoveToIntention, move)
        new_path = data['new_path']
        if new_path:
            move.path = new_path
            move.path_progression = -1

        previous_position = self.subject.position
        new_position = move.path[move.path_progression + 1]

        if data['reach_next']:
            # TODO: fin de path
            move.path_progression += 1
            self.subject.position = new_position
            move.last_intention_time = time.time()
            move.just_reach = True
            event = FinishMoveEvent(
                self.subject.id,
                previous_position,
                new_position,
                gui_action=move.gui_action,
            )
        else:
            move.just_reach = False
            event = StartMoveEvent(
                self.subject.id,
                previous_position,
                new_position,
                gui_action=move.gui_action,
            )

        move.initial = False
        # Note: Need to explicitly set to update shared data
        self.subject.intentions.set(move)

        return [event]
