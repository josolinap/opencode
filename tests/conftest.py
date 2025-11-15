"""
Pytest configuration and shared fixtures for OpenCode testing
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
import os
import sys

# Add neo-clone to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "neo-clone"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp(prefix="opencode_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def isolated_memory_dir(temp_dir):
    """Create isolated memory directories for testing."""
    memory_dir = Path(temp_dir) / "memory"
    vector_dir = Path(temp_dir) / "vector_memory"

    memory_dir.mkdir(parents=True, exist_ok=True)
    vector_dir.mkdir(parents=True, exist_ok=True)

    return {
        "memory_dir": str(memory_dir),
        "vector_dir": str(vector_dir)
    }


@pytest.fixture(scope="function")
async def mock_memory(isolated_memory_dir):
    """Create a mock unified memory instance for testing."""
    try:
        from unified_memory import UnifiedMemoryManager, UnifiedMemoryConfig

        config = UnifiedMemoryConfig(
            persistent_dir=isolated_memory_dir["memory_dir"],
            vector_dir=isolated_memory_dir["vector_dir"],
            auto_save=False,  # Disable auto-save for tests
            cache_enabled=True
        )

        memory = UnifiedMemoryManager(config)
        yield memory

        # Cleanup
        await memory._persistent_memory._save_conversations()
        await memory._vector_memory._save_index()

    except ImportError:
        pytest.skip("Unified memory not available")


@pytest.fixture(scope="function")
async def mock_skills_manager():
    """Create a mock skills manager for testing."""
    try:
        from skills import SkillsManager
        manager = SkillsManager()
        yield manager
    except ImportError:
        pytest.skip("Skills system not available")


@pytest.fixture(scope="function")
async def mock_brain(isolated_memory_dir):
    """Create a mock brain instance for testing."""
    try:
        from base_brain import BaseBrain, ProcessingMode

        brain = BaseBrain(
            processing_mode=ProcessingMode.STANDARD,
            enable_learning=False,  # Disable learning for tests
            enable_optimization=False  # Disable optimization for tests
        )
        yield brain
    except ImportError:
        pytest.skip("Brain system not available")


@pytest.fixture(scope="function")
def mock_model_orchestrator():
    """Create a mock model orchestrator for testing."""
    try:
        from ai_model_integration import AIModelOrchestrator
        orchestrator = AIModelOrchestrator()
        return orchestrator
    except ImportError:
        pytest.skip("Model integration not available")


@pytest.fixture(scope="function")
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "user_input": "Hello, how are you?",
        "assistant_response": "I'm doing well, thank you for asking!",
        "intent": "greeting",
        "skill_used": "conversation",
        "metadata": {"confidence": 0.95}
    }


@pytest.fixture(scope="function")
def sample_memory_entry():
    """Sample memory entry for testing."""
    return {
        "content": "Test memory content for unit testing",
        "memory_type": "EPISODIC",
        "importance": 0.8,
        "tags": ["test", "unit"],
        "metadata": {"test_id": "sample"}
    }


@pytest.fixture(scope="function")
def sample_skill_context():
    """Sample skill context for testing."""
    try:
        from data_models import SkillContext, MessageRole
        return SkillContext(
            user_input="Generate a simple Python function",
            intent_type="CODE_GENERATION",
            conversation_history=[],
            metadata={"complexity": "simple"}
        )
    except ImportError:
        return {
            "user_input": "Generate a simple Python function",
            "intent_type": "CODE_GENERATION",
            "conversation_history": [],
            "metadata": {"complexity": "simple"}
        }


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "system: System/end-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "network: Tests requiring network access")
    config.addinivalue_line("markers", "ai: Tests involving AI models")
    config.addinivalue_line("markers", "memory: Tests involving memory systems")
    config.addinivalue_line("markers", "skills: Tests involving skills system")
    config.addinivalue_line("markers", "brain: Tests involving brain system")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path."""
    for item in items:
        # Add markers based on test path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "system" in str(item.fspath):
            item.add_marker(pytest.mark.system)

        # Add markers based on test content
        if "memory" in item.name.lower():
            item.add_marker(pytest.mark.memory)
        elif "skill" in item.name.lower():
            item.add_marker(pytest.mark.skills)
        elif "brain" in item.name.lower():
            item.add_marker(pytest.mark.brain)
        elif "model" in item.name.lower() or "ai" in item.name.lower():
            item.add_marker(pytest.mark.ai)