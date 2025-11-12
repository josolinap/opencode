#!/usr/bin/env python3
"""
Self-Evolving Skill System with Genetic Algorithms for Neo-Clone
Implements automatic skill evolution, adaptation, and optimization
"""

import asyncio
import numpy as np
import random
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import copy
from collections import defaultdict

logger = logging.getLogger(__name__)

class SkillType(Enum):
    """Types of skills in the evolution system"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    SOCIAL = "social"
    METACOGNITIVE = "metacognitive"
    EXECUTIVE = "executive"

class MutationType(Enum):
    """Types of genetic mutations"""
    POINT_MUTATION = "point_mutation"
    CROSSOVER = "crossover"
    INSERTION = "insertion"
    DELETION = "deletion"
    DUPLICATION = "duplication"
    INVERSION = "inversion"

@dataclass
class SkillGene:
    """Represents a single gene in a skill's DNA"""
    gene_id: str
    skill_type: SkillType
    capability: str
    proficiency: float  # 0.0 to 1.0
    efficiency: float   # Computational efficiency
    adaptability: float # Ability to adapt to new contexts
    complexity: float  # Complexity of the skill
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SkillDNA:
    """DNA sequence representing a complete skill"""
    skill_id: str
    name: str
    description: str
    genes: List[SkillGene]
    fitness_score: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutation_history: List[MutationType] = field(default_factory=list)
    performance_history: List[float] = field(default_factory=list)
    usage_count: int = 0
    success_rate: float = 0.0

@dataclass
class EvolutionPopulation:
    """Population of skills for evolution"""
    population: List[SkillDNA]
    generation: int
    population_size: int
    mutation_rate: float
    crossover_rate: float
    elitism_rate: float
    diversity_threshold: float

