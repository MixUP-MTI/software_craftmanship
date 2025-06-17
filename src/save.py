from typing import List

def _write_analysis_file(output_file: str, blueprint_ids: List[int], final_resource_results: List[int]) -> None:
    """Writes the analysis file with the qualities of the blueprints"""
    with open(output_file, 'w', encoding='utf-8') as f:
        qualities = []
        for resource, id in zip(final_resource_results, blueprint_ids):
            qualities.append(resource * id)

        for blueprint_id, quality in zip(blueprint_ids, qualities):
            f.write(f"Blueprint {blueprint_id}: {quality}\n")
        
        if qualities:
            best_index = qualities.index(max(qualities))
            best_blueprint_id = blueprint_ids[best_index]
            f.write(f"\nBest blueprint is the blueprint {best_blueprint_id}.\n")