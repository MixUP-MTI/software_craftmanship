import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from Minerals import (
    QualityCalculator, 
    ProductCalculator, 
    solve_blueprints,
    solve_blueprints_part1,
    solve_blueprints_part2,
    _write_analysis_file,
    OptimizedRobotFactory
)
import Blueprint

class TestResultCalculators(unittest.TestCase):
    """Tests pour les calculateurs de résultats"""
    
    def test_quality_calculator(self):
        """Test du calculateur de qualité"""
        calculator = QualityCalculator()
        geodes = [10, 5, 8]
        blueprint_ids = [1, 2, 3]
        
        # Qualité = géodes * ID : 10*1 + 5*2 + 8*3 = 10 + 10 + 24 = 44
        result = calculator.calculate(geodes, blueprint_ids)
        self.assertEqual(result, 44)
    
    def test_product_calculator(self):
        """Test du calculateur de produit"""
        calculator = ProductCalculator()
        geodes = [3, 4, 5]
        blueprint_ids = [1, 2, 3]  # Les IDs ne sont pas utilisés pour le produit
        
        # Produit = 3 * 4 * 5 = 60
        result = calculator.calculate(geodes, blueprint_ids)
        self.assertEqual(result, 60)
    
    def test_product_calculator_with_zero(self):
        """Test du calculateur de produit avec un zéro"""
        calculator = ProductCalculator()
        geodes = [3, 0, 5]
        blueprint_ids = [1, 2, 3]
        
        # Produit = 3 * 0 * 5 = 0
        result = calculator.calculate(geodes, blueprint_ids)
        self.assertEqual(result, 0)

