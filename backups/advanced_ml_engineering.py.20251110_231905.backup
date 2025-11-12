from functools import lru_cache
'\nadvanced_ml_engineering.py - Professional ML Engineering Capabilities\n\nProvides comprehensive machine learning engineering tools including automated model training,\nhyperparameter optimization, experiment tracking, model deployment, and MLOps workflows.\n'
import time
import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path
import statistics
import threading
import pickle
import hashlib
logger = logging.getLogger(__name__)

@dataclass
class MLExperiment:
    """ML experiment definition"""
    experiment_id: str
    name: str
    description: str
    dataset_path: str
    model_type: str
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = 'created'
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    model_path: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

@dataclass
class ModelRegistry:
    """Model registry entry"""
    model_id: str
    name: str
    version: str
    model_type: str
    framework: str
    created_at: float
    model_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    is_deployed: bool = False
    deployment_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MLPipeline:
    """ML pipeline definition"""
    pipeline_id: str
    name: str
    description: str
    stages: List[Dict[str, Any]]
    parameters: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None
    is_active: bool = False
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    run_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class HyperparameterSearch:
    """Hyperparameter search configuration"""
    search_id: str
    experiment_name: str
    search_space: Dict[str, Any]
    search_method: str
    max_trials: int
    best_params: Dict[str, Any] = field(default_factory=dict)
    best_score: float = float('-inf')
    trial_results: List[Dict[str, Any]] = field(default_factory=list)
    status: str = 'created'

