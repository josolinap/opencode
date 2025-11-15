#!/usr/bin/env python3
"""
Spec-Driven Development Planner for OpenCode
Based on Traycer's approach to transforming requirements into structured implementation plans

This module implements:
- Intent parsing from natural language requirements
- Codebase exploration and analysis
- Generation of file-level detailed plans
- Mermaid diagram creation for visualization
- Reasoning generation for each implementation step
- Implementation verification framework
"""

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"           # Single file, basic functionality
    MODERATE = "moderate"       # Multiple files, standard patterns
    COMPLEX = "complex"         # Multi-component, advanced patterns
    ENTERPRISE = "enterprise"   # Large-scale, distributed systems

class ImplementationPhase(Enum):
    """Implementation phases"""
    PLANNING = "planning"
    SETUP = "setup"
    CORE_IMPLEMENTATION = "core_implementation"
    INTEGRATION = "integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"

class FileType(Enum):
    """File types for planning"""
    SOURCE_CODE = "source_code"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    TEST = "test"
    DEPLOYMENT = "deployment"
    ASSET = "asset"

@dataclass
class PlanFile:
    """Individual file in implementation plan"""
    filename: str
    file_type: FileType
    description: str
    purpose: str
    key_components: List[str]
    dependencies: List[str]
    estimated_complexity: str
    implementation_notes: str

@dataclass
class PlanPhase:
    """Implementation phase with detailed planning"""
    phase_name: str
    phase_type: ImplementationPhase
    description: str
    objectives: List[str]
    deliverables: List[str]
    files: List[PlanFile]
    prerequisites: List[str]
    success_criteria: List[str]
    estimated_duration: str
    risks: List[str]

@dataclass
class MermaidDiagram:
    """Mermaid diagram for system visualization"""
    diagram_type: str
    title: str
    content: str
    description: str

@dataclass
class ImplementationReasoning:
    """Reasoning for implementation approach"""
    approach: str
    rationale: str
    alternatives_considered: List[str]
    trade_offs: List[str]
    best_practices_applied: List[str]
    potential_issues: List[str]
    mitigation_strategies: List[str]

@dataclass
class VerificationCriteria:
    """Criteria for verifying implementation adherence"""
    functional_tests: List[str]
    integration_tests: List[str]
    performance_criteria: List[str]
    security_checks: List[str]
    code_quality_metrics: List[str]
    documentation_requirements: List[str]

@dataclass
class ImplementationPlan:
    """Complete implementation plan"""
    plan_id: str
    task_description: str
    complexity_level: TaskComplexity
    phases: List[PlanPhase]
    diagrams: List[MermaidDiagram]
    reasoning: ImplementationReasoning
    verification_criteria: VerificationCriteria
    success_metrics: Dict[str, Any]
    created_at: datetime
    estimated_total_duration: str

