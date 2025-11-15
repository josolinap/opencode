#!/usr/bin/env python3
"""
Fixed Spec-Driven Development Planner for OpenCode
Simplified implementation with resolved object type issues

This module provides:
- Reliable requirements parsing
- Structured implementation planning  
- File-level plan generation
- Mermaid diagram creation
- Reasoning and verification
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate" 
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

class PhaseType(Enum):
    """Implementation phase types"""
    PLANNING = "planning"
    SETUP = "setup"
    CORE_IMPLEMENTATION = "core_implementation"
    INTEGRATION = "integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"

@dataclass
class PhaseFile:
    """File specification for a phase"""
    filename: str
    purpose: str
    complexity: str
    dependencies: List[str]

@dataclass 
class ImplementationPhase:
    """Implementation phase"""
    name: str
    phase_type: str
    description: str
    objectives: List[str]
    deliverables: List[str]
    files: List[PhaseFile]
    prerequisites: List[str]
    duration: str
    risks: List[str]

@dataclass
class MermaidDiagram:
    """Mermaid diagram"""
    diagram_type: str
    title: str
    content: str
    description: str

@dataclass
class ImplementationReasoning:
    """Implementation reasoning"""
    approach: str
    rationale: str
    technologies: List[str]
    best_practices: List[str]
    potential_issues: List[str]
    mitigation_strategies: List[str]

@dataclass
class SuccessMetrics:
    """Success metrics for the plan"""
    completion_percentage: float
    test_coverage: int
    performance_benchmarks: Dict[str, str]
    security_score: int
    code_quality_score: int

@dataclass
class ImplementationPlan:
    """Complete implementation plan"""
    plan_id: str
    task_description: str
    complexity_level: str
    phases: List[ImplementationPhase]
    diagrams: List[MermaidDiagram]
    reasoning: ImplementationReasoning
    success_metrics: SuccessMetrics
    created_at: str
    estimated_duration: str

class RequirementsParser:
    """Parse and analyze requirements"""
    
    def __init__(self):
        self.task_keywords = {
            'web_application': ['web', 'website', 'app', 'application', 'frontend', 'backend', 'api'],
            'authentication': ['auth', 'login', 'register', 'user', 'permission', 'jwt', 'oauth'],
            'database_system': ['database', 'db', 'sql', 'nosql', 'postgres', 'mysql', 'mongodb'],
            'ai_ml_system': ['ai', 'ml', 'machine learning', 'model', 'train', 'predict'],
            'mobile_app': ['mobile', 'ios', 'android', 'react native', 'flutter'],
            'devops': ['docker', 'kubernetes', 'deploy', 'ci', 'cd', 'pipeline']
        }
    
    def parse_requirements(self, requirements: str) -> Dict[str, Any]:
        """Parse requirements into structured data"""
        requirements_lower = requirements.lower()
        
        # Detect task types
        detected_types = []
        for task_type, keywords in self.task_keywords.items():
            if any(keyword in requirements_lower for keyword in keywords):
                detected_types.append(task_type)
        
        # Extract key components
        components = []
        component_keywords = ['authentication', 'authorization', 'database', 'api', 'frontend', 
                             'backend', 'user interface', 'payment', 'notification', 'search']
        for keyword in component_keywords:
            if keyword in requirements_lower:
                components.append(keyword)
        
        # Determine complexity
        complexity = TaskComplexity.MODERATE
        if any(word in requirements_lower for word in ['enterprise', 'large scale', 'distributed']):
            complexity = TaskComplexity.ENTERPRISE
        elif any(word in requirements_lower for word in ['simple', 'basic', 'single']):
            complexity = TaskComplexity.SIMPLE
        elif any(word in requirements_lower for word in ['complex', 'advanced', 'sophisticated']):
            complexity = TaskComplexity.COMPLEX
        
        # Extract technologies
        tech_keywords = ['python', 'javascript', 'typescript', 'react', 'vue', 'angular',
                        'node', 'express', 'flask', 'django', 'fastapi', 'spring',
                        'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes']
        technologies = [tech for tech in tech_keywords if tech in requirements_lower]
        
        return {
            'detected_types': detected_types,
            'complexity': complexity,
            'components': components,
            'technologies': technologies,
            'original_requirements': requirements
        }

class SpecDrivenPlanner:
    """Main spec-driven planner"""
    
    def __init__(self):
        self.requirements_parser = RequirementsParser()
    
    def create_implementation_plan(self, requirements: str) -> ImplementationPlan:
        """Create complete implementation plan from requirements"""
        logger.info(f"Creating implementation plan for: {requirements[:100]}...")
        
        # Parse requirements
        parsed = self.requirements_parser.parse_requirements(requirements)
        logger.info(f"Parsed requirements: {parsed['detected_types']}")
        
        # Generate phases
        phases = self._generate_phases(parsed)
        
        # Generate files for each phase
        for phase in phases:
            phase.files = self._generate_phase_files(phase, parsed)
        
        # Generate diagrams
        diagrams = self._generate_diagrams(phases)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(parsed, phases)
        
        # Generate success metrics
        success_metrics = self._generate_success_metrics(parsed)
        
        # Create plan
        plan = ImplementationPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_description=requirements,
            complexity_level=parsed['complexity'].value,
            phases=phases,
            diagrams=diagrams,
            reasoning=reasoning,
            success_metrics=success_metrics,
            created_at=datetime.now().isoformat(),
            estimated_duration=self._estimate_total_duration(phases)
        )
        
        logger.info(f"Implementation plan created with ID: {plan.plan_id}")
        return plan
    
    def _generate_phases(self, parsed: Dict[str, Any]) -> List[ImplementationPhase]:
        """Generate implementation phases"""
        phases = []
        
        # Planning phase
        phases.append(ImplementationPhase(
            name="Requirements Analysis & Planning",
            phase_type=PhaseType.PLANNING.value,
            description="Analyze requirements and create detailed implementation plan",
            objectives=[
                "Validate requirements completeness",
                "Identify technical constraints", 
                "Define implementation strategy",
                "Create project timeline"
            ],
            deliverables=[
                "Requirements validation report",
                "Technical architecture document",
                "Implementation roadmap",
                "Risk assessment"
            ],
            files=[],
            prerequisites=[],
            duration="1-2 hours",
            risks=[
                "Incomplete or ambiguous requirements",
                "Technical constraints not discovered",
                "Scope creep during development"
            ]
        ))
        
        # Setup phase
        phases.append(ImplementationPhase(
            name="Project Setup & Configuration",
            phase_type=PhaseType.SETUP.value,
            description="Set up development environment and project structure",
            objectives=[
                "Initialize project structure",
                "Configure development tools",
                "Set up version control",
                "Install dependencies"
            ],
            deliverables=[
                "Project directory structure",
                "Development environment configuration",
                "Version control setup",
                "Dependency management"
            ],
            files=[],
            prerequisites=["Requirements Analysis & Planning"],
            duration="2-3 hours",
            risks=[
                "Configuration conflicts",
                "Dependency compatibility issues",
                "Environment setup problems"
            ]
        ))
        
        # Add task-specific phases
        for task_type in parsed['detected_types']:
            phase = self._create_task_specific_phase(task_type)
            if phase:
                phases.append(phase)
        
        # Integration phase
        phases.append(ImplementationPhase(
            name="System Integration & Testing",
            phase_type=PhaseType.INTEGRATION.value,
            description="Integrate all components and perform system testing",
            objectives=[
                "Integrate all system components",
                "Perform end-to-end testing",
                "Validate system requirements",
                "Optimize performance"
            ],
            deliverables=[
                "Integrated system",
                "Test results",
                "Performance report",
                "Integration documentation"
            ],
            files=[],
            prerequisites=["All core implementation phases"],
            duration="4-6 hours",
            risks=[
                "Integration conflicts",
                "Performance issues",
                "Testing failures"
            ]
        ))
        
        # Documentation phase
        phases.append(ImplementationPhase(
            name="Documentation & Deployment Preparation",
            phase_type=PhaseType.DOCUMENTATION.value,
            description="Create comprehensive documentation and prepare for deployment",
            objectives=[
                "Write user documentation",
                "Create API documentation",
                "Prepare deployment guide",
                "Create maintenance documentation"
            ],
            deliverables=[
                "User manual",
                "API documentation",
                "Deployment guide",
                "Maintenance documentation"
            ],
            files=[],
            prerequisites=["System Integration & Testing"],
            duration="2-3 hours",
            risks=[
                "Documentation gaps",
                "Unclear deployment process",
                "Missing user guidance"
            ]
        ))
        
        return phases
    
    def _create_task_specific_phase(self, task_type: str) -> Optional[ImplementationPhase]:
        """Create task-specific implementation phase"""
        phases_map = {
            'web_application': ImplementationPhase(
                name="Web Application Development",
                phase_type=PhaseType.CORE_IMPLEMENTATION.value,
                description="Develop the web application with frontend and backend",
                objectives=[
                    "Create responsive frontend interface",
                    "Implement backend API endpoints",
                    "Integrate with database",
                    "Implement user authentication"
                ],
                deliverables=[
                    "Frontend application",
                    "Backend API",
                    "Database integration",
                    "Authentication system"
                ],
                files=[],
                prerequisites=["Project Setup & Configuration"],
                duration="8-12 hours",
                risks=[
                    "Frontend-backend integration issues",
                    "Database performance problems",
                    "Security vulnerabilities",
                    "Responsive design challenges"
                ]
            ),
            'authentication': ImplementationPhase(
                name="Authentication & Authorization System",
                phase_type=PhaseType.CORE_IMPLEMENTATION.value,
                description="Implement secure authentication and authorization",
                objectives=[
                    "Implement user registration and login",
                    "Add session management",
                    "Implement role-based access control",
                    "Ensure security best practices"
                ],
                deliverables=[
                    "User authentication system",
                    "Session management",
                    "Authorization middleware",
                    "Security configuration"
                ],
                files=[],
                prerequisites=["Project Setup & Configuration"],
                duration="6-8 hours",
                risks=[
                    "Security vulnerabilities",
                    "Session management issues",
                    "Authorization bypasses",
                    "Password security problems"
                ]
            ),
            'database_system': ImplementationPhase(
                name="Database Design & Implementation",
                phase_type=PhaseType.CORE_IMPLEMENTATION.value,
                description="Design and implement database schema and operations",
                objectives=[
                    "Design database schema",
                    "Implement data models",
                    "Create migration scripts",
                    "Optimize database performance"
                ],
                deliverables=[
                    "Database schema design",
                    "Data models implementation",
                    "Migration scripts",
                    "Database optimization"
                ],
                files=[],
                prerequisites=["Project Setup & Configuration"],
                duration="4-6 hours",
                risks=[
                    "Schema design issues",
                    "Performance bottlenecks",
                    "Data integrity problems",
                    "Migration failures"
                ]
            )
        }
        
        return phases_map.get(task_type)
    
    def _generate_phase_files(self, phase: ImplementationPhase, 
                            parsed: Dict[str, Any]) -> List[PhaseFile]:
        """Generate files for a phase"""
        files = []
        
        if phase.phase_type == PhaseType.SETUP.value:
            files = [
                PhaseFile("requirements.txt", "Python package dependencies", "low", []),
                PhaseFile("package.json", "Node.js project configuration", "low", []),
                PhaseFile("Dockerfile", "Container configuration", "low", []),
                PhaseFile("docker-compose.yml", "Multi-container setup", "medium", ["Dockerfile"]),
            ]
        elif phase.phase_type == PhaseType.CORE_IMPLEMENTATION.value:
            # Add task-specific files
            if "web_application" in parsed['detected_types']:
                files = [
                    PhaseFile("app/main.py", "Main application entry point", "medium", []),
                    PhaseFile("app/models.py", "Database models", "medium", []),
                    PhaseFile("app/routes/api.py", "API endpoints", "high", ["app/main.py"]),
                    PhaseFile("templates/index.html", "Main HTML template", "medium", []),
                    PhaseFile("static/js/app.js", "Frontend JavaScript", "medium", []),
                ]
            elif "authentication" in parsed['detected_types']:
                files = [
                    PhaseFile("app/auth.py", "Authentication module", "medium", ["app/models.py"]),
                    PhaseFile("app/middleware/auth.py", "Authentication middleware", "high", ["app/auth.py"]),
                    PhaseFile("tests/test_auth.py", "Authentication tests", "medium", ["app/auth.py"]),
                ]
            elif "database_system" in parsed['detected_types']:
                files = [
                    PhaseFile("database/schema.sql", "Database schema", "medium", []),
                    PhaseFile("database/migrations/001_initial.py", "Migration script", "medium", ["database/schema.sql"]),
                    PhaseFile("database/seeds.py", "Database seeding", "low", ["database/migrations/001_initial.py"]),
                ]
        elif phase.phase_type == PhaseType.TESTING.value:
            files = [
                PhaseFile("tests/test_main.py", "Main application tests", "medium", ["app/main.py"]),
                PhaseFile("tests/integration/test_api.py", "API integration tests", "high", ["app/routes/api.py"]),
                PhaseFile("tests/performance/test_load.py", "Performance tests", "medium", ["app/main.py"]),
            ]
        elif phase.phase_type == PhaseType.DOCUMENTATION.value:
            files = [
                PhaseFile("README.md", "Project documentation", "low", []),
                PhaseFile("docs/API.md", "API documentation", "medium", ["app/routes/api.py"]),
                PhaseFile("docs/DEPLOYMENT.md", "Deployment guide", "medium", ["Dockerfile"]),
            ]
        
        return files
    
    def _generate_diagrams(self, phases: List[ImplementationPhase]) -> List[MermaidDiagram]:
        """Generate Mermaid diagrams"""
        diagrams = []
        
        # Workflow diagram
        workflow_content = "flowchart TD\n"
        workflow_content += "    A[Requirements] --> B[Planning]\n"
        workflow_content += "    B --> C[Setup]\n"
        
        for i, phase in enumerate(phases):
            phase_id = f"Phase{i+1}"
            next_phase = f"End" if i == len(phases)-1 else f"Phase{i+2}"
            workflow_content += f"    C --> {phase_id}[{phase.name}]\n"
            workflow_content += f"    {phase_id} --> {next_phase}\n"
        
        diagrams.append(MermaidDiagram(
            diagram_type="flowchart",
            title="Implementation Workflow",
            content=workflow_content,
            description="Shows the implementation phases and their dependencies"
        ))
        
        # Architecture diagram
        arch_content = "graph TB\n"
        arch_content += "    subgraph \"Client Layer\"\n"
        arch_content += "        Web[Web Browser]\n"
        arch_content += "        Mobile[Mobile App]\n"
        arch_content += "    end\n"
        
        arch_content += "    subgraph \"Application Layer\"\n"
        arch_content += "        API[REST API]\n"
        arch_content += "        Auth[Authentication]\n"
        arch_content += "        Business[Business Logic]\n"
        arch_content += "    end\n"
        
        arch_content += "    subgraph \"Data Layer\"\n"
        arch_content += "        Database[(Database)]\n"
        arch_content += "        Cache[(Cache)]\n"
        arch_content += "    end\n"
        
        arch_content += "    Web --> API\n"
        arch_content += "    Mobile --> API\n"
        arch_content += "    API --> Auth\n"
        arch_content += "    API --> Business\n"
        arch_content += "    Business --> Database\n"
        arch_content += "    Business --> Cache\n"
        
        diagrams.append(MermaidDiagram(
            diagram_type="graph",
            title="System Architecture",
            content=arch_content,
            description="Shows the high-level system architecture and component relationships"
        ))
        
        return diagrams
    
    def _generate_reasoning(self, parsed: Dict[str, Any], 
                          phases: List[ImplementationPhase]) -> ImplementationReasoning:
        """Generate implementation reasoning"""
        
        # Determine approach
        approach = "modular"
        if parsed['complexity'] == TaskComplexity.ENTERPRISE:
            approach = "microservices"
        elif parsed['complexity'] == TaskComplexity.SIMPLE:
            approach = "monolithic"
        
        # Get technologies
        technologies = parsed.get('technologies', [])
        if not technologies:
            # Default technologies based on task types
            if 'web_application' in parsed['detected_types']:
                technologies = ['Python', 'Flask/FastAPI', 'JavaScript', 'HTML/CSS']
            if 'authentication' in parsed['detected_types']:
                technologies.extend(['JWT', 'bcrypt', 'SQLAlchemy'])
            if 'database_system' in parsed['detected_types']:
                technologies.extend(['PostgreSQL', 'Redis'])
        
        best_practices = [
            "RESTful API design principles",
            "OWASP security guidelines", 
            "Clean code principles",
            "Test-driven development",
            "Documentation-first approach"
        ]
        
        potential_issues = [
            "Integration complexity between modules",
            "Performance bottlenecks in data access",
            "Security vulnerabilities in user input handling",
            "Scalability challenges with increased load"
        ]
        
        mitigation_strategies = [
            "Implement comprehensive integration testing",
            "Use database query optimization",
            "Apply input validation and sanitization",
            "Design for horizontal scaling"
        ]
        
        rationale = f"Selected {approach} architecture for {parsed['complexity'].value} complexity level with {', '.join(parsed['detected_types'])} components."
        
        return ImplementationReasoning(
            approach=approach,
            rationale=rationale,
            technologies=list(set(technologies)),  # Remove duplicates
            best_practices=best_practices,
            potential_issues=potential_issues,
            mitigation_strategies=mitigation_strategies
        )
    
    def _generate_success_metrics(self, parsed: Dict[str, Any]) -> SuccessMetrics:
        """Generate success metrics"""
        return SuccessMetrics(
            completion_percentage=100.0,
            test_coverage=80,
            performance_benchmarks={
                "page_load_time": "< 3 seconds",
                "api_response_time": "< 500ms"
            },
            security_score=95,
            code_quality_score=85
        )
    
    def _estimate_total_duration(self, phases: List[ImplementationPhase]) -> str:
        """Estimate total duration"""
        total_hours = 0
        for phase in phases:
            duration_str = phase.duration
            if "hours" in duration_str:
                # Extract hours (simplified)
                import re
                hours_match = re.search(r'(\d+)', duration_str)
                if hours_match:
                    total_hours += int(hours_match.group(1))
        
        if total_hours <= 8:
            return f"{total_hours} hours"
        elif total_hours <= 40:
            days = total_hours / 8
            return f"{days:.1f} days"
        else:
            weeks = total_hours / 40
            return f"{weeks:.1f} weeks"
    
    def save_plan_to_file(self, plan: ImplementationPlan, workspace_path: str = "."):
        """Save implementation plan to JSON file"""
        plan_dict = asdict(plan)
        
        plan_file = Path(workspace_path) / f"implementation_plan_{plan.plan_id}.json"
        with open(plan_file, 'w') as f:
            json.dump(plan_dict, f, indent=2, default=str)
        
        logger.info(f"Plan saved to: {plan_file}")
        return plan_file

def demo_fixed_spec_driven_planner():
    """Demonstrate the fixed spec-driven planner"""
    
    print("🚀 Fixed Spec-Driven Development Planner Demo")
    print("=" * 60)
    
    # Initialize planner
    planner = SpecDrivenPlanner()
    
    # Example requirements
    test_requirements = """
    Create a user authentication system for a web application with the following features:
    - User registration with email validation
    - Secure login with password hashing
    - JWT token-based session management
    - Role-based access control (admin, user)
    - Password reset functionality
    - Integration with PostgreSQL database
    - API endpoints for all authentication operations
    - Frontend login/register forms
    - Security best practices and input validation
    """
    
    print(f"📋 Requirements:\n{test_requirements.strip()}\n")
    
    try:
        # Generate implementation plan
        plan = planner.create_implementation_plan(test_requirements)
        
        # Save to file
        plan_file = planner.save_plan_to_file(plan)
        
        print(f"✅ Implementation Plan Generated Successfully!")
        print(f"📊 Plan Summary:")
        print(f"• Plan ID: {plan.plan_id}")
        print(f"• Complexity: {plan.complexity_level}")
        print(f"• Phases: {len(plan.phases)}")
        print(f"• Diagrams: {len(plan.diagrams)}")
        print(f"• Duration: {plan.estimated_duration}")
        
        print(f"\n📈 Implementation Phases:")
        for i, phase in enumerate(plan.phases, 1):
            print(f"{i}. {phase.name} ({phase.duration})")
            print(f"   {phase.description}")
            print(f"   Files: {len(phase.files)} files")
            print()
        
        print(f"💻 Technologies: {', '.join(plan.reasoning.technologies)}")
        print(f"🎯 Approach: {plan.reasoning.approach}")
        print(f"⚡ Rationale: {plan.reasoning.rationale}")
        
        print(f"\n📈 Generated Diagrams:")
        for diagram in plan.diagrams:
            print(f"• {diagram.title} ({diagram.diagram_type})")
        
        print(f"\n💾 Plan saved to: {plan_file}")
        
        return plan
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    plan = demo_fixed_spec_driven_planner()