import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.blueprint import Blueprint, RobotCost
from src.optimization_service import OptimizedRobotFactory


class TestOptimizedRobotFactory(unittest.TestCase):

    def setUp(self):
        self.simple_blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })
        self.complex_blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7}),
            "diamond": RobotCost({"geode": 1, "clay": 8, "obsidian": 7})
        })

    def test_init_and_final_resource(self):
        factory = OptimizedRobotFactory(self.complex_blueprint, final_resource="diamond")
        self.assertEqual(factory.final_resource, "diamond")
        self.assertEqual(factory.final_index, 4)

    def test_calculate_max_spend(self):
        factory = OptimizedRobotFactory(self.simple_blueprint)
        self.assertEqual(factory.max_spend["ore"], 4)
        self.assertEqual(factory.max_spend["clay"], 14)
        self.assertEqual(factory.max_spend["obsidian"], 7)
        self.assertEqual(factory.max_spend["geode"], float('inf'))

    def test_can_build_robot(self):
        factory = OptimizedRobotFactory(self.simple_blueprint)
        self.assertTrue(factory._can_build_robot("ore", (5, 0, 0, 0)))
        self.assertFalse(factory._can_build_robot("obsidian", (3, 10, 0, 0)))
        self.assertTrue(factory._can_build_robot("obsidian", (3, 14, 0, 0)))

    def test_build_robot(self):
        factory = OptimizedRobotFactory(self.simple_blueprint)
        self.assertEqual(factory._build_robot("ore", (5, 2, 1, 0)), (1, 2, 1, 0))
        self.assertEqual(factory._build_robot("obsidian", (10, 20, 5, 3)), (7, 6, 5, 3))

    def test_initial_state(self):
        factory = OptimizedRobotFactory(self.complex_blueprint)
        state = factory._initial_state()
        self.assertEqual(state.resources, tuple(0 for _ in factory.resource_types))
        self.assertEqual(state.robots[0], 1)
        self.assertEqual(state.time, 0)

    def test_get_build_options(self):
        factory = OptimizedRobotFactory(self.simple_blueprint)
        self.assertIn(None, factory._get_build_options((0, 0, 0, 0), (1, 0, 0, 0)))
        self.assertIn("clay", factory._get_build_options((5, 0, 0, 0), (1, 0, 0, 0)))
        self.assertNotIn("obsidian", factory._get_build_options((5, 0, 0, 0), (1, 0, 0, 0)))

    def test_max_final_resource(self):
        factory = OptimizedRobotFactory(self.simple_blueprint)
        self.assertEqual(factory.max_final_resource(0), 0)
        self.assertIsInstance(factory.max_final_resource(5), int)

    def test_performance_short_limit(self):
        import time
        factory = OptimizedRobotFactory(self.simple_blueprint)
        start = time.time()
        result = factory.max_final_resource(8)
        self.assertLess(time.time() - start, 5)
        self.assertIsInstance(result, int)


class TestOptimizedRobotFactoryIntegration(unittest.TestCase):

    def test_integration_with_increasing_time(self):
        blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })
        factory = OptimizedRobotFactory(blueprint)
        short = factory.max_final_resource(5)
        medium = factory.max_final_resource(10)
        long = factory.max_final_resource(15)
        self.assertGreaterEqual(medium, short)
        self.assertGreaterEqual(long, medium)

    def test_blueprint_comparison(self):
        blueprint1 = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })
        blueprint2 = Blueprint({
            "ore": RobotCost({"ore": 2}),
            "clay": RobotCost({"ore": 3}),
            "obsidian": RobotCost({"ore": 3, "clay": 8}),
            "geode": RobotCost({"ore": 3, "obsidian": 12})
        })
        r1 = OptimizedRobotFactory(blueprint1).max_final_resource(10)
        r2 = OptimizedRobotFactory(blueprint2).max_final_resource(10)
        self.assertGreaterEqual(r1, 0)
        self.assertGreaterEqual(r2, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