class RequirementsParser:
    """Parse natural language requirements into structured intent"""
    
    def __init__(self):
        self.task_patterns = {
            'web_application': [
                r'\b(web|website|app|application|frontend|backend|api)\b',
                r'\b(http|rest|graphql|server|client)\b'
            ],
            'database_system': [
                r'\b(database|db|sql|nosql|postgres|mysql|mongodb)\b',
                r'\b(schema|migration|queries|storage)\b'
            ],
            'authentication': [
                r'\b(auth|login|register|user|permission|jwt|oauth)\b',
                r'\b(security|authorization|credential)\b'
            ],
            'ai_ml_system': [
                r'\b(ai|ml|machine learning|model|train|predict)\b',
                r'\b(neural|algorithm|classification|regression)\b'
            ],
            'mobile_app': [
                r'\b(mobile|ios|android|react native|flutter)\b',
                r'\b(app store|google play|native)\b'
            ],
            'devops': [
                r'\b(docker|kubernetes|deploy|ci|cd|pipeline)\b',
                r'\b(automation|infrastructure|cloud|aws|azure)\b'
            ]
        }
        
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                'simple', 'basic', 'single', 'one file', 'minimal'
            ],
            TaskComplexity.MODERATE: [
                'multiple', 'standard', 'typical', 'moderate', 'several'
            ],
            TaskComplexity.COMPLEX: [
                'complex', 'advanced', 'sophisticated', 'multiple components'
            ],
            TaskComplexity.ENTERPRISE: [
                'enterprise', 'large scale', 'distributed', 'microservices'
            ]
        }
    
    async def parse_requirements(self, requirements: str) -> Dict[str, Any]:
        """Parse requirements into structured intent"""
        requirements_lower = requirements.lower()
        
        # Detect task types
        detected_types = []
        for task_type, patterns in self.task_patterns.items():
            if any(re.search(pattern, requirements_lower) for pattern in patterns):
                detected_types.append(task_type)
        
        # Determine complexity
        complexity = TaskComplexity.MODERATE
        for comp_level, indicators in self.complexity_indicators.items():
            if any(indicator in requirements_lower for indicator in indicators):
                complexity = comp_level
                break
        
        # Extract key components
        components = await self._extract_components(requirements)
        
        # Identify technologies
        technologies = await self._identify_technologies(requirements)
        
        # Determine constraints
        constraints = await self._extract_constraints(requirements)
        
        return {
            'original_requirements': requirements,
            'detected_types': detected_types,
            'complexity': complexity,
            'components': components,
            'technologies': technologies,
            'constraints': constraints,
            'success_criteria': await self._extract_success_criteria(requirements)
        }
    
    async def _extract_components(self, requirements: str) -> List[str]:
        """Extract key components from requirements"""
        # Simple component extraction - can be enhanced with NLP
        component_keywords = [
            'authentication', 'authorization', 'database', 'api', 'frontend',
            'backend', 'user interface', 'payment', 'notification', 'search',
            'upload', 'download', 'reporting', 'dashboard', 'admin panel'
        ]
        
        components = []
        requirements_lower = requirements.lower()
        for keyword in component_keywords:
            if keyword in requirements_lower:
                components.append(keyword)
        
        return components
    
    async def _identify_technologies(self, requirements: str) -> List[str]:
        """Identify mentioned technologies"""
        tech_keywords = [
            'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
            'node', 'express', 'flask', 'django', 'fastapi', 'spring',
            'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes'
        ]
        
        technologies = []
        requirements_lower = requirements.lower()
        for tech in tech_keywords:
            if tech in requirements_lower:
                technologies.append(tech)
        
        return technologies
    
    async def _extract_constraints(self, requirements: str) -> List[str]:
        """Extract constraints and requirements"""
        constraint_keywords = [
            'must', 'should', 'required', 'must not', 'cannot',
            'performance', 'scalability', 'security', 'responsive'
        ]
        
        constraints = []
        requirements_lower = requirements.lower()
        for keyword in constraint_keywords:
            if keyword in requirements_lower:
                constraints.append(keyword)
        
        return constraints
    
    async def _extract_success_criteria(self, requirements: str) -> List[str]:
        """Extract success criteria from requirements"""
        # Extract success criteria - can be enhanced with better NLP
        criteria_patterns = [
            r'should\s+(\w+)',
            r'must\s+(\w+)',
            r'able to\s+(\w+)',
            r'can\s+(\w+)'
        ]
        
        criteria = []
        for pattern in criteria_patterns:
            matches = re.findall(pattern, requirements.lower())
            criteria.extend(matches)
        
        return list(set(criteria))  # Remove duplicates

