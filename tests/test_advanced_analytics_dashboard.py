"""
Tests for advanced_analytics_dashboard skill
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_framework import SkillTestCase


class TestAdvancedAnalyticsDashboardSkill(SkillTestCase):
    """Test cases for advanced_analytics_dashboard skill"""

    def setUp(self):
        super().setUp()
        self.skill = self.load_skill("advanced_analytics_dashboard")

    def test_basic_execution(self):
        """Test basic skill execution"""
        if self.skill:
            response = self.skill.execute({})
            self.assertSkillResponse(response)

    def test_parameter_validation(self):
        """Test parameter validation"""
        if self.skill:
            response = self.skill.execute({"invalid_param": "test"})
            # Should handle gracefully
            self.assertIsInstance(response, dict)


if __name__ == '__main__':
    unittest.main()