class TestAnalysisFile(unittest.TestCase):
    """Tests pour l'écriture du fichier d'analyse"""
    
    def test_write_analysis_file(self):
        """Test de l'écriture du fichier d'analyse"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            blueprint_ids = [1, 2, 3]
            qualities = [10, 30, 20]
            
            _write_analysis_file(tmp_filename, blueprint_ids, qualities)
            
            # Vérifier le contenu du fichier
            with open(tmp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            expected_content = (
                "Blueprint 1: 10\n"
                "Blueprint 2: 30\n"
                "Blueprint 3: 20\n"
                "\n"
                "Best blueprint is the blueprint 2.\n"
            )
            
            self.assertEqual(content, expected_content)
        
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    def test_write_analysis_file_empty(self):
        """Test avec des listes vides"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            _write_analysis_file(tmp_filename, [], [])
            
            with open(tmp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aucun blueprint, donc fichier vide
            self.assertEqual(content, "")
        
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

class TestSolveBlueprintsIntegration(unittest.TestCase):
    """Tests d'intégration pour solve_blueprints"""
    
    def setUp(self):
        """Configuration des mocks pour les tests"""
        # Mock des blueprints
        self.mock_blueprint1 = Mock()
        self.mock_blueprint1.robot_costs = {
            'ore': Mock(resources={'ore': 4}),
            'clay': Mock(resources={'ore': 2}),
            'obsidian': Mock(resources={'ore': 3, 'clay': 14}),
            'geode': Mock(resources={'ore': 2, 'obsidian': 7})
        }
        
        self.mock_blueprint2 = Mock()
        self.mock_blueprint2.robot_costs = {
            'ore': Mock(resources={'ore': 2}),
            'clay': Mock(resources={'ore': 3}),
            'obsidian': Mock(resources={'ore': 3, 'clay': 8}),
            'geode': Mock(resources={'ore': 3, 'obsidian': 12})
        }
    
    @patch('Blueprint.BlueprintLoader')
    @patch('Minerals.OptimizedRobotFactory')
    def test_solve_blueprints_quality_mode(self, mock_factory_class, mock_loader_class):
        """Test de solve_blueprints en mode qualité"""
        # Configuration des mocks
        mock_loader = Mock()
        mock_loader.load.return_value = [self.mock_blueprint1, self.mock_blueprint2]
        mock_loader_class.return_value = mock_loader
        
        # Mock des factories qui retournent des résultats de géodes
        mock_factory1 = Mock()
        mock_factory1.max_geodes.return_value = 9
        
        mock_factory2 = Mock()
        mock_factory2.max_geodes.return_value = 12
        
        mock_factory_class.side_effect = [mock_factory1, mock_factory2]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            # Test avec calculateur de qualité
            calculator = QualityCalculator()
            result = solve_blueprints(
                "test_blueprints.txt", 
                24, 
                calculator, 
                None, 
                tmp_filename
            )
            
            # Vérifier le résultat: 9*1 + 12*2 = 9 + 24 = 33
            self.assertEqual(result, 33)
            
            # Vérifier que le fichier d'analyse a été créé
            self.assertTrue(os.path.exists(tmp_filename))
            
            with open(tmp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn("Blueprint 1: 9", content)
            self.assertIn("Blueprint 2: 24", content)
            self.assertIn("Best blueprint is the blueprint 2", content)
        
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    @patch('Blueprint.BlueprintLoader')
    @patch('Minerals.OptimizedRobotFactory')
    def test_solve_blueprints_product_mode(self, mock_factory_class, mock_loader_class):
        """Test de solve_blueprints en mode produit"""
        # Configuration similaire mais avec calculateur de produit
        mock_loader = Mock()
        mock_loader.load.return_value = [self.mock_blueprint1, self.mock_blueprint2]
        mock_loader_class.return_value = mock_loader
        
        mock_factory1 = Mock()
        mock_factory1.max_geodes.return_value = 3
        
        mock_factory2 = Mock()
        mock_factory2.max_geodes.return_value = 5
        
        mock_factory_class.side_effect = [mock_factory1, mock_factory2]
        
        calculator = ProductCalculator()
        result = solve_blueprints("test_blueprints.txt", 32, calculator, 2)
        
        # Vérifier le résultat: 3 * 5 = 15
        self.assertEqual(result, 15)
    
    @patch('Minerals.solve_blueprints')
    def test_solve_blueprints_part1(self, mock_solve_blueprints):
        """Test de la fonction de commodité part1"""
        mock_solve_blueprints.return_value = 100
        
        result = solve_blueprints_part1("test.txt", 24, "test_analysis.txt")
        
        # Vérifier que solve_blueprints a été appelé avec les bons paramètres
        mock_solve_blueprints.assert_called_once_with(
            "test.txt", 24, unittest.mock.ANY, None, "test_analysis.txt"
        )
        
        # Vérifier que le calculateur passé est bien QualityCalculator
        args, kwargs = mock_solve_blueprints.call_args
        self.assertIsInstance(args[2], QualityCalculator)
        
        self.assertEqual(result, 100)
    
    @patch('Minerals.solve_blueprints')
    def test_solve_blueprints_part2(self, mock_solve_blueprints):
        """Test de la fonction de commodité part2"""
        mock_solve_blueprints.return_value = 500
        
        result = solve_blueprints_part2("test.txt", 32, 3, "test_analysis.txt")
        
        mock_solve_blueprints.assert_called_once_with(
            "test.txt", 32, unittest.mock.ANY, 3, "test_analysis.txt"
        )
        
        # Vérifier que le calculateur passé est bien ProductCalculator
        args, kwargs = mock_solve_blueprints.call_args
        self.assertIsInstance(args[2], ProductCalculator)
        
        self.assertEqual(result, 500)

class TestOptimizedRobotFactory(unittest.TestCase):
    """Tests pour OptimizedRobotFactory (tests plus simples)"""
    
    def setUp(self):
        """Configuration d'un blueprint mock simple"""
        self.mock_blueprint = Mock()
        self.mock_blueprint.robot_costs = {
            'ore': Mock(resources={'ore': 4}),
            'clay': Mock(resources={'ore': 2}),
            'obsidian': Mock(resources={'ore': 3, 'clay': 14}),
            'geode': Mock(resources={'ore': 2, 'obsidian': 7})
        }
    
    def test_factory_initialization(self):
        """Test de l'initialisation de la factory"""
        factory = OptimizedRobotFactory(self.mock_blueprint)
        
        self.assertEqual(factory.blueprint, self.mock_blueprint)
        self.assertEqual(factory.resource_types, ["ore", "clay", "obsidian", "geode"])
        self.assertIsNotNone(factory.max_spend)
    
    def test_calculate_max_spend(self):
        """Test du calcul des dépenses maximales"""
        factory = OptimizedRobotFactory(self.mock_blueprint)
        max_spend = factory._calculate_max_spend()
        
        # Le maximum d'ore dépensé est 4 (robot ore)
        self.assertEqual(max_spend['ore'], 4)
        # Le maximum de clay dépensé est 14 (robot obsidian)
        self.assertEqual(max_spend['clay'], 14)
        # Le maximum d'obsidian dépensé est 7 (robot geode)
        self.assertEqual(max_spend['obsidian'], 7)
        # Les geodes n'ont pas de limite
        self.assertEqual(max_spend['geode'], float('inf'))
    
    def test_can_build_robot(self):
        """Test de la vérification de construction de robot"""
        factory = OptimizedRobotFactory(self.mock_blueprint)
        
        # Ressources suffisantes pour un robot ore (coût: 4 ore)
        resources = (4, 0, 0, 0)  # ore, clay, obsidian, geode
        self.assertTrue(factory._can_build_robot('ore', resources))
        
        # Ressources insuffisantes
        resources = (3, 0, 0, 0)
        self.assertFalse(factory._can_build_robot('ore', resources))

if __name__ == '__main__':
    # Configuration pour afficher plus de détails
    unittest.main(verbosity=2)