from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from src.blueprint import BlueprintLoader, DefaultBlueprintParser
from src.optimization_service import OptimizedRobotFactory
from src.save import _write_analysis_file


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
        if not final_resource:
            return 0
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

def calculate_and_write_analysis(config: SolverConfig) -> int:
    final_resource_results, blueprint_ids = solve_blueprints(config)
    _write_analysis_file(config.output_file, blueprint_ids, final_resource_results)
    
    result = config.calculator.calculate(final_resource_results, blueprint_ids)
    return result