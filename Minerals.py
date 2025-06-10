import Blueprint

blueprints= Blueprint.parse_blueprints('blueprints.txt')
    
class factory:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.robots = {
            'ore': 1,
            'clay': 0,
            'obsidian': 0,
            'geode': 0
        }
        self.resources = {
            'ore': 0,
            'clay': 0,
            'obsidian': 0,
            'geode': 0
        }
        self.time = 1
        self.time_limit = 24
        self.queue_robot_builders = []

    def collect_resources(self):
        for robot_type, count in self.robots.items():
            if count > 0:
                self.resources[robot_type] += count
                print(f"Collected {count} {robot_type} resources. Total {robot_type}: {self.resources[robot_type]}")

    def build_ore_robot(self):
        if self.resources['ore'] >= self.blueprint.ore_robot_cost:
            self.resources['ore'] -= self.blueprint.ore_robot_cost
            print("Spent", self.blueprint.ore_robot_cost, "ore to build an ore robot.")
            self.queue_robot_builders.append('ore')
    
    def build_clay_robot(self):
        if self.resources['ore'] >= self.blueprint.clay_robot_cost:
            self.resources['ore'] -= self.blueprint.clay_robot_cost
            print("Spent", self.blueprint.clay_robot_cost, "ore to build a clay robot.")
            self.queue_robot_builders.append('clay')

    def build_obsidian_robot(self):
        if (self.resources['ore'] >= self.blueprint.obsidian_robot_cost_ore and
            self.resources['clay'] >= self.blueprint.obsidian_robot_cost_clay):
            self.resources['ore'] -= self.blueprint.obsidian_robot_cost_ore
            self.resources['clay'] -= self.blueprint.obsidian_robot_cost_clay
            print("Spent", self.blueprint.obsidian_robot_cost_ore, "ore and", 
                  self.blueprint.obsidian_robot_cost_clay, "clay to build an obsidian robot.")
            self.queue_robot_builders.append('obsidian')

    def build_geode_robot(self):
        if (self.resources['ore'] >= self.blueprint.geode_robot_cost_ore and
            self.resources['obsidian'] >= self.blueprint.geode_robot_cost_obsidian):
            self.resources['ore'] -= self.blueprint.geode_robot_cost_ore
            self.resources['obsidian'] -= self.blueprint.geode_robot_cost_obsidian
            print("Spent", self.blueprint.geode_robot_cost_ore, "ore and", 
                  self.blueprint.geode_robot_cost_obsidian, "obsidian to build a geode robot.")
            self.queue_robot_builders.append('geode')

    def dequeue_robot_builders(self):
        if self.queue_robot_builders:
            robot_type = self.queue_robot_builders.pop(0)
            self.robots[robot_type] += 1
            print(f"Built a {robot_type} robot. Total {robot_type} robots: {self.robots[robot_type]}")

    def builder_algorithm(self):
        if self.time < self.time_limit/2:
            self.build_geode_robot()
            if self.time%(8) == 0:
                self.build_ore_robot()

            if self.time%(3) == 0:
                self.build_clay_robot()

            if self.time%(1) == 0:
                self.build_obsidian_robot()
        else:

            self.build_geode_robot()
            self.build_geode_robot()
            self.build_geode_robot()

            if self.time%(10) == 0:
                self.build_ore_robot()

            if self.time%(10) == 0:
                self.build_clay_robot()

            if self.time%(4) == 0:
                self.build_obsidian_robot()

    def turn(self):
        while self.time <= self.time_limit:
            print(f"== Minutes: {self.time} ==")
            self.collect_resources()

            self.builder_algorithm()

            self.dequeue_robot_builders()
            self.time += 1
            print()
        print("Final geodes:", self.resources['geode'])
    

# blueprint_instance = Blueprint.Blueprint(4, 2, [3, 14], [2, 7])
blueprint_instance = Blueprint.Blueprint(2, 3, [3, 8], [3, 12])
# factory_instance = factory(blueprints[0])
factory_instance = factory(blueprint_instance)
factory_instance.turn()
