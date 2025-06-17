from asyncio import sleep
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from unittest.mock import mock_open, patch
import tempfile
import re
from src.blueprint import (
    RobotCost, Blueprint, BlueprintParser, 
    DefaultBlueprintParser, BlueprintLoader
)


class TestRobotCost(unittest.TestCase):
    """Tests pour la classe RobotCost"""
    
    def test_robot_cost_creation(self):
        """Test la création d'un RobotCost"""
        cost = RobotCost({"ore": 4, "clay": 2})
        self.assertEqual(cost.resources["ore"], 4)
        self.assertEqual(cost.resources["clay"], 2)
        
    def test_robot_cost_empty(self):
        """Test la création d'un RobotCost vide"""
        cost = RobotCost({})
        self.assertEqual(len(cost.resources), 0)
        
    def test_robot_cost_single_resource(self):
        """Test avec une seule ressource"""
        cost = RobotCost({"obsidian": 7})
        self.assertEqual(cost.resources["obsidian"], 7)
        self.assertEqual(len(cost.resources), 1)


class TestBlueprint(unittest.TestCase):
    """Tests pour la classe Blueprint"""
    
    def test_blueprint_creation(self):
        """Test la création d'un Blueprint"""
        robot_costs = {
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2})
        }
        blueprint = Blueprint(robot_costs)
        self.assertEqual(len(blueprint.robot_costs), 2)
        self.assertIn("ore", blueprint.robot_costs)
        self.assertIn("clay", blueprint.robot_costs)
        
    def test_blueprint_empty(self):
        """Test la création d'un Blueprint vide"""
        blueprint = Blueprint({})
        self.assertEqual(len(blueprint.robot_costs), 0)