class GeneticSkillEvolver:
    """Genetic algorithm-based skill evolution system"""
    
    def __init__(self, population_size: int = 50, mutation_rate: float = 0.1, 
                 crossover_rate: float = 0.7, elitism_rate: float = 0.2):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_rate = elitism_rate
        self.diversity_threshold = 0.3
        
        self.current_population = None
        self.evolution_history = []
        self.best_skills = {}
        self.skill_ecosystem = {}
        self.evolution_metrics = {
            'generations': 0,
            'total_mutations': 0,
            'successful_crossovers': 0,
            'fitness_improvements': 0,
            'diversity_score': 0.0
        }
        
    def initialize_population(self, initial_skills: List[Dict[str, Any]]) -> EvolutionPopulation:
        """Initialize the evolution population with seed skills"""
        population = []
        
        for i, skill_data in enumerate(initial_skills):
            # Create DNA for initial skill
            genes = []
            
            # Generate genes based on skill type and capabilities
            skill_type = SkillType(skill_data.get('type', 'analytical'))
            capabilities = skill_data.get('capabilities', [])
            
            for j, capability in enumerate(capabilities):
                gene = SkillGene(
                    gene_id=f"{skill_data['id']}_gene_{j}",
                    skill_type=skill_type,
                    capability=capability,
                    proficiency=random.uniform(0.3, 0.8),
                    efficiency=random.uniform(0.5, 0.9),
                    adaptability=random.uniform(0.4, 0.8),
                    complexity=random.uniform(0.2, 0.7),
                    dependencies=random.sample(capabilities[:j], min(j, 2))
                )
                genes.append(gene)
            
            dna = SkillDNA(
                skill_id=skill_data['id'],
                name=skill_data['name'],
                description=skill_data.get('description', ''),
                genes=genes,
                generation=0,
                fitness_score=self._calculate_fitness(genes)
            )
            
            population.append(dna)
        
        # Fill remaining population with variations
        while len(population) < self.population_size:
            # Create variation of existing skill
            parent = random.choice(population[:len(initial_skills)])
            variant = self._create_variant(parent, len(population))
            population.append(variant)
        
        self.current_population = EvolutionPopulation(
            population=population,
            generation=0,
            population_size=self.population_size,
            mutation_rate=self.mutation_rate,
            crossover_rate=self.crossover_rate,
            elitism_rate=self.elitism_rate,
            diversity_threshold=self.diversity_threshold
        )
        
        logger.info(f"Initialized evolution population with {len(population)} skills")
        return self.current_population
    
    def evolve_generation(self, performance_feedback: Dict[str, float]) -> EvolutionPopulation:
        """Evolve the population by one generation"""
        if not self.current_population:
            raise ValueError("Population not initialized")
        
        # Update fitness based on performance feedback
        self._update_fitness(performance_feedback)
        
        # Selection
        selected = self._selection()
        
        # Crossover and mutation
        offspring = self._crossover_and_mutation(selected)
        
        # Create new generation
        new_population = self._create_new_generation(offspring)
        
        # Update population
        self.current_population = new_population
        self.evolution_metrics['generations'] += 1
        
        # Record evolution
        self._record_evolution()
        
        logger.info(f"Evolved to generation {new_population.generation} with {len(new_population.population)} skills")
        return new_population
    
    def _calculate_fitness(self, genes: List[SkillGene]) -> float:
        """Calculate fitness score for a set of genes"""
        if not genes:
            return 0.0
        
        # Base fitness from gene proficiencies
        proficiency_score = np.mean([g.proficiency for g in genes])
        
        # Efficiency bonus
        efficiency_score = np.mean([g.efficiency for g in genes])
        
        # Adaptability bonus
        adaptability_score = np.mean([g.adaptability for g in genes])
        
        # Complexity penalty (too complex is bad)
        complexity_penalty = np.mean([g.complexity for g in genes]) * 0.2
        
        # Gene diversity bonus
        capability_diversity = len(set(g.capability for g in genes)) / len(genes) if genes else 0
        
        # Combined fitness
        fitness = (
            0.4 * proficiency_score +
            0.2 * efficiency_score +
            0.2 * adaptability_score +
            0.1 * capability_diversity -
            complexity_penalty
        )
        
        return max(0.0, min(1.0, float(fitness)))
    
    def _update_fitness(self, performance_feedback: Dict[str, float]):
        """Update fitness scores based on performance feedback"""
        if not self.current_population:
            return
            
        for skill_dna in self.current_population.population:
            skill_id = skill_dna.skill_id
            
            if skill_id in performance_feedback:
                performance = performance_feedback[skill_id]
                skill_dna.performance_history.append(performance)
                
                # Update success rate
                if len(skill_dna.performance_history) > 0:
                    skill_dna.success_rate = float(np.mean(skill_dna.performance_history[-10:]))  # Last 10 performances
                
                # Combine genetic fitness with performance
                genetic_fitness = skill_dna.fitness_score
                performance_fitness = skill_dna.success_rate
                
                # Weighted combination (performance more important)
                skill_dna.fitness_score = 0.3 * genetic_fitness + 0.7 * performance_fitness
    
    def _selection(self) -> List[SkillDNA]:
        """Select parents for next generation using tournament selection"""
        if not self.current_population:
            return []
            
        population = self.current_population.population
        selected = []
        
        # Elitism: keep best performers
        elite_count = int(len(population) * self.elitism_rate)
        elite = sorted(population, key=lambda x: x.fitness_score, reverse=True)[:elite_count]
        selected.extend(elite)
        
        # Tournament selection for remaining spots
        tournament_size = 3
        while len(selected) < len(population):
            tournament = random.sample(population, tournament_size)
            winner = max(tournament, key=lambda x: x.fitness_score)
            selected.append(winner)
        
        return selected
    
    def _crossover_and_mutation(self, selected: List[SkillDNA]) -> List[SkillDNA]:
        """Perform crossover and mutation to create offspring"""
        offspring = []
        
        # Keep elite individuals unchanged
        elite_count = int(len(selected) * self.elitism_rate)
        elite = sorted(selected, key=lambda x: x.fitness_score, reverse=True)[:elite_count]
        offspring.extend(elite)
        
        # Create offspring through crossover
        while len(offspring) < self.population_size:
            if random.random() < self.crossover_rate and len(selected) >= 2:
                # Crossover
                parent1, parent2 = random.sample(selected, 2)
                child = self._crossover(parent1, parent2)
                self.evolution_metrics['successful_crossovers'] += 1
            else:
                # Clone with mutation
                parent = random.choice(selected)
                child = self._mutate(copy.deepcopy(parent))
            
            offspring.append(child)
        
        return offspring[:self.population_size]
    
    def _crossover(self, parent1: SkillDNA, parent2: SkillDNA) -> SkillDNA:
        """Perform crossover between two parent skills"""
        # Single-point crossover on genes
        genes1, genes2 = parent1.genes, parent2.genes
        
        # Ensure both parents have genes
        if not genes1 or not genes2:
            return copy.deepcopy(parent1 if genes1 else parent2)
        
        # Crossover point
        max_point = min(len(genes1), len(genes2))
        if max_point <= 1:
            return copy.deepcopy(parent1)
        
        crossover_point = random.randint(1, max_point - 1)
        
        # Create child genes
        child_genes = genes1[:crossover_point] + genes2[crossover_point:]
        
        # Ensure unique gene IDs
        for i, gene in enumerate(child_genes):
            gene.gene_id = f"child_{int(time.time())}_{i}"
        
        # Create child DNA
        child = SkillDNA(
            skill_id=f"evolved_{int(time.time())}_{random.randint(1000, 9999)}",
            name=f"Evolved {parent1.name} + {parent2.name}",
            description=f"Crossover of {parent1.name} and {parent2.name}",
            genes=child_genes,
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.skill_id, parent2.skill_id],
            mutation_history=[MutationType.CROSSOVER]
        )
        
        child.fitness_score = self._calculate_fitness(child_genes)
        return child
    
    def _mutate(self, individual: SkillDNA) -> SkillDNA:
        """Apply mutations to an individual"""
        if not individual.genes:
            return individual
        
        # Decide mutation type
        mutation_types = list(MutationType)
        mutation_type = random.choice(mutation_types)
        
        if mutation_type == MutationType.POINT_MUTATION:
            self._point_mutation(individual)
        elif mutation_type == MutationType.INSERTION:
            self._insertion_mutation(individual)
        elif mutation_type == MutationType.DELETION:
            self._deletion_mutation(individual)
        elif mutation_type == MutationType.DUPLICATION:
            self._duplication_mutation(individual)
        elif mutation_type == MutationType.INVERSION:
            self._inversion_mutation(individual)
        
        individual.mutation_history.append(mutation_type)
        individual.generation += 1
        individual.fitness_score = self._calculate_fitness(individual.genes)
        
        self.evolution_metrics['total_mutations'] += 1
        return individual
    
    def _point_mutation(self, individual: SkillDNA):
        """Point mutation: modify random gene attributes"""
        if not individual.genes:
            return
        
        gene = random.choice(individual.genes)
        
        # Mutate random attribute
        attributes = ['proficiency', 'efficiency', 'adaptability', 'complexity']
        attribute = random.choice(attributes)
        
        # Small random change
        current_value = getattr(gene, attribute)
        mutation = random.uniform(-0.1, 0.1)
        new_value = max(0.0, min(1.0, current_value + mutation))
        setattr(gene, attribute, new_value)
    
    def _insertion_mutation(self, individual: SkillDNA):
        """Insertion mutation: add new gene"""
        if len(individual.genes) >= 10:  # Limit gene count
            return
        
        # Create new gene
        new_gene = SkillGene(
            gene_id=f"inserted_{int(time.time())}",
            skill_type=random.choice(list(SkillType)),
            capability=f"new_capability_{random.randint(100, 999)}",
            proficiency=random.uniform(0.3, 0.8),
            efficiency=random.uniform(0.5, 0.9),
            adaptability=random.uniform(0.4, 0.8),
            complexity=random.uniform(0.2, 0.7)
        )
        
        # Insert at random position
        position = random.randint(0, len(individual.genes))
        individual.genes.insert(position, new_gene)
    
    def _deletion_mutation(self, individual: SkillDNA):
        """Deletion mutation: remove random gene"""
        if len(individual.genes) <= 1:  # Keep at least one gene
            return
        
        individual.genes.pop(random.randint(0, len(individual.genes) - 1))
    
    def _duplication_mutation(self, individual: SkillDNA):
        """Duplication mutation: duplicate random gene"""
        if len(individual.genes) >= 10:  # Limit gene count
            return
        
        gene_to_duplicate = random.choice(individual.genes)
        duplicated_gene = copy.deepcopy(gene_to_duplicate)
        duplicated_gene.gene_id = f"duplicated_{int(time.time())}"
        
        # Insert after original
        index = individual.genes.index(gene_to_duplicate)
        individual.genes.insert(index + 1, duplicated_gene)
    
    def _inversion_mutation(self, individual: SkillDNA):
        """Inversion mutation: reverse gene sequence"""
        if len(individual.genes) < 2:
            return
        
        # Select random segment to invert
        start = random.randint(0, len(individual.genes) - 2)
        end = random.randint(start + 1, len(individual.genes) - 1)
        
        # Invert segment
        individual.genes[start:end+1] = individual.genes[start:end+1][::-1]
    
    def _create_variant(self, parent: SkillDNA, variant_id: int) -> SkillDNA:
        """Create a variant of an existing skill"""
        variant_genes = []
        
        for gene in parent.genes:
            variant_gene = copy.deepcopy(gene)
            variant_gene.gene_id = f"{variant_id}_{gene.gene_id}"
            
            # Small random variations
            variant_gene.proficiency = max(0.0, min(1.0, 
                variant_gene.proficiency + random.uniform(-0.2, 0.2)))
            variant_gene.efficiency = max(0.0, min(1.0, 
                variant_gene.efficiency + random.uniform(-0.1, 0.1)))
            variant_gene.adaptability = max(0.0, min(1.0, 
                variant_gene.adaptability + random.uniform(-0.1, 0.1)))
            
            variant_genes.append(variant_gene)
        
        variant = SkillDNA(
            skill_id=f"variant_{variant_id}_{int(time.time())}",
            name=f"Variant of {parent.name}",
            description=f"Generated variant of {parent.name}",
            genes=variant_genes,
            generation=0,
            parent_ids=[parent.skill_id],
            mutation_history=[MutationType.POINT_MUTATION]
        )
        
        variant.fitness_score = self._calculate_fitness(variant_genes)
        return variant
    
    def _create_new_generation(self, offspring: List[SkillDNA]) -> EvolutionPopulation:
        """Create the new generation population"""
        if not self.current_population:
            # Create new population if none exists
            return EvolutionPopulation(
                population=offspring[:self.population_size],
                generation=0,
                population_size=self.population_size,
                mutation_rate=self.mutation_rate,
                crossover_rate=self.crossover_rate,
                elitism_rate=self.elitism_rate,
                diversity_threshold=self.diversity_threshold
            )
        
        # Sort by fitness
        offspring.sort(key=lambda x: x.fitness_score, reverse=True)
        
        # Trim to population size
        offspring = offspring[:self.population_size]
        
        # Update generation numbers
        for individual in offspring:
            individual.generation = self.current_population.generation + 1
        
        return EvolutionPopulation(
            population=offspring,
            generation=self.current_population.generation + 1,
            population_size=self.population_size,
            mutation_rate=self.mutation_rate,
            crossover_rate=self.crossover_rate,
            elitism_rate=self.elitism_rate,
            diversity_threshold=self.diversity_threshold
        )
    
    def _record_evolution(self):
        """Record evolution metrics and history"""
        if not self.current_population:
            return
            
        population = self.current_population.population
        
        # Calculate diversity
        diversity_score = self._calculate_diversity(population)
        self.evolution_metrics['diversity_score'] = diversity_score
        
        # Track best skills
        best_skill = max(population, key=lambda x: x.fitness_score)
        self.best_skills[self.current_population.generation] = best_skill
        
        # Record generation data
        generation_data = {
            'generation': self.current_population.generation,
            'best_fitness': best_skill.fitness_score,
            'average_fitness': float(np.mean([s.fitness_score for s in population])),
            'diversity_score': diversity_score,
            'population_size': len(population),
            'mutations': self.evolution_metrics['total_mutations'],
            'crossovers': self.evolution_metrics['successful_crossovers']
        }
        
        self.evolution_history.append(generation_data)
        
        # Limit history size
        if len(self.evolution_history) > 1000:
            self.evolution_history = self.evolution_history[-800:]
    
    def _calculate_diversity(self, population: List[SkillDNA]) -> float:
        """Calculate genetic diversity in the population"""
        if len(population) < 2:
            return 0.0
        
        # Calculate diversity based on gene differences
        total_diversity = 0.0
        comparisons = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                diversity = self._calculate_individual_diversity(population[i], population[j])
                total_diversity += diversity
                comparisons += 1
        
        return total_diversity / comparisons if comparisons > 0 else 0.0
    
    def _calculate_individual_diversity(self, individual1: SkillDNA, individual2: SkillDNA) -> float:
        """Calculate diversity between two individuals"""
        genes1, genes2 = individual1.genes, individual2.genes
        
        if not genes1 or not genes2:
            return 1.0
        
        # Capability diversity
        capabilities1 = set(g.capability for g in genes1)
        capabilities2 = set(g.capability for g in genes2)
        
        if not capabilities1 and not capabilities2:
            return 0.0
        
        intersection = capabilities1.intersection(capabilities2)
        union = capabilities1.union(capabilities2)
        
        capability_diversity = 1.0 - (len(intersection) / len(union)) if union else 0.0
        
        # Proficiency diversity
        proficiencies1 = [g.proficiency for g in genes1]
        proficiencies2 = [g.proficiency for g in genes2]
        
        proficiency_diversity = abs(np.mean(proficiencies1) - np.mean(proficiencies2)) if proficiencies1 and proficiencies2 else 0.0
        
        # Combined diversity
        return float(0.7 * capability_diversity + 0.3 * proficiency_diversity)
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """Generate comprehensive evolution report"""
        if not self.current_population:
            return {'status': 'no_population'}
        
        population = self.current_population.population
        
        return {
            'current_generation': self.current_population.generation,
            'population_size': len(population),
            'best_fitness': max(s.fitness_score for s in population),
            'average_fitness': np.mean([s.fitness_score for s in population]),
            'diversity_score': self.evolution_metrics['diversity_score'],
            'total_generations': self.evolution_metrics['generations'],
            'total_mutations': self.evolution_metrics['total_mutations'],
            'successful_crossovers': self.evolution_metrics['successful_crossovers'],
            'fitness_improvements': self.evolution_metrics['fitness_improvements'],
            'evolution_trend': self._calculate_evolution_trend(),
            'best_skill': self._get_best_skill_info(),
            'skill_ecosystem': self._analyze_skill_ecosystem()
        }
    
    def _calculate_evolution_trend(self) -> str:
        """Calculate the trend of evolution over recent generations"""
        if len(self.evolution_history) < 3:
            return "insufficient_data"
        
        recent = self.evolution_history[-5:]  # Last 5 generations
        fitnesses = [g['best_fitness'] for g in recent]
        
        # Simple trend analysis
        if len(fitnesses) < 2:
            return "stable"
        
        # Calculate slope
        x = list(range(len(fitnesses)))
        y = fitnesses
        n = len(fitnesses)
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if (n * sum_x2 - sum_x ** 2) != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        else:
            slope = 0.0
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _get_best_skill_info(self) -> Dict[str, Any]:
        """Get information about the best skill"""
        if not self.current_population:
            return {}
        
        best_skill = max(self.current_population.population, key=lambda x: x.fitness_score)
        
        return {
            'skill_id': best_skill.skill_id,
            'name': best_skill.name,
            'fitness': best_skill.fitness_score,
            'generation': best_skill.generation,
            'gene_count': len(best_skill.genes),
            'success_rate': best_skill.success_rate,
            'mutation_count': len(best_skill.mutation_history),
            'capabilities': [g.capability for g in best_skill.genes]
        }
    
    def _analyze_skill_ecosystem(self) -> Dict[str, Any]:
        """Analyze the skill ecosystem diversity and distribution"""
        if not self.current_population:
            return {}
        
        population = self.current_population.population
        
        # Skill type distribution
        type_counts = defaultdict(int)
        capability_counts = defaultdict(int)
        
        for skill in population:
            for gene in skill.genes:
                type_counts[gene.skill_type.value] += 1
                capability_counts[gene.capability] += 1
        
        # Complexity distribution
        complexities = [g.complexity for skill in population for g in skill.genes]
        
        return {
            'skill_types': dict(type_counts),
            'capability_diversity': len(capability_counts),
            'most_common_capabilities': sorted(capability_counts.items(), 
                                            key=lambda x: x[1], reverse=True)[:10],
            'average_complexity': np.mean(complexities) if complexities else 0.0,
            'complexity_range': (min(complexities), max(complexities)) if complexities else (0.0, 0.0)
        }

