import os
from src.solver import  ProductCalculator, QualityCalculator, SolverConfig, calculate_and_write_analysis

    

# === Main ===
if __name__ == "__main__":
    filename = os.path.join("data", "blueprints.txt")
    filenameDiamond = os.path.join("data", "diamond.txt")
    fileOutput = os.path.join("data", "analysis.txt")
    
    print("=== Partie 1 : Max Géodes en 24 min ===")
    config1 = SolverConfig(
        filename=filename,
        time_limit=24,
        calculator=QualityCalculator(),
        output_file=fileOutput,
    )
    print(f"Produit total: {calculate_and_write_analysis(config1)}")
    
    print("\n=== Partie 2 : Produit des Géodes sur les 3 premiers en 32 min ===")
    config2 = SolverConfig(
        filename=filename,
        time_limit=32,
        calculator=ProductCalculator(),
        max_blueprints=3,
        output_file=fileOutput,
    )
    print(f"Produit total: {calculate_and_write_analysis(config2)}")
    
    print("\n=== Partie 3 : Produit des Diamants sur les 2 blueprints en 24 min ===")
    config3 = SolverConfig(
        filename=filenameDiamond,
        time_limit=24,
        calculator=ProductCalculator(),
        final_resource='diamond',
        output_file=fileOutput,
    )
    print(f"Produit total: {calculate_and_write_analysis(config3)}")