# === Dynamic DFS  ===
from collections import deque, namedtuple
from src.blueprint import Blueprint


class OptimizedRobotFactory:
    def __init__(self, blueprint: Blueprint, final_resource: str = None):
        self.blueprint = blueprint
        self.resource_types = list(blueprint.robot_costs.keys())
        self.final_resource = final_resource or self.resource_types[-1]
        self.final_index = self.resource_types.index(self.final_resource)
        self.max_spend = self._calculate_max_spend()
        self.State = namedtuple("State", "time resources robots")

    def _calculate_max_spend(self):
        max_spend = {rtype: 0 for rtype in self.resource_types}
        max_spend[self.final_resource] = float('inf')
        for robot_cost in self.blueprint.robot_costs.values():
            for rtype, amount in robot_cost.resources.items():
                if rtype != self.final_resource:
                    max_spend[rtype] = max(max_spend[rtype], amount)
        return max_spend

    def _can_build_robot(self, robot_type: str, resources: tuple) -> bool:
        cost = self.blueprint.robot_costs[robot_type].resources
        return all(resources[self.resource_types.index(rtype)] >= amount for rtype, amount in cost.items())

    def _build_robot(self, robot_type: str, resources: tuple) -> tuple:
        new_resources = list(resources)
        for rtype, amount in self.blueprint.robot_costs[robot_type].resources.items():
            new_resources[self.resource_types.index(rtype)] -= amount
        return tuple(new_resources)

    def _initial_state(self) -> tuple:
        return self.State(
            0,
            tuple([0] * len(self.resource_types)),
            tuple([1 if i == 0 else 0 for i in range(len(self.resource_types))])
        )

    def _get_build_options(self, resources, robots) -> list:
        """ Return a list of robot types that can be built """
        options = []
        for i, rtype in enumerate(self.resource_types):
            if rtype != self.final_resource and robots[i] >= self.max_spend[rtype]:
                continue
            if self._can_build_robot(rtype, resources):
                options.append(rtype)
        options.append(None)
        return options

    def max_final_resource(self, time_limit: int = 24) -> int:
        start = self._initial_state()
        seen = set()
        best_result = 0
        stack = deque([start])

        while stack:
            time, resources, robots = stack.pop()

            if time == time_limit:
                best_result = max(best_result, resources[self.final_index])
                continue
            # Pruning: estimate the best possible outcome from this state
            minutes_left = time_limit - time
            current = resources[self.final_index]
            current_robots = robots[self.final_index]

            # Max possible using current robots and potential future ones
            potential = current + current_robots * minutes_left + (minutes_left * (minutes_left - 1)) // 2
            if potential <= best_result:
                continue

            key = (time, resources, robots)
            if key in seen:
                continue
            seen.add(key)

            for choice in self._get_build_options(resources, robots):
                new_resources = list(resources)
                for i in range(len(self.resource_types)):
                    new_resources[i] += robots[i]

                new_robots = list(robots)
                if choice:
                    new_resources = list(self._build_robot(choice, tuple(new_resources)))
                    new_robots[self.resource_types.index(choice)] += 1

                stack.append(self.State(time + 1, tuple(new_resources), tuple(new_robots)))

        return best_result