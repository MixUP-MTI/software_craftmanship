from fastapi import FastAPI
from fastapi.responses import JSONResponse
from Minerals import OptimizedRobotFactory
from Blueprint import BlueprintLoader, DefaultBlueprintParser

app = FastAPI()

@app.get("/blueprints/analyze")
def analyze_blueprints():
    filename = "diamond.txt"
    loader = BlueprintLoader(DefaultBlueprintParser())
    blueprints = loader.load(filename)

    blueprint_results = []
    best_quality = 0
    best_id = 0

    for i, blueprint in enumerate(blueprints, 1):
        factory = OptimizedRobotFactory(blueprint, final_resource="diamond")
        max_diamonds = factory.max_final_resource(time_limit=24)
        quality = max_diamonds * i

        blueprint_results.append({
            "id": str(i),
            "quality": quality
        })

        if quality > best_quality:
            best_quality = quality
            best_id = i

    return JSONResponse({
        "bestBlueprint": str(best_id),
        "blueprints": blueprint_results
    })
