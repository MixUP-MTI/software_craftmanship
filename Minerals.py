from abc import ABC, abstractmethod
from collections import deque, namedtuple

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


class OptimizedRobotFactory:
    def __init__(self, blueprint: Blueprint):
        self.blueprint = blueprint
        self.resource_types = ["ore", "clay", "obsidian", "geode"]
        
        # Calculer les dépenses maximales pour le pruning
        self.max_spend = self._calculate_max_spend()
    
    def _calculate_max_spend(self):
        """Calcule la dépense maximale de chaque ressource par minute"""
        max_spend = {"ore": 0, "clay": 0, "obsidian": 0, "geode": float('inf')}
        
        for robot_type, cost in self.blueprint.robot_costs.items():
            for resource, amount in cost.resources.items():
                if resource != "geode":  # On veut toujours maximiser les geodes
                    max_spend[resource] = max(max_spend[resource], amount)
        
        return max_spend
    
    def _can_build_robot(self, robot_type: str, resources: tuple) -> bool:
        """Vérifie si on peut construire un robot donné"""
        cost = self.blueprint.robot_costs[robot_type]
        resource_dict = dict(zip(self.resource_types, resources))
        
        for resource, amount in cost.resources.items():
            if resource_dict.get(resource, 0) < amount:
                return False
        return True
    
    def _build_robot(self, robot_type: str, resources: tuple) -> tuple:
        """Construit un robot et retourne les nouvelles ressources"""
        cost = self.blueprint.robot_costs[robot_type]
        new_resources = list(resources)
        
        for resource, amount in cost.resources.items():
            resource_idx = self.resource_types.index(resource)
            new_resources[resource_idx] -= amount
        
        return tuple(new_resources)
    
    def max_geodes(self, time_limit: int = 24) -> int:
        """Trouve le nombre maximum de géodes avec DFS optimisé"""
        State = namedtuple("State", "time, resources, robots")
        
        # État initial: temps=0, pas de ressources, 1 robot ore
        start = State(0, (0, 0, 0, 0), (1, 0, 0, 0))
        
        seen = set()
        best_geodes = 0
        stack = deque([start])
        
        while stack:
            time, resources, robots = stack.pop()
            
            # Si on a atteint la limite de temps
            if time == time_limit:
                best_geodes = max(best_geodes, resources[3])  # geode index = 3
                continue
            
            # Pruning: estimation de la borne supérieure
            minutes_left = time_limit - time
            current_geodes = resources[3]
            geode_robots = robots[3]
            
            # Maximum théorique si on construisait un robot geode chaque minute
            potential = current_geodes + geode_robots * minutes_left + minutes_left * (minutes_left - 1) // 2
            
            if potential <= best_geodes:
                continue
            
            # Éviter les états déjà visités
            key = (time, resources, robots)
            if key in seen:
                continue
            seen.add(key)
            
            # Options de construction
            build_options = []
            
            # Pour chaque type de robot
            for i, robot_type in enumerate(self.resource_types):
                # Ne pas construire plus de robots qu'on peut utiliser (sauf geode)
                if robot_type != "geode" and robots[i] >= self.max_spend[robot_type]:
                    continue
                
                # Vérifier si on peut construire ce robot
                if self._can_build_robot(robot_type, resources):
                    build_options.append(robot_type)
            
            # Toujours considérer l'option "ne rien construire"
            build_options.append(None)
            
            # Explorer chaque option
            for choice in build_options:
                new_resources = list(resources)
                new_robots = list(robots)
                
                # Les robots collectent des ressources
                for i in range(4):
                    new_resources[i] += robots[i]
                
                # Construire un nouveau robot si choisi
                if choice is not None:
                    # Déduire le coût
                    new_resources = list(self._build_robot(choice, tuple(new_resources)))
                    # Ajouter le robot
                    robot_idx = self.resource_types.index(choice)
                    new_robots[robot_idx] += 1
                
                # Ajouter le nouvel état à la pile
                new_state = State(time + 1, tuple(new_resources), tuple(new_robots))
                stack.append(new_state)
        
        return best_geodes

def solve_blueprints(filename: str, time_limit: int = 24) -> int:
    """Résout tous les blueprints et calcule la qualité totale"""
    loader = Blueprint.BlueprintLoader(Blueprint.DefaultBlueprintParser())
    blueprints = loader.load(filename)
    
    total_quality = 0
    
    for i, blueprint in enumerate(blueprints, 1):
        print(f"Traitement du Blueprint {i}...")
        
        factory = OptimizedRobotFactory(blueprint)
        max_geodes = factory.max_geodes(time_limit)
        
        quality = max_geodes * i  # ID du blueprint = index + 1
        total_quality += quality
        
        print(f"Blueprint {i}: {max_geodes} géodes, qualité = {quality}")
    
    return total_quality

def solve_blueprints_part2(filename: str, time_limit: int = 32, max_blueprints: int = 3) -> int:
    """Résout les premiers blueprints pour la partie 2 (produit au lieu de somme)"""
    loader = Blueprint.BlueprintLoader(Blueprint.DefaultBlueprintParser())
    blueprints = loader.load(filename)
    
    total_product = 1
    
    for i, blueprint in enumerate(blueprints[:max_blueprints], 1):
        print(f"Traitement du Blueprint {i}...")
        
        factory = OptimizedRobotFactory(blueprint)
        max_geodes = factory.max_geodes(time_limit)
        
        total_product *= max_geodes
        
        print(f"Blueprint {i}: {max_geodes} géodes")
    
    return total_product

if __name__ == "__main__":
    filename = "blueprints.txt"
    
    print("=== Partie 1 (24 minutes) ===")
    total_quality = solve_blueprints(filename, 24)
    print(f"Qualité totale: {total_quality}")
    
    print("\n=== Partie 2 (32 minutes, 3 premiers blueprints) ===")
    total_product = solve_blueprints_part2(filename, 32, 3)
    print(f"Produit total: {total_product}")