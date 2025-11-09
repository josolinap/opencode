"""
demo_minimax_agent.py - Demo script showing MiniMax Agent integration with Neo-Clone

Demonstrates:
1. Using MiniMax Agent for intent analysis
2. Dynamic skill generation
3. Integration with Neo-Clone's brain system
4. Reasoning trace generation
5. Skill creation and registration
"""

import sys
from pathlib import Path

# Add neo-clone to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, load_config
from skills import SkillRegistry
from brain import Brain, LLMClient
from skills.minimax_agent import MiniMaxAgent
import json
import time


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


def demo_intent_analysis():
    """Demonstrate MiniMax Agent's intent analysis capabilities"""
    print_section("DEMO 1: INTENT ANALYSIS")
    
    # Initialize MiniMax Agent
    agent = MiniMaxAgent()
    
    # Test various user inputs
    test_inputs = [
        "I need to create a Python script to process CSV files and generate charts",
        "Find the latest information about machine learning frameworks",
        "Build a web API for user authentication",
        "Analyze this dataset and create visualizations",
        "Make a tool to organize my files automatically"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print_subsection(f"Analysis {i}: {user_input[:50]}...")
        
        result = agent.analyze_user_input(user_input)
        
        print(f"Primary Intent: {result['primary_intent']} (confidence: {result['confidence']:.2f})")
        print(f"Detected Actions: {result['detected_actions']}")
        print(f"Technologies: {result['detected_technologies']}")
        print(f"Suggested Skills: {result['suggested_skills']}")
        print(f"Complexity Score: {result['complexity_score']}")
        
        # Show reasoning trace
        if result['reasoning_trace']['step_count'] > 0:
            print(f"Reasoning Steps: {result['reasoning_trace']['step_count']}")
            for step in result['reasoning_trace']['steps']:
                print(f"  - {step['step']}: {step['details']}")
        
        print()


def demo_skill_generation():
    """Demonstrate dynamic skill generation"""
    print_section("DEMO 2: DYNAMIC SKILL GENERATION")
    
    agent = MiniMaxAgent()
    
    # Define skill requirements
    skill_requirements = [
        {
            "name": "csv_processor",
            "description": "Process CSV files and generate summary statistics",
            "context": ["user wants data analysis", "needs automation"]
        },
        {
            "name": "web_scraper",
            "description": "Scrape data from websites using BeautifulSoup",
            "context": ["web scraping task", "data extraction"]
        },
        {
            "name": "file_organizer",
            "description": "Organize files in directories by type and date",
            "context": ["file management", "automation needed"]
        }
    ]
    
    for req in skill_requirements:
        print_subsection(f"Generating: {req['name']}")
        
        result = agent.generate_dynamic_skill(
            skill_name=req['name'],
            description=req['description'],
            context=req['context']
        )
        
        print(f"Generated Skill: {result['skill_name']}")
        print(f"Class Name: {result['class_name']}")
        print(f"Lines of Code: {len(result['skill_code'].split(chr(10)))}")
        print(f"Parameters: {list(result['parameters'].keys())}")
        
        # Show code preview
        code_lines = result['skill_code'].split('\n')[:15]  # First 15 lines
        print("Code Preview:")
        for line in code_lines:
            print(f"  {line}")
        if len(result['skill_code'].split('\n')) > 15:
            print("  ...")
        
        print()


def demo_integration_with_brain():
    """Demonstrate integration with Neo-Clone's brain system"""
    print_section("DEMO 3: INTEGRATION WITH NEO-CLONE BRAIN")
    
    # Load configuration
    try:
        cfg = load_config()
    except:
        print("Creating default config for demo...")
        cfg = Config()
    
    # Initialize skill registry
    skills = SkillRegistry()
    
    # Manually register MiniMax Agent
    minimax_agent = MiniMaxAgent()
    skills.register(minimax_agent)
    
    # Initialize brain
    brain = Brain(cfg, skills)
    
    # Test queries
    test_queries = [
        "I need to create a custom skill for data analysis",
        "Help me analyze this Python code and suggest improvements",
        "Generate a tool to process JSON files",
        "What's the best approach for building a web scraper?"
    ]
    
    for query in test_queries:
        print_subsection(f"Query: {query}")
        
        # Use brain to process the query
        response = brain.send_message(query)
        print(f"Brain Response: {response[:200]}..." if len(response) > 200 else response)
        
        # If it triggered the MiniMax agent, show details
        if "minimax_agent" in response.lower() or "skill generation" in response.lower():
            print("→ MiniMax Agent was triggered for enhanced reasoning!")
        
        print()


def demo_skill_creation_and_usage():
    """Demonstrate creating and using a generated skill"""
    print_section("DEMO 4: SKILL CREATION AND USAGE")
    
    agent = MiniMaxAgent()
    
    # Generate a skill
    print("Generating a sample CSV processor skill...")
    result = agent.generate_dynamic_skill(
        skill_name="csv_analyzer",
        description="Analyze CSV files and provide statistical summaries",
        parameters={
            "file_path": "path to CSV file",
            "analysis_type": "type of analysis to perform"
        }
    )
    
    # Save the skill
    print("Saving generated skill to file...")
    save_result = agent.save_generated_skill(result['skill_code'], "skills/demo_csv_analyzer.py")
    print(f"Save result: {save_result}")
    
    if save_result['status'] == 'success':
        # Try to import and use the generated skill
        print_subsection("Testing Generated Skill")
        
        try:
            # Import the generated skill
            import importlib.util
            spec = importlib.util.spec_from_file_location("demo_csv_analyzer", "skills/demo_csv_analyzer.py")
            demo_skill = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(demo_skill)
            
            # Create instance and test
            skill_instance = demo_skill.CsvAnalyzer()
            test_params = {
                "file_path": "sample.csv",
                "analysis_type": "summary"
            }
            
            print(f"Skill name: {skill_instance.name}")
            print(f"Skill description: {skill_instance.description}")
            
            # Execute with test parameters
            execution_result = skill_instance.execute(test_params)
            print(f"Execution result: {execution_result}")
            
        except Exception as e:
            print(f"Error testing generated skill: {e}")
    
    print()


def demo_reasoning_traces():
    """Demonstrate reasoning trace generation and logging"""
    print_section("DEMO 5: REASONING TRACES")
    
    agent = MiniMaxAgent()
    
    # Complex query requiring deep reasoning
    complex_query = """
    I need to build a comprehensive data pipeline that can:
    1. Ingest CSV files from multiple sources
    2. Clean and validate the data
    3. Transform it into a unified format
    4. Generate reports with visualizations
    5. Export to different formats (JSON, Excel, database)
    Please suggest the best approach and generate appropriate tools.
    """
    
    print_subsection("Complex Query Analysis")
    print(f"Query: {complex_query[:100]}...")
    
    result = agent.analyze_user_input(complex_query)
    
    # Show detailed reasoning trace
    trace = result['reasoning_trace']
    print(f"\nReasoning Trace (Total Time: {trace['total_time']:.3f}s):")
    for i, step in enumerate(trace['steps'], 1):
        print(f"{i:2d}. [{step['timestamp']:.3f}s] {step['step']}")
        print(f"    {step['details']}")
        print(f"    Confidence: {step['confidence']:.2f}")
    
    # Show intent analysis details
    print(f"\nIntent Analysis:")
    print(f"  Primary: {result['primary_intent']} (confidence: {result['confidence']:.2f})")
    print(f"  All scores: {result['intent_scores']}")
    print(f"  Complexity: {result['complexity_score']}")
    
    print()


def demo_performance_comparison():
    """Compare performance with and without MiniMax Agent"""
    print_section("DEMO 6: PERFORMANCE COMPARISON")
    
    agent = MiniMaxAgent()
    
    # Test with simple query
    simple_query = "create a simple script"
    start_time = time.time()
    result1 = agent.analyze_user_input(simple_query)
    simple_time = time.time() - start_time
    
    # Test with complex query
    complex_query = "build a comprehensive machine learning pipeline with data preprocessing, feature engineering, model training, hyperparameter tuning, and deployment capabilities"
    start_time = time.time()
    result2 = agent.analyze_user_input(complex_query)
    complex_time = time.time() - start_time
    
    print("Performance Results:")
    print(f"Simple query:  {simple_time:.4f}s - Intent: {result1['primary_intent']}")
    print(f"Complex query: {complex_time:.4f}s - Intent: {result2['primary_intent']}")
    print(f"Overhead ratio: {complex_time/simple_time:.2f}x")
    
    print()


def main():
    """Run all MiniMax Agent demonstrations"""
    print("🤖 MiniMax Agent for Neo-Clone - Comprehensive Demo")
    print("=" * 60)
    print("This demo shows the MiniMax emulation layer in action:")
    print("• Intent analysis and classification")
    print("• Dynamic skill generation")
    print("• Integration with Neo-Clone brain")
    print("• Reasoning trace generation")
    print("• Performance characteristics")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_intent_analysis()
        demo_skill_generation()
        demo_integration_with_brain()
        demo_skill_creation_and_usage()
        demo_reasoning_traces()
        demo_performance_comparison()
        
        print_section("DEMO COMPLETION")
        print("✅ All MiniMax Agent demonstrations completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Intelligent intent analysis with confidence scoring")
        print("  • Dynamic skill generation with code templates")
        print("  • Seamless integration with Neo-Clone's brain system")
        print("  • Detailed reasoning traces for transparency")
        print("  • Real-time skill creation and execution")
        print("\nThe MiniMax Agent is now ready for use in Neo-Clone!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()