class TestDefaultBlueprintParser(unittest.TestCase):
    """Tests pour DefaultBlueprintParser"""
    
    def setUp(self):
        self.parser = DefaultBlueprintParser()
        
    def test_parse_blueprint_1_complete(self):
        """Test parsing du Blueprint 1 complet"""
        text = "Blueprint 1: Each ore robot costs 4 ore. Each clay robot costs 2 ore. Each obsidian robot costs 3 ore and 14 clay. Each geode robot costs 2 ore and 7 obsidian. Each diamond robot costs 1 geode, 8 clay and 7 obsidian."
        
        blueprint = self.parser.parse(text)
        
        # Vérifier ore robot
        self.assertIn("ore", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["ore"].resources["ore"], 4)
        
        # Vérifier clay robot
        self.assertIn("clay", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["clay"].resources["ore"], 2)
        
        # Vérifier obsidian robot
        self.assertIn("obsidian", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["obsidian"].resources["ore"], 3)
        self.assertEqual(blueprint.robot_costs["obsidian"].resources["clay"], 14)
        
        # Vérifier geode robot
        self.assertIn("geode", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["geode"].resources["ore"], 2)
        self.assertEqual(blueprint.robot_costs["geode"].resources["obsidian"], 7)
        
        # Vérifier diamond robot
        self.assertIn("diamond", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["diamond"].resources["geode"], 1)
        self.assertEqual(blueprint.robot_costs["diamond"].resources["clay"], 8)
        self.assertEqual(blueprint.robot_costs["diamond"].resources["obsidian"], 7)
        
    def test_parse_blueprint_2_complete(self):
        """Test parsing du Blueprint 2 complet"""
        text = "Blueprint 2: Each ore robot costs 2 ore. Each clay robot costs 3 ore. Each obsidian robot costs 3 ore and 8 clay. Each geode robot costs 3 ore and 12 obsidian. Each diamond robot costs 3 geode, 2 clay and 3 obsidian."
        
        blueprint = self.parser.parse(text)
        
        # Vérifier ore robot
        self.assertEqual(blueprint.robot_costs["ore"].resources["ore"], 2)
        
        # Vérifier clay robot
        self.assertEqual(blueprint.robot_costs["clay"].resources["ore"], 3)
        
        # Vérifier obsidian robot
        self.assertEqual(blueprint.robot_costs["obsidian"].resources["ore"], 3)
        self.assertEqual(blueprint.robot_costs["obsidian"].resources["clay"], 8)
        
        # Vérifier geode robot
        self.assertEqual(blueprint.robot_costs["geode"].resources["ore"], 3)
        self.assertEqual(blueprint.robot_costs["geode"].resources["obsidian"], 12)
        
        # Vérifier diamond robot
        self.assertEqual(blueprint.robot_costs["diamond"].resources["geode"], 3)
        self.assertEqual(blueprint.robot_costs["diamond"].resources["clay"], 2)
        self.assertEqual(blueprint.robot_costs["diamond"].resources["obsidian"], 3)
        
    def test_parse_partial_blueprint(self):
        """Test parsing d'un blueprint partiel (sans diamond)"""
        text = "Blueprint 3: Each ore robot costs 1 ore. Each clay robot costs 1 ore. Each obsidian robot costs 2 ore and 3 clay. Each geode robot costs 1 ore and 2 obsidian."
        
        blueprint = self.parser.parse(text)
        
        self.assertEqual(len(blueprint.robot_costs), 4)  # ore, clay, obsidian, geode
        self.assertNotIn("diamond", blueprint.robot_costs)
        
    def test_parse_ore_robot_only(self):
        """Test parsing avec seulement ore robot"""
        text = "Blueprint 4: Each ore robot costs 5 ore."
        
        blueprint = self.parser.parse(text)
        
        self.assertEqual(len(blueprint.robot_costs), 1)
        self.assertIn("ore", blueprint.robot_costs)
        self.assertEqual(blueprint.robot_costs["ore"].resources["ore"], 5)
        
    def test_parse_invalid_blueprint_empty(self):
        """Test parsing d'un blueprint vide"""
        text = ""
        
        with self.assertRaises(ValueError) as context:
            self.parser.parse(text)
        self.assertIn("Invalid blueprint format", str(context.exception))
        
    def test_parse_invalid_blueprint_no_match(self):
        """Test parsing d'un blueprint sans pattern valide"""
        text = "This is not a valid blueprint format"
        
        with self.assertRaises(ValueError) as context:
            self.parser.parse(text)
        self.assertIn("Invalid blueprint format", str(context.exception))
        
    def test_parse_with_different_number_format(self):
        """Test parsing avec des nombres à plusieurs chiffres"""
        text = "Blueprint 5: Each ore robot costs 10 ore. Each clay robot costs 25 ore. Each obsidian robot costs 100 ore and 150 clay."
        
        blueprint = self.parser.parse(text)
        
        self.assertEqual(blueprint.robot_costs["ore"].resources["ore"], 10)
        self.assertEqual(blueprint.robot_costs["clay"].resources["ore"], 25)
        self.assertEqual(blueprint.robot_costs["obsidian"].resources["ore"], 100)
        self.assertEqual(blueprint.robot_costs["obsidian"].resources["clay"], 150)
        
    def test_regex_patterns(self):
        """Test des patterns regex individuellement"""
        patterns = {
            "ore": r"ore robot costs (\d+) ore",
            "clay": r"clay robot costs (\d+) ore",
            "obsidian": r"obsidian robot costs (\d+) ore and (\d+) clay",
            "geode": r"geode robot costs (\d+) ore and (\d+) obsidian",
            "diamond": r"diamond robot costs (\d+) geode, (\d+) clay and (\d+) obsidian"
        }
        
        test_strings = {
            "ore": "Each ore robot costs 4 ore.",
            "clay": "Each clay robot costs 2 ore.",
            "obsidian": "Each obsidian robot costs 3 ore and 14 clay.",
            "geode": "Each geode robot costs 2 ore and 7 obsidian.",
            "diamond": "Each diamond robot costs 1 geode, 8 clay and 7 obsidian."
        }
        
        for robot_type, pattern in patterns.items():
            with self.subTest(robot_type=robot_type):
                match = re.search(pattern, test_strings[robot_type])
                self.assertIsNotNone(match, f"Pattern for {robot_type} should match")


