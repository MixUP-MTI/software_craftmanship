from collections import deque, namedtuple
from Blueprint import BlueprintLoader, DefaultBlueprintParser, Blueprint

class OptimizedRobotFactory:
    def __init__(self, blueprint: Blueprint):
        self.blueprint = blueprint
        self.resource_types = ["ore", "clay", "obsidian", "geode", "diamond"]
        self.max_spend = self._calculate_max_spend()

    def _calculate_max_spend(self):
        max_spend = {res: 0 for res in self.resource_types}
        max_spend["geode"] = float('inf')  # we want infinite geodes for diamond
        max_spend["diamond"] = float('inf')  # we want infinite diamonds

        for cost in self.blueprint.robot_costs.values():
            for resource, amount in cost.resources.items():
                if resource not in ("geode", "diamond"):
                    max_spend[resource] = max(max_spend[resource], amount)

        return max_spend

    def _can_build_robot(self, robot_type: str, resources: tuple) -> bool:
        cost = self.blueprint.robot_costs[robot_type]
        resource_dict = dict(zip(self.resource_types, resources))

        for resource, amount in cost.resources.items():
            if resource_dict.get(resource, 0) < amount:
                return False
        return True

    def _build_robot(self, robot_type: str, resources: tuple) -> tuple:
        cost = self.blueprint.robot_costs[robot_type]
        new_resources = list(resources)

        for resource, amount in cost.resources.items():
            resource_idx = self.resource_types.index(resource)
            new_resources[resource_idx] -= amount

        return tuple(new_resources)

    def max_diamonds(self, time_limit: int = 24) -> int:
        State = namedtuple("State", "time, resources, robots")
        start = State(0, (0, 0, 0, 0, 0), (1, 0, 0, 0, 0))

        seen = set()
        best_diamonds = 0
        stack = deque([start])

        while stack:
            time, resources, robots = stack.pop()

            if time == time_limit:
                best_diamonds = max(best_diamonds, resources[4])  # index of diamond
                continue

            minutes_left = time_limit - time
            current_diamonds = resources[4]
            diamond_robots = robots[4]
            potential = current_diamonds + diamond_robots * minutes_left + minutes_left * (minutes_left - 1) // 2

            if potential <= best_diamonds:
                continue

            key = (time, resources, robots)
            if key in seen:
                continue
            seen.add(key)

            build_options = []
            for i, robot_type in enumerate(self.resource_types):
                if robot_type not in ("geode", "diamond") and robots[i] >= self.max_spend[robot_type]:
                    continue
                if self._can_build_robot(robot_type, resources):
                    build_options.append(robot_type)

            build_options.append(None)  # wait

            for choice in build_options:
                new_resources = list(resources)
                new_robots = list(robots)

                for i in range(5):
                    new_resources[i] += robots[i]

                if choice is not None:
                    new_resources = list(self._build_robot(choice, tuple(new_resources)))
                    robot_idx = self.resource_types.index(choice)
                    new_robots[robot_idx] += 1

                new_state = State(time + 1, tuple(new_resources), tuple(new_robots))
                stack.append(new_state)

        return best_diamonds

def solve_blueprints(filename: str, time_limit: int = 24) -> int:
    loader = BlueprintLoader(DefaultBlueprintParser())
    blueprints = loader.load(filename)

    total_quality = 0
    for i, blueprint in enumerate(blueprints, 1):
        print(f"Traitement du Blueprint {i}...")
        factory = OptimizedRobotFactory(blueprint)
        max_diamonds = factory.max_diamonds(time_limit)
        quality = max_diamonds * i
        total_quality += quality
        print(f"Blueprint {i}: {max_diamonds} diamonds, qualité = {quality}")
    return total_quality

solve_blueprints("diamond.txt")