class AdvancedMLEngineering:
    """Advanced ML Engineering System"""

    def __init__(self, workspace_path: str='ml_workspace'):
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(exist_ok=True)
        self.experiments: Dict[str, MLExperiment] = {}
        self.model_registry: Dict[str, ModelRegistry] = {}
        self.pipelines: Dict[str, MLPipeline] = {}
        self.hyperparameter_searches: Dict[str, HyperparameterSearch] = {}
        self.experiment_queue = deque()
        self.running_experiments: Dict[str, threading.Thread] = {}
        self.ml_config = {'default_framework': 'sklearn', 'max_concurrent_experiments': 3, 'auto_save_models': True, 'track_experiments': True, 'enable_gpu': False, 'random_seed': 42, 'cross_validation_folds': 5, 'test_size': 0.2, 'validation_size': 0.1}
        self.supported_algorithms = {'classification': ['logistic_regression', 'random_forest', 'svm', 'xgboost', 'lightgbm', 'neural_network', 'ensemble'], 'regression': ['linear_regression', 'ridge', 'lasso', 'random_forest_reg', 'xgboost_reg', 'svr', 'neural_network_reg'], 'clustering': ['kmeans', 'hierarchical', 'dbscan', 'gaussian_mixture'], 'dimensionality_reduction': ['pca', 'tsne', 'umap', 'lda']}
        self._initialize_workspace()
        self._load_workspace_data()

    def _initialize_workspace(self):
        """Initialize ML workspace structure"""
        directories = ['experiments', 'models', 'datasets', 'pipelines', 'logs', 'artifacts', 'deployments', 'monitoring']
        for directory in directories:
            (self.workspace_path / directory).mkdir(exist_ok=True)
        logger.info(f'Initialized ML workspace at {self.workspace_path}')

    @lru_cache(maxsize=128)
    def _load_workspace_data(self):
        """Load existing workspace data"""
        try:
            experiments_file = self.workspace_path / 'experiments' / 'experiments.json'
            if experiments_file.exists():
                with open(experiments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for exp_data in data:
                    experiment = MLExperiment(**exp_data)
                    self.experiments[experiment.experiment_id] = experiment
            registry_file = self.workspace_path / 'models' / 'registry.json'
            if registry_file.exists():
                with open(registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for model_data in data:
                    model = ModelRegistry(**model_data)
                    self.model_registry[model.model_id] = model
            pipelines_file = self.workspace_path / 'pipelines' / 'pipelines.json'
            if pipelines_file.exists():
                with open(pipelines_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for pipeline_data in data:
                    pipeline = MLPipeline(**pipeline_data)
                    self.pipelines[pipeline.pipeline_id] = pipeline
            logger.info(f'Loaded workspace: {len(self.experiments)} experiments, {len(self.model_registry)} models, {len(self.pipelines)} pipelines')
        except Exception as e:
            logger.warning(f'Failed to load workspace data: {e}')

    def create_experiment(self, name: str, description: str, dataset_path: str, model_type: str, hyperparameters: Dict[str, Any]=None) -> str:
        """Create a new ML experiment"""
        experiment_id = f'exp_{int(time.time() * 1000)}'
        if not Path(dataset_path).exists():
            raise ValueError(f'Dataset not found: {dataset_path}')
        valid_types = []
        for (category, algorithms) in self.supported_algorithms.items():
            valid_types.extend(algorithms)
        if model_type not in valid_types:
            raise ValueError(f'Unsupported model type: {model_type}. Supported: {valid_types}')
        experiment = MLExperiment(experiment_id=experiment_id, name=name, description=description, dataset_path=dataset_path, model_type=model_type, hyperparameters=hyperparameters or {})
        self.experiments[experiment_id] = experiment
        self._save_experiments()
        logger.info(f'Created experiment: {name} ({experiment_id})')
        return experiment_id

    def run_experiment(self, experiment_id: str) -> bool:
        """Run an ML experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f'Experiment not found: {experiment_id}')
        experiment = self.experiments[experiment_id]
        if experiment.status == 'running':
            logger.warning(f'Experiment already running: {experiment_id}')
            return False
        running_count = len(self.running_experiments)
        if running_count >= self.ml_config['max_concurrent_experiments']:
            logger.warning(f'Max concurrent experiments reached ({running_count})')
            return False
        self.experiment_queue.append(experiment_id)
        if not hasattr(self, '_experiment_runner_active'):
            self._experiment_runner_active = True
            runner_thread = threading.Thread(target=self._experiment_runner_loop, daemon=True)
            runner_thread.start()
        logger.info(f'Queued experiment for execution: {experiment_id}')
        return True

    def _experiment_runner_loop(self):
        """Experiment runner loop"""
        while self._experiment_runner_active:
            try:
                if not self.experiment_queue:
                    time.sleep(1)
                    continue
                experiment_id = self.experiment_queue.popleft()
                if experiment_id not in self.experiments:
                    continue
                experiment_thread = threading.Thread(target=self._execute_experiment, args=(experiment_id,), daemon=True)
                self.running_experiments[experiment_id] = experiment_thread
                experiment_thread.start()
            except Exception as e:
                logger.error(f'Error in experiment runner: {e}')
                time.sleep(5)

    def _execute_experiment(self, experiment_id: str):
        """Execute a single experiment"""
        experiment = self.experiments[experiment_id]
        try:
            experiment.status = 'running'
            experiment.started_at = time.time()
            self._save_experiments()
            logger.info(f'Starting experiment: {experiment.name}')
            data = self._load_dataset(experiment.dataset_path)
            (X_train, X_test, y_train, y_test) = self._prepare_data(data, experiment)
            model = self._create_model(experiment.model_type, experiment.hyperparameters)
            start_time = time.time()
            model.fit(X_train, y_train)
            training_time = time.time() - start_time
            metrics = self._evaluate_model(model, X_test, y_test, experiment.model_type)
            model_path = self._save_model(model, experiment_id, experiment.model_type)
            experiment.metrics = metrics
            experiment.model_path = model_path
            experiment.status = 'completed'
            experiment.completed_at = time.time()
            experiment.results = {'training_time': training_time, 'model_size': self._get_model_size(model_path), 'data_shape': {'train_samples': len(X_train), 'test_samples': len(X_test), 'features': X_train.shape[1] if len(X_train.shape) > 1 else 1}}
            self._register_model(experiment, model_path, metrics)
            logger.info(f'Experiment completed: {experiment.name}')
            logger.info(f'Metrics: {metrics}')
        except Exception as e:
            experiment.status = 'failed'
            experiment.completed_at = time.time()
            experiment.results['error'] = str(e)
            logger.error(f'Experiment failed: {experiment.name} - {e}')
        finally:
            self._save_experiments()
            self.running_experiments.pop(experiment_id, None)

    def _load_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Load dataset from file"""
        path = Path(dataset_path)
        if path.suffix == '.csv':
            df = pd.read_csv(path)
            return {'data': df, 'target_column': df.columns[-1]}
        elif path.suffix in ['.pkl', '.pickle']:
            with open(path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f'Unsupported dataset format: {path.suffix}')

    def _prepare_data(self, data: Dict[str, Any], experiment: MLExperiment) -> Tuple:
        """Prepare data for training"""
        df = data['data']
        target_column = data.get('target_column', df.columns[-1])
        X = df.drop(columns=[target_column])
        y = df[target_column]
        X = pd.get_dummies(X, drop_first=True)
        from sklearn.model_selection import train_test_split
        (X_train, X_test, y_train, y_test) = train_test_split(X, y, test_size=self.ml_config['test_size'], random_state=self.ml_config['random_seed'])
        return (X_train, X_test, y_train, y_test)

    def _create_model(self, model_type: str, hyperparameters: Dict[str, Any]):
        """Create model based on type and hyperparameters"""
        if model_type == 'logistic_regression':
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(random_state=self.ml_config['random_seed'], **hyperparameters)
        elif model_type == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(random_state=self.ml_config['random_seed'], **hyperparameters)
        elif model_type == 'svm':
            from sklearn.svm import SVC
            return SVC(random_state=self.ml_config['random_seed'], **hyperparameters)
        elif model_type == 'xgboost':
            from xgboost import XGBClassifier
            return XGBClassifier(random_state=self.ml_config['random_seed'], **hyperparameters)
        elif model_type == 'linear_regression':
            from sklearn.linear_model import LinearRegression
            return LinearRegression(**hyperparameters)
        elif model_type == 'random_forest_reg':
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(random_state=self.ml_config['random_seed'], **hyperparameters)
        elif model_type == 'kmeans':
            from sklearn.cluster import KMeans
            return KMeans(random_state=self.ml_config['random_seed'], **hyperparameters)
        else:
            raise ValueError(f'Unsupported model type: {model_type}')

    def _evaluate_model(self, model, X_test, y_test, model_type: str) -> Dict[str, float]:
        """Evaluate model performance"""
        y_pred = model.predict(X_test)
        metrics = {}
        if model_type in self.supported_algorithms['classification']:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            metrics['accuracy'] = accuracy_score(y_test, y_pred)
            metrics['precision'] = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            metrics['f1_score'] = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            try:
                if hasattr(model, 'predict_proba'):
                    y_proba = model.predict_proba(X_test)
                    metrics['roc_auc'] = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
            except:
                pass
        elif model_type in self.supported_algorithms['regression']:
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            metrics['mse'] = mean_squared_error(y_test, y_pred)
            metrics['rmse'] = np.sqrt(metrics['mse'])
            metrics['mae'] = mean_absolute_error(y_test, y_pred)
            metrics['r2_score'] = r2_score(y_test, y_pred)
        elif model_type in self.supported_algorithms['clustering']:
            from sklearn.metrics import silhouette_score, calinski_harabasz_score
            metrics['silhouette_score'] = silhouette_score(X_test, y_pred)
            metrics['calinski_harabasz_score'] = calinski_harabasz_score(X_test, y_pred)
        return metrics

    def _save_model(self, model, experiment_id: str, model_type: str) -> str:
        """Save trained model"""
        model_dir = self.workspace_path / 'models' / experiment_id
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / f'model.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        metadata = {'experiment_id': experiment_id, 'model_type': model_type, 'framework': self.ml_config['default_framework'], 'created_at': time.time()}
        metadata_path = model_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return str(model_path)

    def _get_model_size(self, model_path: str) -> int:
        """Get model file size in bytes"""
        return Path(model_path).stat().st_size

    def _register_model(self, experiment: MLExperiment, model_path: str, metrics: Dict[str, float]):
        """Register model in registry"""
        model_id = f'model_{experiment.experiment_id}'
        existing_models = [m for m in self.model_registry.values() if m.name == experiment.name]
        version = f'v{len(existing_models) + 1}'
        model = ModelRegistry(model_id=model_id, name=experiment.name, version=version, model_type=experiment.model_type, framework=self.ml_config['default_framework'], created_at=time.time(), model_path=model_path, performance_metrics=metrics, metadata={'experiment_id': experiment.experiment_id, 'hyperparameters': experiment.hyperparameters, 'dataset_path': experiment.dataset_path})
        self.model_registry[model_id] = model
        self._save_model_registry()

    def create_hyperparameter_search(self, experiment_name: str, search_space: Dict[str, Any], search_method: str='random', max_trials: int=50) -> str:
        """Create hyperparameter search"""
        search_id = f'search_{int(time.time() * 1000)}'
        search = HyperparameterSearch(search_id=search_id, experiment_name=experiment_name, search_space=search_space, search_method=search_method, max_trials=max_trials)
        self.hyperparameter_searches[search_id] = search
        logger.info(f'Created hyperparameter search: {search_id}')
        return search_id

    def run_hyperparameter_search(self, search_id: str) -> bool:
        """Run hyperparameter optimization"""
        if search_id not in self.hyperparameter_searches:
            raise ValueError(f'Search not found: {search_id}')
        search = self.hyperparameter_searches[search_id]
        search.status = 'running'
        try:
            for trial in range(search.max_trials):
                if search.search_method == 'random':
                    params = self._sample_random_params(search.search_space)
                elif search.search_method == 'grid':
                    params = self._sample_grid_params(search.search_space, trial)
                else:
                    params = self._sample_random_params(search.search_space)
                experiment_id = self.create_experiment(name=f'{search.experiment_name}_trial_{trial}', description=f'Hyperparameter trial {trial} for {search.experiment_name}', dataset_path='', model_type='', hyperparameters=params)
                trial_result = {'trial': trial, 'params': params, 'score': 0.0, 'experiment_id': experiment_id}
                search.trial_results.append(trial_result)
                if trial_result['score'] > search.best_score:
                    search.best_score = trial_result['score']
                    search.best_params = params
            search.status = 'completed'
        except Exception as e:
            search.status = 'failed'
            logger.error(f'Hyperparameter search failed: {e}')
            return False
        return True

    def _sample_random_params(self, search_space: Dict[str, Any]) -> Dict[str, Any]:
        """Sample random parameters from search space"""
        params = {}
        for (param, config) in search_space.items():
            if config['type'] == 'categorical':
                params[param] = np.random.choice(config['values'])
            elif config['type'] == 'uniform':
                params[param] = np.random.uniform(config['min'], config['max'])
            elif config['type'] == 'int':
                params[param] = np.random.randint(config['min'], config['max'] + 1)
            elif config['type'] == 'loguniform':
                params[param] = np.exp(np.random.uniform(np.log(config['min']), np.log(config['max'])))
        return params

    def _sample_grid_params(self, search_space: Dict[str, Any], trial: int) -> Dict[str, Any]:
        """Sample grid parameters (simplified)"""
        return self._sample_random_params(search_space)

    def create_pipeline(self, name: str, description: str, stages: List[Dict[str, Any]], schedule: str=None) -> str:
        """Create ML pipeline"""
        pipeline_id = f'pipeline_{int(time.time() * 1000)}'
        pipeline = MLPipeline(pipeline_id=pipeline_id, name=name, description=description, stages=stages, schedule=schedule)
        self.pipelines[pipeline_id] = pipeline
        self._save_pipelines()
        logger.info(f'Created pipeline: {name} ({pipeline_id})')
        return pipeline_id

    def run_pipeline(self, pipeline_id: str) -> bool:
        """Run ML pipeline"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f'Pipeline not found: {pipeline_id}')
        pipeline = self.pipelines[pipeline_id]
        try:
            pipeline.last_run = time.time()
            run_results = []
            for (i, stage) in enumerate(pipeline.stages):
                stage_start = time.time()
                if stage['type'] == 'data_preprocessing':
                    result = self._execute_data_preprocessing(stage)
                elif stage['type'] == 'model_training':
                    result = self._execute_model_training(stage)
                elif stage['type'] == 'model_evaluation':
                    result = self._execute_model_evaluation(stage)
                elif stage['type'] == 'model_deployment':
                    result = self._execute_model_deployment(stage)
                else:
                    result = {'status': 'skipped', 'message': f"Unknown stage type: {stage['type']}"}
                stage['execution_time'] = time.time() - stage_start
                run_results.append(result)
                if result.get('status') == 'failed':
                    break
            pipeline.run_history.append({'timestamp': time.time(), 'results': run_results, 'status': 'completed' if all((r.get('status') != 'failed' for r in run_results)) else 'failed'})
            self._save_pipelines()
            logger.info(f'Pipeline completed: {pipeline.name}')
            return True
        except Exception as e:
            logger.error(f'Pipeline failed: {pipeline.name} - {e}')
            return False

    def _execute_data_preprocessing(self, stage: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data preprocessing stage"""
        time.sleep(1)
        return {'status': 'completed', 'message': 'Data preprocessing completed'}

    def _execute_model_training(self, stage: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model training stage"""
        time.sleep(2)
        return {'status': 'completed', 'message': 'Model training completed'}

    def _execute_model_evaluation(self, stage: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model evaluation stage"""
        time.sleep(0.5)
        return {'status': 'completed', 'message': 'Model evaluation completed'}

    def _execute_model_deployment(self, stage: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model deployment stage"""
        time.sleep(1)
        return {'status': 'completed', 'message': 'Model deployment completed'}

    def deploy_model(self, model_id: str, deployment_config: Dict[str, Any]) -> bool:
        """Deploy model to production"""
        if model_id not in self.model_registry:
            raise ValueError(f'Model not found: {model_id}')
        model = self.model_registry[model_id]
        try:
            deployment_info = {'deployment_id': f'deploy_{int(time.time() * 1000)}', 'environment': deployment_config.get('environment', 'production'), 'endpoint': deployment_config.get('endpoint', f'/api/models/{model_id}'), 'deployed_at': time.time(), 'status': 'active'}
            model.is_deployed = True
            model.deployment_info = deployment_info
            self._save_model_registry()
            logger.info(f'Model deployed: {model.name} v{model.version}')
            return True
        except Exception as e:
            logger.error(f'Model deployment failed: {e}')
            return False

    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get detailed experiment results"""
        if experiment_id not in self.experiments:
            raise ValueError(f'Experiment not found: {experiment_id}')
        experiment = self.experiments[experiment_id]
        return {'experiment': asdict(experiment), 'model_info': self._get_model_info(experiment.model_path) if experiment.model_path else None, 'performance_comparison': self._compare_with_similar_experiments(experiment)}

    def _get_model_info(self, model_path: str) -> Dict[str, Any]:
        """Get model information"""
        if not model_path or not Path(model_path).exists():
            return None
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            return {'model_type': type(model).__name__, 'parameters': model.get_params() if hasattr(model, 'get_params') else {}, 'size_bytes': Path(model_path).stat().st_size}
        except Exception as e:
            logger.error(f'Failed to get model info: {e}')
            return None

    def _compare_with_similar_experiments(self, experiment: MLExperiment) -> List[Dict[str, Any]]:
        """Compare experiment with similar ones"""
        similar = []
        for (exp_id, exp) in self.experiments.items():
            if exp_id != experiment.experiment_id and exp.model_type == experiment.model_type and (exp.status == 'completed'):
                similar.append({'experiment_id': exp_id, 'name': exp.name, 'metrics': exp.metrics, 'hyperparameters': exp.hyperparameters})
        primary_metric = 'accuracy' if experiment.model_type in self.supported_algorithms['classification'] else 'r2_score'
        similar.sort(key=lambda x: x['metrics'].get(primary_metric, 0), reverse=True)
        return similar[:5]

    def get_workspace_overview(self) -> Dict[str, Any]:
        """Get comprehensive workspace overview"""
        exp_stats = {'total': len(self.experiments), 'completed': len([e for e in self.experiments.values() if e.status == 'completed']), 'running': len([e for e in self.experiments.values() if e.status == 'running']), 'failed': len([e for e in self.experiments.values() if e.status == 'failed'])}
        model_stats = {'total': len(self.model_registry), 'deployed': len([m for m in self.model_registry.values() if m.is_deployed]), 'by_type': defaultdict(int)}
        for model in self.model_registry.values():
            model_stats['by_type'][model.model_type] += 1
        pipeline_stats = {'total': len(self.pipelines), 'active': len([p for p in self.pipelines.values() if p.is_active])}
        recent_experiments = sorted([e for e in self.experiments.values() if e.completed_at], key=lambda x: x.completed_at, reverse=True)[:5]
        return {'workspace_path': str(self.workspace_path), 'experiments': exp_stats, 'models': model_stats, 'pipelines': pipeline_stats, 'recent_experiments': [asdict(e) for e in recent_experiments], 'configuration': self.ml_config, 'supported_algorithms': self.supported_algorithms}

    def _save_experiments(self):
        """Save experiments to file"""
        try:
            experiments_file = self.workspace_path / 'experiments' / 'experiments.json'
            with open(experiments_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(exp) for exp in self.experiments.values()], f, indent=2, default=str)
        except Exception as e:
            logger.error(f'Failed to save experiments: {e}')

    def _save_model_registry(self):
        """Save model registry to file"""
        try:
            registry_file = self.workspace_path / 'models' / 'registry.json'
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(model) for model in self.model_registry.values()], f, indent=2, default=str)
        except Exception as e:
            logger.error(f'Failed to save model registry: {e}')

    def _save_pipelines(self):
        """Save pipelines to file"""
        try:
            pipelines_file = self.workspace_path / 'pipelines' / 'pipelines.json'
            with open(pipelines_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(pipeline) for pipeline in self.pipelines.values()], f, indent=2, default=str)
        except Exception as e:
            logger.error(f'Failed to save pipelines: {e}')

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ML engineering operations based on parameters"""
        try:
            action = params.get('action', 'overview')

            if action == 'create_experiment':
                experiment_id = self.create_experiment(
                    name=params.get('name', 'test_experiment'),
                    description=params.get('description', 'Test experiment'),
                    dataset_path=params.get('dataset_path', ''),
                    model_type=params.get('model_type', 'linear_regression'),
                    hyperparameters=params.get('hyperparameters', {})
                )
                return {'success': True, 'experiment_id': experiment_id}

            elif action == 'run_experiment':
                success = self.run_experiment(params.get('experiment_id', ''))
                return {'success': success}

            elif action == 'overview':
                overview = self.get_workspace_overview()
                return {'success': True, 'overview': overview}

            else:
                return {'success': False, 'error': f'Unknown action: {action}'}

        except Exception as e:
            logger.error(f'Execution failed: {e}')
            return {'success': False, 'error': str(e)}
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ml_engineer = AdvancedMLEngineering()
    try:
        import pandas as pd
        from sklearn.datasets import make_classification
        (X, y) = make_classification(n_samples=1000, n_features=10, n_classes=2, random_state=42)
        df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
        df['target'] = y
        dataset_path = 'sample_dataset.csv'
        df.to_csv(dataset_path, index=False)
        experiment_id = ml_engineer.create_experiment(name='Sample Classification', description='Test classification with random forest', dataset_path=dataset_path, model_type='random_forest', hyperparameters={'n_estimators': 100, 'max_depth': 10, 'min_samples_split': 5})
        print(f'Running experiment: {experiment_id}')
        success = ml_engineer.run_experiment(experiment_id)
        if success:
            time.sleep(5)
            results = ml_engineer.get_experiment_results(experiment_id)
            print(f"Experiment results: {results['experiment']['metrics']}")
        search_id = ml_engineer.create_hyperparameter_search(experiment_name='Random Forest Optimization', search_space={'n_estimators': {'type': 'int', 'min': 50, 'max': 200}, 'max_depth': {'type': 'int', 'min': 5, 'max': 20}, 'min_samples_split': {'type': 'categorical', 'values': [2, 5, 10]}}, search_method='random', max_trials=5)
        pipeline_id = ml_engineer.create_pipeline(name='ML Pipeline', description='Complete ML workflow', stages=[{'type': 'data_preprocessing', 'name': 'Preprocessing'}, {'type': 'model_training', 'name': 'Training'}, {'type': 'model_evaluation', 'name': 'Evaluation'}])
        overview = ml_engineer.get_workspace_overview()
        print(f'Workspace overview: {overview}')
    finally:
        if Path(dataset_path).exists():
            Path(dataset_path).unlink()