from dataclasses import dataclass
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
import re
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

    def _calculate_max_spend(self):
        max_spend = {rtype: 0 for rtype in self.resource_types}
        max_spend[self.final_resource] = float('inf')

        for cost in self.blueprint.robot_costs.values():
            for r, v in cost.resources.items():
                if r != self.final_resource:
                    max_spend[r] = max(max_spend[r], v)

        return max_spend

    def _can_build_robot(self, robot_type: str, resources: tuple) -> bool:
        cost = self.blueprint.robot_costs[robot_type].resources
        return all(resources[self.resource_types.index(r)] >= v for r, v in cost.items())

    def _build_robot(self, robot_type: str, resources: tuple) -> tuple:
        new_resources = list(resources)
        for r, v in self.blueprint.robot_costs[robot_type].resources.items():
            new_resources[self.resource_types.index(r)] -= v
        return tuple(new_resources)

    def max_final_resource(self, time_limit: int = 24) -> int:
        State = namedtuple("State", "time resources robots")
        start = State(0, tuple([0] * len(self.resource_types)), tuple([1 if i == 0 else 0 for i in range(len(self.resource_types))]))

        seen = set()
        best_result = 0
        stack = deque([start])

        while stack:
            time, resources, robots = stack.pop()

            if time == time_limit:
                best_result = max(best_result, resources[self.final_index])
                continue

            # Pruning
            minutes_left = time_limit - time
            current = resources[self.final_index]
            current_robots = robots[self.final_index]
            potential = current + current_robots * minutes_left + (minutes_left * (minutes_left - 1)) // 2
            if potential <= best_result:
                continue

            key = (time, resources, robots)
            if key in seen:
                continue
            seen.add(key)

            build_options = []
            for i, rtype in enumerate(self.resource_types):
                if rtype != self.final_resource and robots[i] >= self.max_spend[rtype]:
                    continue
                if self._can_build_robot(rtype, resources):
                    build_options.append(rtype)

            build_options.append(None)  # option de ne rien construire

            for choice in build_options:
                new_resources = list(resources)
                for i in range(len(self.resource_types)):
                    new_resources[i] += robots[i]

                new_robots = list(robots)
                if choice:
                    new_resources = list(self._build_robot(choice, tuple(new_resources)))
                    new_robots[self.resource_types.index(choice)] += 1

                stack.append(State(time + 1, tuple(new_resources), tuple(new_robots)))

        return best_result

# === Solvers ===
class ResultCalculator(ABC):
    """Interface pour calculer le résultat final (Single Responsibility)"""
    
    @abstractmethod
    def calculate(self, geodes: List[int], blueprint_ids: List[int]) -> int:
        pass

class QualityCalculator(ResultCalculator):
    """Calcule la qualité totale (somme des géodes * ID)"""
    
    def calculate(self, geodes: List[int], blueprint_ids: List[int]) -> int:
        return sum(geode_count * blueprint_id 
                  for geode_count, blueprint_id in zip(geodes, blueprint_ids))

class ProductCalculator(ResultCalculator):
    """Calcule le produit des géodes"""
    
    def calculate(self, geodes: List[int], blueprint_ids: List[int]) -> int:
        result = 1
        for geode_count in geodes:
            result *= geode_count
        return result
    
@dataclass
class SolverConfig:
    """Configuration pour le solveur de blueprints"""
    filename: str
    time_limit: int = 24
    calculator: Optional[ResultCalculator] = None
    max_blueprints: Optional[int] = None
    output_file: str = "./analysis.txt"
    final_resource: str = "geode"

def solve_blueprints(config: SolverConfig) -> int:
    """
    Résout les blueprints selon la stratégie de calcul fournie
    
    Args:
        filename: Fichier contenant les blueprints
        time_limit: Limite de temps en minutes
        calculator: Stratégie de calcul du résultat (par défaut: QualityCalculator)
        max_blueprints: Nombre maximum de blueprints à traiter (None = tous)
        output_file: Fichier de sortie pour l'analyse
    
    Returns:
        Résultat calculé selon la stratégie choisie
    """
    # Dependency Inversion: dépend de l'abstraction ResultCalculator
    if config.calculator is None:
        config.calculator = QualityCalculator()
    
    loader = BlueprintLoader(DefaultBlueprintParser())
    blueprints = loader.load(config.filename)
    
    # Open/Closed: facile d'ajouter de nouvelles limites sans modifier le code
    if config.max_blueprints is not None:
        blueprints = blueprints[:config.max_blueprints]

    final_resource_results = []
    blueprint_ids = []
    blueprint_qualities = []
    
    for i, blueprint in enumerate(blueprints, 1):
        print(f"Traitement du Blueprint {i}...")
        
        factory = OptimizedRobotFactory(blueprint, final_resource=config.final_resource)
        max_geodes = factory.max_final_resource(config.time_limit)
        
        final_resource_results.append(max_geodes)
        blueprint_ids.append(i)
        
        # Calcul de la qualité pour chaque blueprint (géodes * ID)
        quality = max_geodes * i
        blueprint_qualities.append(quality)
        
        print(f"Blueprint {i}: {max_geodes} {config.final_resource}s")
    
    # Écriture du fichier d'analyse
    _write_analysis_file(config.output_file, blueprint_ids, blueprint_qualities)
    
    # Liskov Substitution: n'importe quelle implémentation de ResultCalculator fonctionne
    result = config.calculator.calculate(final_resource_results, blueprint_ids)
    return result


def _write_analysis_file(output_file: str, blueprint_ids: List[int], qualities: List[int]) -> None:
    """Écrit le fichier d'analyse avec les qualités des blueprints"""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Écriture des qualités de chaque blueprint
        for blueprint_id, quality in zip(blueprint_ids, qualities):
            f.write(f"Blueprint {blueprint_id}: {quality}\n")
        
        # Trouve le meilleur blueprint
        if qualities:
            best_index = qualities.index(max(qualities))
            best_blueprint_id = blueprint_ids[best_index]
            f.write(f"\nBest blueprint is the blueprint {best_blueprint_id}.\n")


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
    print(f"Score total: {solve_blueprints(config1)}")
    
    print("\n=== Partie 2 : Produit des Géodes sur les 3 premiers en 32 min ===")
    config2 = SolverConfig(
        filename=filename,
        time_limit=32,
        calculator=ProductCalculator(),
        max_blueprints=3
    )
    print(f"Produit total: {solve_blueprints(config2)}")
    
    print("\n=== Partie 3 : Produit des Diamants sur les 2 blueprints en 24 min ===")
    config3 = SolverConfig(
        filename=filenameDiamond,
        time_limit=24,
        calculator=ProductCalculator(),
        final_resource='diamond'
    )
    print(f"Produit total: {solve_blueprints(config3)}")