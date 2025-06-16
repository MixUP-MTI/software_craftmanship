from dataclasses import dataclass
from typing import Dict
from abc import ABC, abstractmethod
from typing import List
import re

@dataclass
class RobotCost:
    resources: Dict[str, int]

@dataclass
class Blueprint:
    robot_costs: Dict[str, RobotCost]

class BlueprintParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> Blueprint:
        pass

class DefaultBlueprintParser(BlueprintParser):
    pattern = re.compile(
        r"ore robot costs (\d+) ore.*?"
        r"clay robot costs (\d+) ore.*?"
        r"obsidian robot costs (\d+) ore and (\d+) clay.*?"
        r"geode robot costs (\d+) ore and (\d+) obsidian.*?"
        r"diamond robot costs (\d+) geode, (\d+) clay and (\d+) obsidian"
    )

    def parse(self, text: str) -> Blueprint:
        match = self.pattern.search(text)
        if not match:
            raise ValueError("Invalid blueprint format")

        robot_costs = {
            "ore": RobotCost({"ore": int(match.group(1))}),
            "clay": RobotCost({"ore": int(match.group(2))}),
            "obsidian": RobotCost({
                "ore": int(match.group(3)),
                "clay": int(match.group(4))
            }),
            "geode": RobotCost({
                "ore": int(match.group(5)),
                "obsidian": int(match.group(6))
            }),
            "diamond": RobotCost({
                "geode": int(match.group(7)),
                "clay": int(match.group(8)),
                "obsidian": int(match.group(9)),
            }),
        }

        return Blueprint(robot_costs)


class BlueprintLoader:
    def __init__(self, parser: BlueprintParser):
        self.parser = parser

    def load(self, filename: str) -> List[Blueprint]:
        with open(filename, 'r') as file:
            return [self.parser.parse(line.strip()) for line in file if line.strip()]

if __name__ == "__main__":
    loader = BlueprintLoader(DefaultBlueprintParser())
    blueprints = loader.load("blueprints copy.txt")

    for bp in blueprints:
        for robot, cost in bp.robot_costs.items():
            print(f"{robot.capitalize()}, {cost.resources}")