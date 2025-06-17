from http.client import HTTPException
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.main import ProductCalculator, SolverConfig, solve_blueprints
from src.blueprint import BlueprintLoader, DefaultBlueprintParser

app = FastAPI()

@app.get("/blueprints/analyze")
def analyze_blueprints():
    filename = "diamond.txt"
    try:
        loader = BlueprintLoader(DefaultBlueprintParser())
        blueprints = loader.load(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des blueprints : {str(e)}")

    if not blueprints:
        raise HTTPException(status_code=404, detail="Aucun blueprint trouvé dans le fichier.")

    config = SolverConfig(
        filename=filename,
        time_limit=24,
        calculator=ProductCalculator(),
        final_resource='diamond'
    )
    
    (final_resource_results, blueprint_ids) = solve_blueprints(config)
    blueprint_results = []
    best_quality = 0
    best_id = 0

    for resource, id in zip(final_resource_results, blueprint_ids):
        quality = resource * id

        blueprint_results.append({
            "id": str(id),
            "quality": quality
        })

        if quality > best_quality:
            best_quality = quality
            best_id = id

    return JSONResponse({
        "bestBlueprint": str(best_id),
        "blueprints": blueprint_results
    })