class CodebaseExplorer:
    """Explore existing codebase to understand current state"""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
    
    async def explore_codebase(self) -> Dict[str, Any]:
        """Explore the codebase and return analysis"""
        if not self.workspace_path.exists():
            return {'exists': False, 'analysis': {}}
        
        file_structure = await self._analyze_file_structure()
        existing_files = await self._identify_existing_files()
        dependencies = await self._analyze_dependencies()
        
        return {
            'exists': True,
            'file_structure': file_structure,
            'existing_files': existing_files,
            'dependencies': dependencies,
            'entry_points': await self._find_entry_points(),
            'config_files': await self._find_config_files(),
            'test_files': await self._find_test_files()
        }
    
    async def _analyze_file_structure(self) -> Dict[str, Any]:
        """Analyze the overall file structure"""
        structure = {
            'total_files': 0,
            'directories': [],
            'file_types': {},
            'language_distribution': {}
        }
        
        for file_path in self.workspace_path.rglob('*'):
            if file_path.is_file():
                structure['total_files'] += 1
                
                # Categorize by extension
                ext = file_path.suffix.lower()
                structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                
                # Identify language
                language = self._get_language_from_extension(ext)
                if language:
                    structure['language_distribution'][language] = \
                        structure['language_distribution'].get(language, 0) + 1
        
        return structure
    
    async def _identify_existing_files(self) -> List[Dict[str, str]]:
        """Identify important existing files"""
        important_files = []
        
        common_patterns = [
            ('main.py', 'Main entry point'),
            ('app.py', 'Application entry point'),
            ('index.js', 'JavaScript entry point'),
            ('package.json', 'Node.js configuration'),
            ('requirements.txt', 'Python dependencies'),
            ('Dockerfile', 'Docker configuration'),
            ('README.md', 'Project documentation'),
            ('.env', 'Environment configuration')
        ]
        
        for pattern, description in common_patterns:
            for file_path in self.workspace_path.rglob(pattern):
                if file_path.is_file():
                    important_files.append({
                        'path': str(file_path.relative_to(self.workspace_path)),
                        'description': description,
                        'size': file_path.stat().st_size
                    })
        
        return important_files
    
    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {
            'python': {},
            'nodejs': {},
            'docker': False,
            'database': []
        }
        
        # Python dependencies
        req_files = list(self.workspace_path.rglob('requirements.txt'))
        if req_files:
            try:
                with open(req_files[0], 'r') as f:
                    content = f.read()
                    # Parse dependencies (simplified)
                    for line in content.strip().split('\n'):
                        if line and not line.startswith('#'):
                            deps = line.split('==')
                            if len(deps) == 2:
                                dependencies['python'][deps[0]] = deps[1]
            except Exception as e:
                logger.warning(f"Could not parse requirements.txt: {e}")
        
        # Node.js dependencies
        package_json_files = list(self.workspace_path.rglob('package.json'))
        if package_json_files:
            try:
                with open(package_json_files[0], 'r') as f:
                    data = json.load(f)
                    dependencies['nodejs'] = {
                        'dependencies': data.get('dependencies', {}),
                        'devDependencies': data.get('devDependencies', {})
                    }
            except Exception as e:
                logger.warning(f"Could not parse package.json: {e}")
        
        # Docker
        dockerfile = self.workspace_path / 'Dockerfile'
        dependencies['docker'] = dockerfile.exists()
        
        return dependencies
    
    async def _find_entry_points(self) -> List[str]:
        """Find application entry points"""
        entry_points = []
        
        patterns = ['main.py', 'app.py', 'index.js', 'server.js', '__main__.py']
        for pattern in patterns:
            for file_path in self.workspace_path.rglob(pattern):
                if file_path.is_file():
                    entry_points.append(str(file_path.relative_to(self.workspace_path)))
        
        return entry_points
    
    async def _find_config_files(self) -> List[str]:
        """Find configuration files"""
        config_patterns = ['*.config.js', '*.config.ts', '.env*', '*.ini', '*.yaml', '*.yml']
        config_files = []
        
        for pattern in config_patterns:
            for file_path in self.workspace_path.rglob(pattern):
                if file_path.is_file():
                    config_files.append(str(file_path.relative_to(self.workspace_path)))
        
        return config_files
    
    async def _find_test_files(self) -> List[str]:
        """Find test files"""
        test_patterns = ['test_*.py', '*_test.py', '*.test.js', '*.spec.js', 'tests/*.py']
        test_files = []
        
        for pattern in test_patterns:
            for file_path in self.workspace_path.rglob(pattern):
                if file_path.is_file():
                    test_files.append(str(file_path.relative_to(self.workspace_path)))
        
        return test_files
    
    def _get_language_from_extension(self, extension: str) -> Optional[str]:
        """Get programming language from file extension"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sql': 'SQL',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML'
        }
        
        return language_map.get(extension.lower())

class MermaidDiagramGenerator:
    """Generate Mermaid diagrams for system visualization"""
    
    def __init__(self):
        self.diagram_templates = {
            'flowchart': self._generate_flowchart_template,
            'sequence': self._generate_sequence_template,
            'class': self._generate_class_template,
            'er': self._generate_er_template,
            'state': self._generate_state_template
        }
    
    async def generate_diagrams(self, plan: ImplementationPlan, 
                              codebase_analysis: Dict[str, Any]) -> List[MermaidDiagram]:
        """Generate relevant diagrams for the implementation plan"""
        diagrams = []
        
        # Generate workflow diagram
        workflow_diagram = await self._generate_workflow_diagram(plan)
        if workflow_diagram:
            diagrams.append(workflow_diagram)
        
        # Generate architecture diagram
        architecture_diagram = await self._generate_architecture_diagram(plan)
        if architecture_diagram:
            diagrams.append(architecture_diagram)
        
        # Generate database diagram if needed
        if 'database' in plan.task_description.lower():
            db_diagram = await self._generate_database_diagram(plan)
            if db_diagram:
                diagrams.append(db_diagram)
        
        return diagrams
    
    async def _generate_workflow_diagram(self, plan: ImplementationPlan) -> Optional[MermaidDiagram]:
        """Generate workflow diagram showing implementation phases"""
        content = "flowchart TD\n"
        content += "    A[Requirements] --> B[Planning]\n"
        content += "    B --> C[Setup]\n"
        
        for i, phase in enumerate(plan.phases):
            phase_id = f"Phase{i+1}"
            content += f"    C --> {phase_id}[{phase.phase_name}]\n"
            content += f"    {phase_id} --> {phase_id}Next{['None', f'Phase{i+2}', 'Testing', 'Deployment'][i%4] if i < len(plan.phases)-1 else 'End'}\n"
        
        content += "    C --> End[Implementation Complete]\n"
        
        return MermaidDiagram(
            diagram_type="flowchart",
            title=f"Implementation Workflow: {plan.task_description[:50]}...",
            content=content,
            description="Shows the implementation phases and their dependencies"
        )
    
    async def _generate_architecture_diagram(self, plan: ImplementationPlan) -> Optional[MermaidDiagram]:
        """Generate system architecture diagram"""
        content = "graph TB\n"
        content += "    subgraph \"Client Layer\"\n"
        content += "        Web[Web Browser]\n"
        content += "        Mobile[Mobile App]\n"
        content += "    end\n"
        
        content += "    subgraph \"Application Layer\"\n"
        content += "        API[REST API]\n"
        content += "        Auth[Authentication]\n"
        content += "        Business[Business Logic]\n"
        content += "    end\n"
        
        content += "    subgraph \"Data Layer\"\n"
        content += "        Database[(Database)]\n"
        content += "        Cache[(Cache)]\n"
        content += "    end\n"
        
        content += "    Web --> API\n"
        content += "    Mobile --> API\n"
        content += "    API --> Auth\n"
        content += "    API --> Business\n"
        content += "    Business --> Database\n"
        content += "    Business --> Cache\n"
        
        return MermaidDiagram(
            diagram_type="graph",
            title=f"System Architecture: {plan.task_description[:50]}...",
            content=content,
            description="Shows the high-level system architecture and component relationships"
        )
    
    async def _generate_database_diagram(self, plan: ImplementationPlan) -> Optional[MermaidDiagram]:
        """Generate entity-relationship diagram"""
        content = "erDiagram\n"
        content += "    USER {\n"
        content += "        int id PK\n"
        content += "        string name\n"
        content += "        string email\n"
        content += "        datetime created_at\n"
        content += "    }\n"
        
        # This would be enhanced to read from actual plan data
        content += "    USER ||--o{ POST : creates\n"
        content += "    USER {\n"
        content += "        int id PK\n"
        content += "        string title\n"
        content += "        text content\n"
        content += "        int user_id FK\n"
        content += "        datetime created_at\n"
        content += "    }\n"
        
        return MermaidDiagram(
            diagram_type="er",
            title=f"Database Schema: {plan.task_description[:50]}...",
            content=content,
            description="Shows the database entities and their relationships"
        )
    
    def _generate_flowchart_template(self) -> str:
        return """flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E"""
    
    def _generate_sequence_template(self) -> str:
        return """sequenceDiagram
    participant A as Component A
    participant B as Component B
    A->>B: Request
    B->>A: Response"""
    
    def _generate_class_template(self) -> str:
        return """classDiagram
    class ClassA {
        +attribute1: string
        +method1(): void
    }
    class ClassB {
        +attribute2: int
        +method2(): boolean
    }"""
    
    def _generate_er_template(self) -> str:
        return """erDiagram
    ENTITY1 {
        int id PK
        string name
    }
    ENTITY2 {
        int id PK
        string description
        int entity1_id FK
    }"""
    
    def _generate_state_template(self) -> str:
        return """stateDiagram-v2
    [*] --> State1
    State1 --> State2: Event
    State2 --> [*]"""

class PlanGenerator:
    """Generate detailed implementation plan from requirements and analysis"""
    
    def __init__(self):
        self.requirements_parser = RequirementsParser()
        self.codebase_explorer = CodebaseExplorer()
        self.diagram_generator = MermaidDiagramGenerator()
    
    async def generate_plan(self, requirements: str, 
                          workspace_path: str = ".") -> ImplementationPlan:
        """Generate complete implementation plan"""
        logger.info("Generating implementation plan...")
        
        # Parse requirements
        parsed_requirements = await self.requirements_parser.parse_requirements(requirements)
        logger.info(f"Parsed requirements: {parsed_requirements['detected_types']}")
        
        # Explore codebase
        codebase_analysis = await self.codebase_explorer.explore_codebase()
        logger.info(f"Codebase analysis: {codebase_analysis.get('exists', False)}")
        
        # Determine implementation phases
        phases = await self._generate_phases(parsed_requirements, codebase_analysis)
        logger.info(f"Generated {len(phases)} implementation phases")
        
        # Generate files for each phase
        for phase in phases:
            phase.files = await self._generate_phase_files(phase, parsed_requirements, codebase_analysis)
        
        # Generate diagrams
        diagrams = await self.diagram_generator.generate_diagrams(phases, codebase_analysis)
        logger.info(f"Generated {len(diagrams)} diagrams")
        
        # Generate reasoning
        reasoning = await self._generate_reasoning(parsed_requirements, phases)
        
        # Generate verification criteria
        verification_criteria = await self._generate_verification_criteria(parsed_requirements)
        
        # Create plan
        plan = ImplementationPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_description=requirements,
            complexity_level=parsed_requirements['complexity'],
            phases=phases,
            diagrams=diagrams,
            reasoning=reasoning,
            verification_criteria=verification_criteria,
            success_metrics=await self._generate_success_metrics(parsed_requirements),
            created_at=datetime.now(),
            estimated_total_duration=await self._estimate_duration(phases)
        )
        
        logger.info("Implementation plan generated successfully")
        return plan
    
    async def _generate_phases(self, requirements: Dict[str, Any], 
                             codebase_analysis: Dict[str, Any]) -> List[PlanPhase]:
        """Generate implementation phases based on requirements"""
        phases = []
        
        # Planning phase (always first)
        phases.append(PlanPhase(
            phase_name="Requirements Analysis & Planning",
            phase_type=ImplementationPhase.PLANNING,
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
            success_criteria=[
                "Requirements are clearly understood",
                "Technical approach is defined",
                "Project scope is validated"
            ],
            estimated_duration="1-2 hours",
            risks=[
                "Incomplete or ambiguous requirements",
                "Technical constraints not discovered",
                "Scope creep during development"
            ]
        ))
        
        # Setup phase
        phases.append(PlanPhase(
            phase_name="Project Setup & Configuration",
            phase_type=ImplementationPhase.SETUP,
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
            success_criteria=[
                "Project structure is properly organized",
                "All development tools are configured",
                "Dependencies are installed and working"
            ],
            estimated_duration="2-3 hours",
            risks=[
                "Configuration conflicts",
                "Dependency compatibility issues",
                "Environment setup problems"
            ]
        ))
        
        # Core implementation phases based on requirements
        for task_type in requirements['detected_types']:
            phase = await self._create_task_specific_phase(task_type, requirements)
            if phase:
                phases.append(phase)
        
        # Integration phase
        phases.append(PlanPhase(
            phase_name="System Integration & Testing",
            phase_type=ImplementationPhase.INTEGRATION,
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
            success_criteria=[
                "All components integrate successfully",
                "System tests pass",
                "Performance meets requirements"
            ],
            estimated_duration="4-6 hours",
            risks=[
                "Integration conflicts",
                "Performance issues",
                "Testing failures"
            ]
        ))
        
        # Documentation phase
        phases.append(PlanPhase(
            phase_name="Documentation & Deployment Preparation",
            phase_type=ImplementationPhase.DOCUMENTATION,
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
            success_criteria=[
                "All documentation is complete",
                "Deployment process is documented",
                "User guides are clear and accurate"
            ],
            estimated_duration="2-3 hours",
            risks=[
                "Documentation gaps",
                "Unclear deployment process",
                "Missing user guidance"
            ]
        ))
        
        return phases
    
    async def _create_task_specific_phase(self, task_type: str, 
                                        requirements: Dict[str, Any]) -> Optional[PlanPhase]:
        """Create task-specific implementation phase"""
        phases_map = {
            'web_application': PlanPhase(
                phase_name="Web Application Development",
                phase_type=ImplementationPhase.CORE_IMPLEMENTATION,
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
                success_criteria=[
                    "Frontend is responsive and functional",
                    "Backend API handles all required endpoints",
                    "Database operations work correctly",
                    "Authentication is secure and functional"
                ],
                estimated_duration="8-12 hours",
                risks=[
                    "Frontend-backend integration issues",
                    "Database performance problems",
                    "Security vulnerabilities",
                    "Responsive design challenges"
                ]
            ),
            'authentication': PlanPhase(
                phase_name="Authentication & Authorization System",
                phase_type=ImplementationPhase.CORE_IMPLEMENTATION,
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
                success_criteria=[
                    "Users can register and login securely",
                    "Sessions are properly managed",
                    "Authorization rules are enforced",
                    "Security best practices are followed"
                ],
                estimated_duration="4-6 hours",
                risks=[
                    "Security vulnerabilities",
                    "Session management issues",
                    "Authorization bypasses",
                    "Password security problems"
                ]
            )
            # Add more task-specific phases as needed
        }
        
        return phases_map.get(task_type)
    
    async def _generate_phase_files(self, phase: PlanPhase, 
                                  requirements: Dict[str, Any],
                                  codebase_analysis: Dict[str, Any]) -> List[PlanFile]:
        """Generate detailed file specifications for a phase"""
        files = []
        
        # Common files based on phase type
        if phase.phase_type == ImplementationPhase.SETUP:
            files.extend([
                PlanFile(
                    filename="requirements.txt",
                    file_type=FileType.CONFIGURATION,
                    description="Python package dependencies",
                    purpose="Manage Python dependencies for the project",
                    key_components=["packages", "versions", "extras"],
                    dependencies=[],
                    estimated_complexity="low",
                    implementation_notes="Include all required packages with specific versions"
                ),
                PlanFile(
                    filename="package.json",
                    file_type=FileType.CONFIGURATION,
                    description="Node.js project configuration",
                    purpose="Manage Node.js dependencies and scripts",
                    key_components=["dependencies", "devDependencies", "scripts"],
                    dependencies=[],
                    estimated_complexity="low",
                    implementation_notes="Set up development and production dependencies"
                )
            ])
        
        elif phase.phase_type == ImplementationPhase.CORE_IMPLEMENTATION:
            for task_type in requirements['detected_types']:
                task_files = await self._get_task_specific_files(task_type)
                files.extend(task_files)
        
        elif phase.phase_type == ImplementationPhase.TESTING:
            files.extend([
                PlanFile(
                    filename="tests/test_main.py",
                    file_type=FileType.TEST,
                    description="Main application tests",
                    purpose="Test core application functionality",
                    key_components=["test cases", "fixtures", "assertions"],
                    dependencies=["main.py"],
                    estimated_complexity="medium",
                    implementation_notes="Cover all main functionality with unit and integration tests"
                )
            ])
        
        return files
    
    async def _get_task_specific_files(self, task_type: str) -> List[PlanFile]:
        """Get file specifications for specific task types"""
        files_map = {
            'web_application': [
                PlanFile(
                    filename="app/main.py",
                    file_type=FileType.SOURCE_CODE,
                    description="Main web application entry point",
                    purpose="Initialize and configure the web application",
                    key_components=["Flask app", "route definitions", "error handlers"],
                    dependencies=["config.py", "models.py"],
                    estimated_complexity="medium",
                    implementation_notes="Create RESTful API endpoints and error handling"
                ),
                PlanFile(
                    filename="app/models.py",
                    file_type=FileType.SOURCE_CODE,
                    description="Database models",
                    purpose="Define database schema and relationships",
                    key_components=["SQLAlchemy models", "relationships", "validations"],
                    dependencies=["database config"],
                    estimated_complexity="medium",
                    implementation_notes="Use proper relationships and constraints"
                ),
                PlanFile(
                    filename="app/templates/index.html",
                    file_type=FileType.ASSET,
                    description="Main HTML template",
                    purpose="Provide the main user interface",
                    key_components=["HTML structure", "CSS styling", "JavaScript"],
                    dependencies=[],
                    estimated_complexity="medium",
                    implementation_notes="Create responsive design with modern CSS"
                )
            ],
            'authentication': [
                PlanFile(
                    filename="app/auth.py",
                    file_type=FileType.SOURCE_CODE,
                    description="Authentication module",
                    purpose="Handle user authentication and authorization",
                    key_components=["login", "register", "session management"],
                    dependencies=["models.py"],
                    estimated_complexity="medium",
                    implementation_notes="Implement secure password hashing and JWT tokens"
                )
            ]
        }
        
        return files_map.get(task_type, [])
    
    async def _generate_reasoning(self, requirements: Dict[str, Any], 
                                phases: List[PlanPhase]) -> ImplementationReasoning:
        """Generate reasoning for implementation approach"""
        
        # Determine approach based on requirements
        approach = "modular"
        if requirements['complexity'] == TaskComplexity.ENTERPRISE:
            approach = "microservices"
        elif requirements['complexity'] == TaskComplexity.SIMPLE:
            approach = "monolithic"
        
        rationale = f"""
        Approach: {approach} architecture
        Rationale: Selected based on complexity level ({requirements['complexity'].value}) and 
        detected components ({', '.join(requirements['components'])})
        """
        
        alternatives = [
            "Microservices architecture (more complex but scalable)",
            "Serverless architecture (simpler but less control)",
            "Monolithic architecture (simplest but less scalable)"
        ]
        
        trade_offs = [
            "Modular vs Microservices: Better maintainability vs increased complexity",
            "Performance vs Simplicity: Optimized code vs easier development",
            "Security vs Convenience: Strict controls vs user experience"
        ]
        
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
        
        return ImplementationReasoning(
            approach=approach,
            rationale=rationale,
            alternatives_considered=alternatives,
            trade_offs=trade_offs,
            best_practices_applied=best_practices,
            potential_issues=potential_issues,
            mitigation_strategies=mitigation_strategies
        )
    
    async def _generate_verification_criteria(self, requirements: Dict[str, Any]) -> VerificationCriteria:
        """Generate verification criteria for implementation"""
        
        functional_tests = [
            "All specified features work as described",
            "User interactions are smooth and intuitive",
            "Data validation works correctly",
            "Error handling provides meaningful feedback"
        ]
        
        integration_tests = [
            "Frontend-backend communication works correctly",
            "Database operations execute successfully",
            "External API integrations function properly",
            "Authentication flow works end-to-end"
        ]
        
        performance_criteria = [
            "Page load times under 3 seconds",
            "API response times under 500ms",
            "Database queries optimized",
            "Concurrent user handling works"
        ]
        
        security_checks = [
            "Input validation prevents injection attacks",
            "Authentication prevents unauthorized access",
            "HTTPS is enforced in production",
            "Sensitive data is properly encrypted"
        ]
        
        code_quality_metrics = [
            "Code coverage above 80%",
            "No critical security vulnerabilities",
            "Follows coding standards",
            "Documentation is complete"
        ]
        
        documentation_requirements = [
            "API documentation is complete and accurate",
            "User manual covers all features",
            "Deployment guide is clear",
            "Code comments explain complex logic"
        ]
        
        return VerificationCriteria(
            functional_tests=functional_tests,
            integration_tests=integration_tests,
            performance_criteria=performance_criteria,
            security_checks=security_checks,
            code_quality_metrics=code_quality_metrics,
            documentation_requirements=documentation_requirements
        )
    
    async def _generate_success_metrics(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate success metrics for the implementation"""
        return {
            "completion_percentage": 100,
            "test_coverage": 80,
            "performance_benchmarks": {
                "page_load_time": "< 3 seconds",
                "api_response_time": "< 500ms"
            },
            "security_score": 95,
            "code_quality_score": 85,
            "user_satisfaction": "high",
            "maintainability_index": "good"
        }
    
    async def _estimate_duration(self, phases: List[PlanPhase]) -> str:
        """Estimate total implementation duration"""
        total_hours = 0
        for phase in phases:
            # Parse duration estimates (simplified)
            duration_str = phase.estimated_duration
            if "hours" in duration_str:
                # Extract hours (simplified parsing)
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

