from dataclasses import dataclass
from typing import List, Optional
from abc import ABC, abstractmethod
from collections import deque, namedtuple
from Blueprint import Blueprint, BlueprintLoader, DefaultBlueprintParser
from typing import List


# === Optimiseur DFS dynamique ===
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

# === Solvers ===
class ResultCalculator(ABC):
    """Interface to calculate the final resource result (Single Responsibility)"""
    @abstractmethod
    def calculate(self, final_resource: List[int], blueprint_ids: List[int]) -> int:
        pass

class QualityCalculator(ResultCalculator):
    """Calculates the total quality (sum of final resource * ID)"""
    def calculate(self, final_resource: List[int], blueprint_ids: List[int]) -> int:
        return sum(final_resource_count * blueprint_id 
                  for final_resource_count, blueprint_id in zip(final_resource, blueprint_ids))

class ProductCalculator(ResultCalculator):
    """Calculate the product of all final resource"""
    def calculate(self, final_resource: List[int], _) -> int:
        result = 1
        for final_resource_count in final_resource:
            result *= final_resource_count
        return result
    
@dataclass
class SolverConfig:
    """Configuration for the blueprint solver"""
    filename: str
    time_limit: int = 24
    calculator: Optional[ResultCalculator] = None
    max_blueprints: Optional[int] = None
    output_file: str = "./analysis.txt"
    final_resource: str = "geode"

def solve_blueprints(config: SolverConfig) -> int:
    """
    Resolve blueprints according to the provided calculation strategy
    Args:
        filename: File containing the blueprints
        time_limit: Time limit in minutes
        calculator: Calculation strategy for the result (default: QualityCalculator)
        max_blueprints: Maximum number of blueprints to process (None = all)
        output_file: Output file for the analysis
    Returns:
        tuple of final resource results and blueprint IDs
    """
    if config.calculator is None:
        config.calculator = QualityCalculator()
    
    loader = BlueprintLoader(DefaultBlueprintParser())
    blueprints = loader.load(config.filename)
    
    if config.max_blueprints is not None:
        blueprints = blueprints[:config.max_blueprints]

    final_resource_results = []
    blueprint_ids = []
    blueprint_qualities = []
    
    for i, blueprint in enumerate(blueprints, 1):
        print(f"Handle Blueprint {i}...")
        
        factory = OptimizedRobotFactory(blueprint, final_resource=config.final_resource)
        max_geodes = factory.max_final_resource(config.time_limit)
        
        final_resource_results.append(max_geodes)
        blueprint_ids.append(i)
        
        quality = max_geodes * i
        blueprint_qualities.append(quality)
        
        print(f"Blueprint {i}: {max_geodes} {config.final_resource}s")
    
    return (final_resource_results, blueprint_ids)
    

def _write_analysis_file(output_file: str, blueprint_ids: List[int], final_resource_results: List[int]) -> None:
    """Writes the analysis file with the qualities of the blueprints"""
    with open(output_file, 'w', encoding='utf-8') as f:
        qualities = []
        for ressource, id in zip(final_resource_results, blueprint_ids):
            qualities.append(ressource * id)

        for blueprint_id, quality in zip(blueprint_ids, qualities):
            f.write(f"Blueprint {blueprint_id}: {quality}\n")
        
        if qualities:
            best_index = qualities.index(max(qualities))
            best_blueprint_id = blueprint_ids[best_index]
            f.write(f"\nBest blueprint is the blueprint {best_blueprint_id}.\n")


def calculate_and_write_analysis(config: SolverConfig) -> int:
    final_resource_results, blueprint_ids = solve_blueprints(config)
    _write_analysis_file(config.output_file, blueprint_ids, final_resource_results)
    
    result = config.calculator.calculate(final_resource_results, blueprint_ids)
    return result


# === Main ===
if __name__ == "__main__":
    filename = "blueprints.txt"
    filenameDiamond = "diamond.txt"
    
    print("=== Partie 1 : Max Géodes en 24 min ===")
    config1 = SolverConfig(
        filename=filename,
        time_limit=24,
        calculator=QualityCalculator()
    )
    print(f"Produit total: {calculate_and_write_analysis(config1)}")
    
    print("\n=== Partie 2 : Produit des Géodes sur les 3 premiers en 32 min ===")
    config2 = SolverConfig(
        filename=filename,
        time_limit=32,
        calculator=ProductCalculator(),
        max_blueprints=3
    )
    print(f"Produit total: {calculate_and_write_analysis(config2)}")
    
    print("\n=== Partie 3 : Produit des Diamants sur les 2 blueprints en 24 min ===")
    config3 = SolverConfig(
        filename=filenameDiamond,
        time_limit=24,
        calculator=ProductCalculator(),
        final_resource='diamond'
    )
    print(f"Produit total: {calculate_and_write_analysis(config3)}")