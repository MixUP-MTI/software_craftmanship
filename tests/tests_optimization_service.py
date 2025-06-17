import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from unittest.mock import patch
from collections import namedtuple
from src.blueprint import Blueprint, RobotCost
from src.optimization_service import OptimizedRobotFactory


class TestOptimizedRobotFactory(unittest.TestCase):
    """Tests pour OptimizedRobotFactory"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Blueprint simple pour les tests de base
        self.simple_blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })
        
        # Blueprint complexe avec diamond (comme dans vos exemples)
        self.complex_blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7}),
            "diamond": RobotCost({"geode": 1, "clay": 8, "obsidian": 7})
        })
        
        # Blueprint du second exemple
        self.blueprint_2 = Blueprint({
            "ore": RobotCost({"ore": 2}),
            "clay": RobotCost({"ore": 3}),
            "obsidian": RobotCost({"ore": 3, "clay": 8}),
            "geode": RobotCost({"ore": 3, "obsidian": 12}),
            "diamond": RobotCost({"geode": 3, "clay": 2, "obsidian": 3})
        })
        
    def test_init_simple_blueprint(self):
        """Test l'initialisation avec un blueprint simple"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        self.assertEqual(factory.blueprint, self.simple_blueprint)
        self.assertEqual(factory.resource_types, ["ore", "clay", "obsidian", "geode"])
        self.assertEqual(factory.final_resource, "geode")  # Dernier par défaut
        self.assertEqual(factory.final_index, 3)
        
    def test_init_with_custom_final_resource(self):
        """Test l'initialisation avec une ressource finale personnalisée"""
        factory = OptimizedRobotFactory(self.complex_blueprint, final_resource="diamond")
        
        self.assertEqual(factory.final_resource, "diamond")
        self.assertEqual(factory.final_index, 4)
        
    def test_init_with_obsidian_final_resource(self):
        """Test l'initialisation avec obsidian comme ressource finale"""
        factory = OptimizedRobotFactory(self.simple_blueprint, final_resource="obsidian")
        
        self.assertEqual(factory.final_resource, "obsidian")
        self.assertEqual(factory.final_index, 2)
        
    def test_calculate_max_spend(self):
        """Test le calcul des dépenses maximales"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        max_spend = factory.max_spend
        
        # Vérifications des valeurs calculées
        self.assertEqual(max_spend["ore"], 4)  # Max entre 4, 2, 3, 2
        self.assertEqual(max_spend["clay"], 14)  # Max pour clay
        self.assertEqual(max_spend["obsidian"], 7)  # Max pour obsidian
        self.assertEqual(max_spend["geode"], float('inf'))  # Ressource finale
        
    def test_calculate_max_spend_complex(self):
        """Test le calcul des dépenses maximales pour blueprint complexe"""
        factory = OptimizedRobotFactory(self.complex_blueprint, final_resource="diamond")
        max_spend = factory.max_spend
        
        self.assertEqual(max_spend["ore"], 4)  # Max entre tous les coûts ore
        self.assertEqual(max_spend["clay"], 14)  # Max entre 14 et 8
        self.assertEqual(max_spend["obsidian"], 7)  # Max entre 7 et 7
        self.assertEqual(max_spend["geode"], 1)  # Utilisé pour diamond
        self.assertEqual(max_spend["diamond"], float('inf'))  # Ressource finale
        
    def test_can_build_robot_sufficient_resources(self):
        """Test si on peut construire un robot avec suffisamment de ressources"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # Ressources suffisantes pour ore robot (coût: 4 ore)
        resources = (5, 0, 0, 0)  # ore, clay, obsidian, geode
        self.assertTrue(factory._can_build_robot("ore", resources))
        
        # Ressources suffisantes pour clay robot (coût: 2 ore)
        self.assertTrue(factory._can_build_robot("clay", resources))
        
        # Ressources insuffisantes pour obsidian robot (coût: 3 ore, 14 clay)
        self.assertFalse(factory._can_build_robot("obsidian", resources))
        
    def test_can_build_robot_insufficient_resources(self):
        """Test si on ne peut pas construire un robot sans ressources suffisantes"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # Ressources insuffisantes
        resources = (1, 0, 0, 0)  # ore, clay, obsidian, geode
        self.assertFalse(factory._can_build_robot("ore", resources))
        self.assertFalse(factory._can_build_robot("clay", resources))
        
    def test_can_build_robot_exact_resources(self):
        """Test construction avec exactement les ressources nécessaires"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # Exactement les ressources pour obsidian robot
        resources = (3, 14, 0, 0)  # ore, clay, obsidian, geode
        self.assertTrue(factory._can_build_robot("obsidian", resources))
        
    def test_build_robot_ore(self):
        """Test la construction d'un robot ore"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        resources = (5, 2, 1, 0)
        new_resources = factory._build_robot("ore", resources)
        
        # Devrait soustraire 4 ore
        expected = (1, 2, 1, 0)
        self.assertEqual(new_resources, expected)
        
    def test_build_robot_obsidian(self):
        """Test la construction d'un robot obsidian"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        resources = (10, 20, 5, 3)
        new_resources = factory._build_robot("obsidian", resources)
        
        # Devrait soustraire 3 ore et 14 clay
        expected = (7, 6, 5, 3)
        self.assertEqual(new_resources, expected)
        
    def test_build_robot_diamond(self):
        """Test la construction d'un robot diamond"""
        factory = OptimizedRobotFactory(self.complex_blueprint, final_resource="diamond")
        
        resources = (10, 20, 15, 5, 0)  # ore, clay, obsidian, geode, diamond
        new_resources = factory._build_robot("diamond", resources)
        
        # Devrait soustraire 1 geode, 8 clay, 7 obsidian
        expected = (10, 12, 8, 4, 0)
        self.assertEqual(new_resources, expected)
        
    def test_initial_state(self):
        """Test l'état initial"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        state = factory._initial_state()
        
        self.assertEqual(state.time, 0)
        self.assertEqual(state.resources, (0, 0, 0, 0))
        self.assertEqual(state.robots, (1, 0, 0, 0))  # 1 ore robot au début
        
    def test_initial_state_complex(self):
        """Test l'état initial avec blueprint complexe"""
        factory = OptimizedRobotFactory(self.complex_blueprint)
        state = factory._initial_state()
        
        self.assertEqual(state.time, 0)
        self.assertEqual(state.resources, (0, 0, 0, 0, 0))
        self.assertEqual(state.robots, (1, 0, 0, 0, 0))  # 1 ore robot au début
        
    def test_get_build_options_initial(self):
        """Test les options de construction à l'état initial"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # État initial: pas de ressources, 1 ore robot
        resources = (0, 0, 0, 0)
        robots = (1, 0, 0, 0)
        
        options = factory._get_build_options(resources, robots)
        
        # Ne devrait pas pouvoir construire de robot (pas de ressources)
        # Mais l'option "None" (ne rien construire) devrait être présente
        self.assertIn(None, options)
        
    def test_get_build_options_with_resources(self):
        """Test les options de construction avec des ressources"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # Ressources pour construire ore et clay robots
        resources = (5, 0, 0, 0)
        robots = (1, 0, 0, 0)
        
        options = factory._get_build_options(resources, robots)
        
        self.assertIn("ore", options)
        self.assertIn("clay", options)
        self.assertNotIn("obsidian", options)  # Pas assez de clay
        self.assertNotIn("geode", options)  # Pas d'obsidian
        self.assertIn(None, options)
        
    def test_get_build_options_max_robots_limit(self):
        """Test la limite du nombre maximum de robots"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # Beaucoup de ressources mais déjà max_spend robots ore
        resources = (100, 100, 100, 100)
        robots = (4, 0, 0, 0)  # max_spend["ore"] = 4
        
        options = factory._get_build_options(resources, robots)
        
        # Ne devrait pas pouvoir construire plus de robots ore
        self.assertNotIn("ore", options)
        self.assertIn("clay", options)
        self.assertIn("obsidian", options)
        self.assertIn("geode", options)
        
    def test_max_final_resource_simple_case(self):
        """Test du calcul de ressource finale pour cas simple"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        # Test avec un temps très court
        result = factory.max_final_resource(time_limit=1)
        
        # En 1 minute, on ne peut que collecter avec le robot ore initial
        self.assertEqual(result, 0)  # Pas de geode produit en 1 minute
        
    def test_max_final_resource_zero_time(self):
        """Test avec temps limite zéro"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        result = factory.max_final_resource(time_limit=0)
        self.assertEqual(result, 0)
        
    def test_max_final_resource_different_blueprints(self):
        """Test avec différents blueprints"""
        factory1 = OptimizedRobotFactory(self.simple_blueprint)
        factory2 = OptimizedRobotFactory(self.blueprint_2)
        
        # Les résultats devraient être différents pour des blueprints différents
        result1 = factory1.max_final_resource(time_limit=5)
        result2 = factory2.max_final_resource(time_limit=5)
        
        # Pas de assertion spécifique car cela dépend de l'algorithme,
        # mais on vérifie que les calculs se font sans erreur
        self.assertIsInstance(result1, int)
        self.assertIsInstance(result2, int)
        self.assertGreaterEqual(result1, 0)
        self.assertGreaterEqual(result2, 0)
        
    def test_max_final_resource_with_diamond(self):
        """Test du calcul avec diamond comme ressource finale"""
        factory = OptimizedRobotFactory(self.complex_blueprint, final_resource="diamond")
        
        result = factory.max_final_resource(time_limit=3)
        
        # Avec un temps court, difficile de produire des diamonds
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)
        
    def test_state_namedtuple(self):
        """Test que State est bien un namedtuple avec les bons champs"""
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        state = factory.State(10, (1, 2, 3, 4), (1, 1, 1, 1))
        
        self.assertEqual(state.time, 10)
        self.assertEqual(state.resources, (1, 2, 3, 4))
        self.assertEqual(state.robots, (1, 1, 1, 1))
        
    def test_performance_reasonable_time(self):
        """Test que l'algorithme termine dans un temps raisonnable"""
        import time
        
        factory = OptimizedRobotFactory(self.simple_blueprint)
        
        start_time = time.time()
        result = factory.max_final_resource(time_limit=8)  # Temps court pour test rapide
        end_time = time.time()
        
        # Devrait terminer en moins de 5 secondes (ajustez selon vos besoins)
        self.assertLess(end_time - start_time, 5.0)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)
        
    def test_resource_types_order(self):
        """Test que l'ordre des types de ressources est préservé"""
        factory = OptimizedRobotFactory(self.complex_blueprint)
        
        expected_order = ["ore", "clay", "obsidian", "geode", "diamond"]
        self.assertEqual(factory.resource_types, expected_order)
        
    def test_edge_case_empty_build_options(self):
        """Test cas limite avec options de construction limitées"""
        # Blueprint très cher pour tester les cas limites
        expensive_blueprint = Blueprint({
            "ore": RobotCost({"ore": 100}),
            "geode": RobotCost({"ore": 200})
        })
        
        factory = OptimizedRobotFactory(expensive_blueprint)
        
        # Avec peu de ressources, peu d'options disponibles
        resources = (50, 0)
        robots = (1, 0)
        
        options = factory._get_build_options(resources, robots)
        
        # Devrait au moins avoir l'option None
        self.assertIn(None, options)
        self.assertNotIn("ore", options)  # Trop cher
        self.assertNotIn("geode", options)  # Trop cher