class SpecDrivenPlanner:
    """Main spec-driven planner orchestrator"""
    
    def __init__(self, workspace_path: str = "."):
        self.plan_generator = PlanGenerator()
        self.workspace_path = workspace_path
    
    async def create_implementation_plan(self, requirements: str) -> ImplementationPlan:
        """Create complete implementation plan from requirements"""
        logger.info(f"Creating implementation plan for: {requirements[:100]}...")
        
        plan = await self.plan_generator.generate_plan(requirements, self.workspace_path)
        
        # Save plan to file
        await self._save_plan_to_file(plan)
        
        logger.info(f"Implementation plan created with ID: {plan.plan_id}")
        return plan
    
    async def _save_plan_to_file(self, plan: ImplementationPlan):
        """Save implementation plan to JSON file"""
        plan_dict = asdict(plan)
        
        # Convert datetime objects to strings
        plan_dict['created_at'] = plan.created_at.isoformat()
        
        for phase in plan_dict['phases']:
            # Handle any datetime objects in phases if needed
            pass
        
        plan_file = Path(self.workspace_path) / f"implementation_plan_{plan.plan_id}.json"
        with open(plan_file, 'w') as f:
            json.dump(plan_dict, f, indent=2, default=str)
        
        logger.info(f"Plan saved to: {plan_file}")

