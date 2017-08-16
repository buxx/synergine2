# coding: utf-8
from synergine2.config import Config
from synergine2_xyz.physics import Physics, TMXPhysics
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.subjects import XYZSubject


class TileStrategySimulation(XYZSimulation):
    behaviours_classes = [

    ]

    def __init__(
        self,
        config: Config,
        map_file_path: str,
    ) -> None:
        self.map_file_path = map_file_path
        super().__init__(config)

    def create_physics(self) -> Physics:
        return TMXPhysics(
            config=self.config,
            map_file_path=self.map_file_path,
        )


class TileStrategySubjects(XYZSubjects):
    pass


class BaseSubject(XYZSubject):
    pass
