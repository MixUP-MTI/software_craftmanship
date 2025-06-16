from abc import ABC, abstractmethod

import Blueprint

class RobotBuilder(ABC):
    @abstractmethod
    def can_build(self, resources: dict) -> bool: pass

    @abstractmethod
    def build(self, resources: dict): pass

    @abstractmethod
    def robot_type(self) -> str: pass

class OreRobotBuilder(RobotBuilder):
    def __init__(self, cost: int):
        self.cost = cost

    def can_build(self, resources):
        return resources["ore"] >= self.cost

    def build(self, resources):
        resources["ore"] -= self.cost

    def robot_type(self):
        return "ore"
    
class ClayRobotBuilder(RobotBuilder):
    def __init__(self, cost: int):
        self.cost = cost

    def can_build(self, resources):
        return resources["ore"] >= self.cost

    def build(self, resources):
        resources["ore"] -= self.cost

    def robot_type(self):
        return "clay"
    
class ObsidianRobotBuilder(RobotBuilder):
    def __init__(self, cost: dict):
        self.cost = cost

    def can_build(self, resources):
        return (resources["ore"] >= self.cost["ore"] and
                resources["clay"] >= self.cost["clay"])

    def build(self, resources):
        resources["ore"] -= self.cost["ore"]
        resources["clay"] -= self.cost["clay"]

    def robot_type(self):
        return "obsidian"
    
class GeodeRobotBuilder(RobotBuilder):
    def __init__(self, cost: dict):
        self.cost = cost

    def can_build(self, resources):
        return (resources["ore"] >= self.cost["ore"] and
                resources["obsidian"] >= self.cost["obsidian"])

    def build(self, resources):
        resources["ore"] -= self.cost["ore"]
        resources["obsidian"] -= self.cost["obsidian"]

    def robot_type(self):
        return "geode"
    
### end builders

class BuildStrategy(ABC):
    @abstractmethod
    def choose_builders(self, builders: list, time: int, time_limit: int, resources: dict) -> list:
        pass

class DefaultBuildStrategy(BuildStrategy):
    def choose_builders(self, builders, time, time_limit):
        chosen = []
        if time < time_limit / 2:
            for builder in builders:
                if builder.robot_type() == "geode" and builder.can_build:
                    chosen.append(builder)
            if time % 8 == 0:
                chosen += [b for b in builders if b.robot_type() == "ore"]
        else:
            chosen += [b for b in builders if b.robot_type() == "geode"]
        return chosen
    
class SmartBuildStrategy(BuildStrategy):
    def __init__(self, blueprint):
        self.costs = blueprint
        self.max_needed = {
            'ore': max(r.resources.get('ore', 0) for r in blueprint.values()),
            'clay': blueprint['obsidian'].resources.get('clay', 0),
            'obsidian': blueprint['geode'].resources.get('obsidian', 0),
        }


    def choose_builders(self, builders, time, time_limit, resources, robots) -> list:
        def need_more(rtype, current_bots):
            if rtype == 'geode':
                return True

            max_needed = self.max_needed.get(rtype, float('inf'))

            remaining_time = time_limit - time
            max_useful = max_needed * remaining_time

            if resources.get(rtype, 0) + current_bots * remaining_time >= max_useful:
                return False

            # sinon on a besoin d'en construire plus
            return current_bots < max_needed

        for priority_type in ['geode', 'obsidian', 'clay', 'ore']:
            for builder in builders:
                if builder.robot_type() == priority_type and builder.can_build(resources):
                    if need_more(priority_type, robots.get(priority_type, 0)):
                        return [builder]
        return []

class Factory:
    def __init__(self, builders: list[RobotBuilder], strategy: BuildStrategy, time_limit=24):
        self.builders = builders
        self.strategy = strategy
        self.robots = {b.robot_type(): 0 for b in builders}
        self.robots["ore"] = 1  # Start with one ore robot
        self.resources = {b.robot_type(): 0 for b in builders}
        self.queue_robot_builders = []
        self.time = 1
        self.time_limit = time_limit

    def collect_resources(self):
        for rtype, count in self.robots.items():
            if count == 0:
                continue
            self.resources[rtype] += count
            print(f"Collected {count} {rtype} resources. Total {rtype}: {self.resources[rtype]}")


    def build_robots(self):
        for builder in self.strategy.choose_builders(self.builders, self.time, self.time_limit, self.resources, self.robots):
            if builder.can_build(self.resources):
                builder.build(self.resources)
                self.queue_robot_builders.append(builder.robot_type())
                print("Spent", self.resources, "to build an", builder.robot_type(), "robot.")
            

    def dequeue_robot_builders(self):
        while self.queue_robot_builders:
            rtype = self.queue_robot_builders.pop(0)
            self.robots[rtype] += 1
            print(f"Built a {rtype} robot. Total {rtype} robots: {self.robots[rtype]}")


    def turn(self):
        while self.time <= self.time_limit:
            print(f"== Minutes: {self.time} ==")
            self.collect_resources()
            self.build_robots()
            self.dequeue_robot_builders()
            self.time += 1
            print()
        last_item = list(self.resources.items())[-1]
        print(f"Final {last_item[0]}: {last_item[1]}")


loader = Blueprint.BlueprintLoader(Blueprint.DefaultBlueprintParser())
blueprints = loader.load("test.txt")
for bp in blueprints:
    builders = [
        OreRobotBuilder(bp.robot_costs['ore'].resources['ore']),
        ClayRobotBuilder(bp.robot_costs['clay'].resources['ore']),
        ObsidianRobotBuilder(bp.robot_costs['obsidian'].resources),
        GeodeRobotBuilder(bp.robot_costs['geode'].resources),
    ]
    print(bp.robot_costs)
    strategy = SmartBuildStrategy(bp.robot_costs)
    factory = Factory(builders, strategy)
    factory.turn()