class TestOptimizedRobotFactoryIntegration(unittest.TestCase):
    """Tests d'intégration pour OptimizedRobotFactory"""
    
    def test_integration_blueprint_1_sample(self):
        """Test d'intégration avec le Blueprint 1 de l'exemple"""
        blueprint = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })
        
        factory = OptimizedRobotFactory(blueprint)
        
        # Test avec différentes limites de temps
        result_short = factory.max_final_resource(time_limit=5)
        result_medium = factory.max_final_resource(time_limit=10)
        result_long = factory.max_final_resource(time_limit=15)
        
        # Plus de temps devrait donner un meilleur ou égal résultat
        self.assertGreaterEqual(result_medium, result_short)
        self.assertGreaterEqual(result_long, result_medium)
        
    def test_integration_comparing_blueprints(self):
        """Test d'intégration comparant différents blueprints"""
        blueprint_1 = Blueprint({
            "ore": RobotCost({"ore": 4}),
            "clay": RobotCost({"ore": 2}),
            "obsidian": RobotCost({"ore": 3, "clay": 14}),
            "geode": RobotCost({"ore": 2, "obsidian": 7})
        })
        
        blueprint_2 = Blueprint({
            "ore": RobotCost({"ore": 2}),
            "clay": RobotCost({"ore": 3}),
            "obsidian": RobotCost({"ore": 3, "clay": 8}),
            "geode": RobotCost({"ore": 3, "obsidian": 12})
        })
        
        factory_1 = OptimizedRobotFactory(blueprint_1)
        factory_2 = OptimizedRobotFactory(blueprint_2)
        
        result_1 = factory_1.max_final_resource(time_limit=10)
        result_2 = factory_2.max_final_resource(time_limit=10)
        
        # Les deux devraient produire des résultats valides
        self.assertIsInstance(result_1, int)
        self.assertIsInstance(result_2, int)
        self.assertGreaterEqual(result_1, 0)
        self.assertGreaterEqual(result_2, 0)


if __name__ == '__main__':
    # Lancer les tests avec plus de verbosité
    unittest.main(verbosity=2)