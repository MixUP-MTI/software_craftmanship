import unittest
from Minerals import (
    OptimizedRobotFactory, QualityCalculator, ProductCalculator, SolverConfig, solve_blueprints,
     Blueprint, DefaultBlueprintParser
)
from Blueprint import RobotCost

class TestOptimizedRobotFactory(unittest.TestCase):
    def setUp(self):
        self.blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })

    def test_max_geodes_simple_case(self):
        factory = OptimizedRobotFactory(self.blueprint)
        result = factory.max_final_resource(24)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    def test_max_geodes_with_limited_time(self):
        factory = OptimizedRobotFactory(self.blueprint)
        result = factory.max_final_resource(5)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)


class TestCalculators(unittest.TestCase):
    def test_quality_calculator(self):
        calc = QualityCalculator()
        result = calc.calculate([1, 2, 3], [10, 20, 30])
        self.assertEqual(result, 1*10 + 2*20 + 3*30)

    def test_product_calculator(self):
        calc = ProductCalculator()
        result = calc.calculate([2, 3, 4], [1, 2, 3])
        self.assertEqual(result, 2 * 3 * 4)


class TestBlueprintParsing(unittest.TestCase):
    def test_parse_standard_blueprint(self):
        text = ("Each ore robot costs 4 ore. Each clay robot costs 2 ore. "
                "Each obsidian robot costs 3 ore and 14 clay. "
                "Each geode robot costs 2 ore and 7 obsidian.")
        parser = DefaultBlueprintParser()
        blueprint = parser.parse(text)

        self.assertIn("ore", blueprint.robot_costs)
        self.assertIn("clay", blueprint.robot_costs)
        self.assertIn("obsidian", blueprint.robot_costs)
        self.assertIn("geode", blueprint.robot_costs)
        self.assertNotIn("diamond", blueprint.robot_costs)

    def test_parse_blueprint_with_diamond(self):
        text = ("Each ore robot costs 4 ore. Each clay robot costs 2 ore. "
                "Each obsidian robot costs 3 ore and 14 clay. "
                "Each geode robot costs 2 ore and 7 obsidian. "
                "Each diamond robot costs 1 geode, 2 clay and 3 obsidian.")
        parser = DefaultBlueprintParser()
        blueprint = parser.parse(text)

        self.assertIn("diamond", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["diamond"].resources["geode"], 1)


# Ce test ne fait pas de I/O mais teste solve_blueprints indirectement
class TestSolveBlueprints(unittest.TestCase):
    def test_solve_blueprints_mocked(self):
        from unittest.mock import mock_open, patch

        blueprint_text = (
            "Each ore robot costs 4 ore. Each clay robot costs 2 ore. "
            "Each obsidian robot costs 3 ore and 14 clay. "
            "Each geode robot costs 2 ore and 7 obsidian.\n"
        )

        with patch("builtins.open", mock_open(read_data=blueprint_text)):
            config = SolverConfig(
                filename="fakefile.txt",
                time_limit=24,
                calculator=QualityCalculator(),
                max_blueprints=1,
                output_file="test_output.txt"
            )
            result = solve_blueprints(config)
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 0)

if __name__ == '__main__':
    unittest.main()
