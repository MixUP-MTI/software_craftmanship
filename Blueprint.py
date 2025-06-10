import re

class Blueprint:
    def __init__(self, ore_robot_cost, clay_robot_cost, obsidian_robot_cost, geode_robot_cost):
        self.ore_robot_cost = ore_robot_cost
        self.clay_robot_cost = clay_robot_cost
        self.obsidian_robot_cost_ore = obsidian_robot_cost[0]
        self.obsidian_robot_cost_clay = obsidian_robot_cost[1]
        self.geode_robot_cost_ore = geode_robot_cost[0]
        self.geode_robot_cost_obsidian = geode_robot_cost[1]

    def __str__(self):
        return (f"Ore Robot Cost: {self.ore_robot_cost}, "
                f"Clay Robot Cost: {self.clay_robot_cost}, "
                f"Obsidian Robot Cost: {self.obsidian_robot_cost_ore} ore and {self.obsidian_robot_cost_clay} clay, "
                f"Geode Robot Cost: {self.geode_robot_cost_ore} ore and {self.geode_robot_cost_obsidian} obsidian")


def parse_blueprints(filename):
    blueprints = []

    pattern = re.compile(
        r"ore robot costs (\d+) ore.*?clay robot costs (\d+) ore.*?"
        r"obsidian robot costs (\d+) ore and (\d+) clay.*?"
        r"geode robot costs (\d+) ore and (\d+) obsidian"
    )

    with open(filename, 'r') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                ore_cost = int(match.group(1))
                clay_cost = int(match.group(2))
                obsidian_cost = [int(match.group(3)), int(match.group(4))]
                geode_cost = [int(match.group(5)), int(match.group(6))]
                blueprints.append(Blueprint(ore_cost, clay_cost, obsidian_cost, geode_cost))
    return blueprints