class TestBlueprintLoader(unittest.TestCase):
    """Tests pour BlueprintLoader"""
    
    def setUp(self):
        self.parser = DefaultBlueprintParser()
        self.loader = BlueprintLoader(self.parser)
        
    def test_load_from_string_data(self):
        """Test loading avec des données en string"""
        test_data = """Blueprint 1: Each ore robot costs 4 ore. Each clay robot costs 2 ore. Each obsidian robot costs 3 ore and 14 clay. Each geode robot costs 2 ore and 7 obsidian.
Blueprint 2: Each ore robot costs 2 ore. Each clay robot costs 3 ore. Each obsidian robot costs 3 ore and 8 clay. Each geode robot costs 3 ore and 12 obsidian."""
        
        with patch("builtins.open", mock_open(read_data=test_data)):
            blueprints = self.loader.load("fake_file.txt")
            
        self.assertEqual(len(blueprints), 2)
        
        # Vérifier blueprint 1
        bp1 = blueprints[0]
        self.assertEqual(bp1.robot_costs["ore"].resources["ore"], 4)
        self.assertEqual(bp1.robot_costs["clay"].resources["ore"], 2)
        
        # Vérifier blueprint 2
        bp2 = blueprints[1]
        self.assertEqual(bp2.robot_costs["ore"].resources["ore"], 2)
        self.assertEqual(bp2.robot_costs["clay"].resources["ore"], 3)
        
    def test_load_with_empty_lines(self):
        """Test loading avec des lignes vides"""
        test_data = """Blueprint 1: Each ore robot costs 4 ore. Each clay robot costs 2 ore.

Blueprint 2: Each ore robot costs 2 ore. Each clay robot costs 3 ore.

"""
        
        with patch("builtins.open", mock_open(read_data=test_data)):
            blueprints = self.loader.load("fake_file.txt")
            
        self.assertEqual(len(blueprints), 2)
        
    def test_load_empty_file(self):
        """Test loading d'un fichier vide"""
        test_data = ""
        
        with patch("builtins.open", mock_open(read_data=test_data)):
            blueprints = self.loader.load("fake_file.txt")
            
        self.assertEqual(len(blueprints), 0)
        
    def test_load_file_not_found(self):
        """Test loading d'un fichier inexistant"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load("nonexistent_file.txt")
            
    def test_load_with_whitespace_lines(self):
        """Test loading avec des lignes contenant seulement des espaces"""
        test_data = """Blueprint 1: Each ore robot costs 4 ore.
   
	
Blueprint 2: Each ore robot costs 2 ore."""
        
        with patch("builtins.open", mock_open(read_data=test_data)):
            blueprints = self.loader.load("fake_file.txt")
            
        self.assertEqual(len(blueprints), 2)


class TestIntegration(unittest.TestCase):
    """Tests d'intégration"""
    
    def test_full_workflow(self):
        """Test du workflow complet"""
        # Créer un fichier temporaire avec des données de test
        test_data = """Blueprint 1: Each ore robot costs 4 ore. Each clay robot costs 2 ore. Each obsidian robot costs 3 ore and 14 clay. Each geode robot costs 2 ore and 7 obsidian. Each diamond robot costs 1 geode, 8 clay and 7 obsidian.
Blueprint 2: Each ore robot costs 2 ore. Each clay robot costs 3 ore. Each obsidian robot costs 3 ore and 8 clay. Each geode robot costs 3 ore and 12 obsidian. Each diamond robot costs 3 geode, 2 clay and 3 obsidian."""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_data)
            temp_filename = f.name
            
        try:
            # Charger les blueprints
            loader = BlueprintLoader(DefaultBlueprintParser())
            blueprints = loader.load(temp_filename)
            
            # Vérifications
            self.assertEqual(len(blueprints), 2)
            
            # Vérifier que tous les robots sont présents dans chaque blueprint
            for i, bp in enumerate(blueprints, 1):
                with self.subTest(blueprint=i):
                    expected_robots = ["ore", "clay", "obsidian", "geode", "diamond"]
                    for robot in expected_robots:
                        self.assertIn(robot, bp.robot_costs, f"Robot {robot} missing in blueprint {i}")
                        
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(temp_filename)
            
    def test_blueprint_data_consistency(self):
        """Test la cohérence des données parsées"""
        text = "Blueprint 1: Each ore robot costs 4 ore. Each clay robot costs 2 ore. Each obsidian robot costs 3 ore and 14 clay. Each geode robot costs 2 ore and 7 obsidian. Each diamond robot costs 1 geode, 8 clay and 7 obsidian."
        
        parser = DefaultBlueprintParser()
        blueprint = parser.parse(text)
        
        # Vérifier que chaque robot a au moins une ressource
        for robot_type, cost in blueprint.robot_costs.items():
            with self.subTest(robot_type=robot_type):
                self.assertGreater(len(cost.resources), 0, f"{robot_type} robot should have at least one resource cost")
                
                # Vérifier que toutes les quantités sont positives
                for resource, quantity in cost.resources.items():
                    self.assertGreater(quantity, 0, f"{robot_type} robot {resource} cost should be positive")


if __name__ == '__main__':
    # Configuration pour des tests plus verbeux
    unittest.main(verbosity=2)