class SkillEvolutionManager:
    """Manager for the skill evolution system"""
    
    def __init__(self):
        self.evolver = GeneticSkillEvolver()
        self.performance_tracker = {}
        self.evolution_active = False
        self.evolution_interval = 100  # Evolve every 100 skill uses
        self.skill_usage_count = 0
        
    def initialize_skills(self, initial_skills: List[Dict[str, Any]]):
        """Initialize the skill evolution system"""
        self.evolver.initialize_population(initial_skills)
        logger.info("Skill evolution system initialized")
    
    def record_skill_performance(self, skill_id: str, performance: float):
        """Record performance of a skill execution"""
        if skill_id not in self.performance_tracker:
            self.performance_tracker[skill_id] = []
        
        self.performance_tracker[skill_id].append(performance)
        self.skill_usage_count += 1
        
        # Trigger evolution if needed
        if self.skill_usage_count >= self.evolution_interval:
            self.trigger_evolution()
            self.skill_usage_count = 0
    
    def trigger_evolution(self):
        """Trigger an evolution cycle"""
        if not self.evolver.current_population:
            return
        
        # Prepare performance feedback
        performance_feedback = {}
        for skill_id, performances in self.performance_tracker.items():
            if performances:
                performance_feedback[skill_id] = np.mean(performances[-10:])  # Last 10 performances
        
        # Evolve generation
        new_population = self.evolver.evolve_generation(performance_feedback)
        
        logger.info(f"Evolution cycle completed. Generation {new_population.generation}")
        
        # Clear old performance data
        self.performance_tracker.clear()
    
    def get_best_skills(self, count: int = 5) -> List[SkillDNA]:
        """Get the best performing skills"""
        if not self.evolver.current_population:
            return []
        
        population = self.evolver.current_population.population
        return sorted(population, key=lambda x: x.fitness_score, reverse=True)[:count]
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution status"""
        return self.evolver.get_evolution_report()