# Demonstration and testing
async def demo_spec_driven_planner():
    """Demonstrate the spec-driven planner functionality"""
    
    print("🚀 Spec-Driven Development Planner Demo")
    print("=" * 50)
    
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
    
    print(f"Requirements:\n{test_requirements}\n")
    
    try:
        # Generate implementation plan
        plan = await planner.create_implementation_plan(test_requirements)
        
        print(f"\n📋 Implementation Plan Generated")
        print(f"Plan ID: {plan.plan_id}")
        print(f"Complexity: {plan.complexity_level.value}")
        print(f"Phases: {len(plan.phases)}")
        print(f"Diagrams: {len(plan.diagrams)}")
        print(f"Estimated Duration: {plan.estimated_total_duration}")
        
        print(f"\n📊 Plan Summary:")
        for i, phase in enumerate(plan.phases, 1):
            print(f"{i}. {phase.phase_name} ({phase.estimated_duration})")
            print(f"   {phase.description}")
        
        print(f"\n🎯 Key Components:")
        for component in plan.reasoning.approach:
            print(f"- {component}")
        
        print(f"\n⚠️  Potential Issues:")
        for issue in plan.reasoning.potential_issues:
            print(f"- {issue}")
        
        print(f"\n✅ Verification Criteria:")
        for criterion in plan.verification_criteria.functional_tests[:3]:
            print(f"- {criterion}")
        
        # Display Mermaid diagrams
        if plan.diagrams:
            print(f"\n📈 Generated Diagrams:")
            for diagram in plan.diagrams:
                print(f"- {diagram.title}")
                print(f"  Type: {diagram.diagram_type}")
        
        return plan
        
    except Exception as e:
        print(f"❌ Error generating plan: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(demo_spec_driven_planner())