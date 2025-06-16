from abc import ABC, abstractmethod
from collections import deque, namedtuple
from typing import List

import Blueprint

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

def solve_blueprints(filename: str, time_limit: int = 24, calculator: ResultCalculator = None, max_blueprints: int = None, output_file: str = "./analysis.txt") -> int:
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
    if calculator is None:
        calculator = QualityCalculator()
    
    loader = Blueprint.BlueprintLoader(Blueprint.DefaultBlueprintParser())
    blueprints = loader.load(filename)
    
    # Open/Closed: facile d'ajouter de nouvelles limites sans modifier le code
    if max_blueprints is not None:
        blueprints = blueprints[:max_blueprints]
    
    geodes_results = []
    blueprint_ids = []
    blueprint_qualities = []
    
    for i, blueprint in enumerate(blueprints, 1):
        print(f"Traitement du Blueprint {i}...")
        
        factory = OptimizedRobotFactory(blueprint)
        max_geodes = factory.max_geodes(time_limit)
        
        geodes_results.append(max_geodes)
        blueprint_ids.append(i)
        
        # Calcul de la qualité pour chaque blueprint (géodes * ID)
        quality = max_geodes * i
        blueprint_qualities.append(quality)
        
        print(f"Blueprint {i}: {max_geodes} géodes")
    
    # Écriture du fichier d'analyse
    _write_analysis_file(output_file, blueprint_ids, blueprint_qualities)
    
    # Liskov Substitution: n'importe quelle implémentation de ResultCalculator fonctionne
    result = calculator.calculate(geodes_results, blueprint_ids)
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

# Fonctions de commodité pour maintenir la compatibilité
def solve_blueprints_part1(filename: str, time_limit: int = 24, output_file: str = "./analysis.txt") -> int:
    """Partie 1: calcule la qualité totale"""
    return solve_blueprints(filename, time_limit, QualityCalculator(), None, output_file)

def solve_blueprints_part2(filename: str, time_limit: int = 32, max_blueprints: int = 3, output_file: str = "./analysis.txt") -> int:
    """Partie 2: calcule le produit des géodes"""
    return solve_blueprints(filename, time_limit, ProductCalculator(), max_blueprints, output_file)

# Exemple d'usage
if __name__ == "__main__":
    filename = "blueprints.txt"
    
    print("=== Partie 1 (24 minutes) ===")
    total_quality = solve_blueprints_part1(filename)
    print(f"Qualité totale: {total_quality}")
    
    print("\n=== Partie 2 (32 minutes, 3 premiers blueprints) ===")
    total_product = solve_blueprints_part2(filename)
    print(f"Produit total: {total_product}")