# coding: utf-8


# TODO: Reprendre les events Move, pour les lister tous ici
from synergine2.simulation import Event


class NewVisibleOpponent(Event):
    def __init__(
        self,
        observer_subject_id: int,
        observed_subject_id: int,
    ) -> None:
        self.observer_subject_id = observer_subject_id
        self.observed_subject_id = observed_subject_id


class NoLongerVisibleOpponent(Event):
    def __init__(
        self,
        observer_subject_id: int,
        observed_subject_id: int,
    ) -> None:
        self.observer_subject_id = observer_subject_id
        self.observed_subject_id = observed_subject_id
