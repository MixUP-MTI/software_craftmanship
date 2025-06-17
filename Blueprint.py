from dataclasses import dataclass
from typing import Dict
from abc import ABC, abstractmethod
from typing import List
import re

@dataclass
class RobotCost:
    # str: Ressource type, int: Quantity
    resources: Dict[str, int]

@dataclass
class Blueprint:
    # str: Robot type
    robot_costs: Dict[str, RobotCost]

class BlueprintParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> Blueprint:
        pass

class DefaultBlueprintParser(BlueprintParser):
    def parse(self, text: str) -> Blueprint:
        robot_costs = {}

        patterns = {
            "ore": r"ore robot costs (\d+) ore",
            "clay": r"clay robot costs (\d+) ore",
            "obsidian": r"obsidian robot costs (\d+) ore and (\d+) clay",
            "geode": r"geode robot costs (\d+) ore and (\d+) obsidian",
            "diamond": r"diamond robot costs (\d+) geode, (\d+) clay and (\d+) obsidian"
        }

        for robot, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                match robot:
                    case "ore":
                        robot_costs["ore"] = RobotCost({"ore": int(match.group(1))})
                    case "clay":
                        robot_costs["clay"] = RobotCost({"ore": int(match.group(1))})
                    case "obsidian":
                        robot_costs["obsidian"] = RobotCost({
                            "ore": int(match.group(1)),
                            "clay": int(match.group(2))
                        })
                    case "geode":
                        robot_costs["geode"] = RobotCost({
                            "ore": int(match.group(1)),
                            "obsidian": int(match.group(2))
                        })
                    case "diamond":
                        robot_costs["diamond"] = RobotCost({
                            "geode": int(match.group(1)),
                            "clay": int(match.group(2)),
                            "obsidian": int(match.group(3))
                        })

        if not robot_costs:
            raise ValueError(f"Invalid blueprint format: {text}")

        return Blueprint(robot_costs)

class BlueprintLoader:
    def __init__(self, parser: BlueprintParser):
        self.parser = parser

    def load(self, filename: str) -> List[Blueprint]:
        with open(filename, 'r') as file:
            return [self.parser.parse(line.strip()) for line in file if line.strip()]

if __name__ == "__main__":
    loader = BlueprintLoader(DefaultBlueprintParser())
    blueprints = loader.load("blueprints.txt")

    for bp in blueprints:
        for robot, cost in bp.robot_costs.items():
            print(f"{robot.capitalize()}, {cost.resources}")