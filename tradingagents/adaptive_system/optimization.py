"""
参数优化模块
优化自适应系统的超参数
"""
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import random
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    history: List[Dict[str, Any]]
    convergence_iteration: int


class WeightOptimizer:
    """权重优化器"""
    
    def __init__(self, 
                param_bounds: Optional[Dict[str, Tuple[float, float]]] = None):
        
        # 默认参数边界
        self.param_bounds = param_bounds or {
            'learning_rate': (0.01, 0.5),
            'weight_decay': (0.9, 0.999),
            'error_window_size': (5, 50),
            'recent_weight_factor': (1.0, 5.0),
            'min_weight': (0.05, 0.3),
            'max_weight': (2.0, 8.0)
        }
        
        self.optimization_history = []
    
    def random_search(self, 
                     evaluate_function: callable,
                     n_iterations: int = 100,
                     seed: int = 42) -> OptimizationResult:
        """随机搜索优化"""
        
        random.seed(seed)
        np.random.seed(seed)
        
        best_score = -float('inf')
        best_params = None
        history = []
        
        for i in range(n_iterations):
            # 生成随机参数
            params = {}
            for param_name, (low, high) in self.param_bounds.items():
                if param_name == 'error_window_size':
                    params[param_name] = random.randint(int(low), int(high))
                else:
                    params[param_name] = random.uniform(low, high)
            
            # 评估参数
            score = evaluate_function(params)
            
            # 记录历史
            history.append({
                'iteration': i,
                'params': params.copy(),
                'score': score
            })
            
            # 更新最佳参数
            if score > best_score:
                best_score = score
                best_params = params.copy()
                convergence_iteration = i
            
            print(f"Iteration {i+1}/{n_iterations}: Score = {score:.4f}")
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            history=history,
            convergence_iteration=convergence_iteration
        )
    
    def grid_search(self, 
                   evaluate_function: callable,
                   param_grid: Optional[Dict[str, List]] = None) -> OptimizationResult:
        """网格搜索优化"""
        
        # 默认参数网格
        if param_grid is None:
            param_grid = {
                'learning_rate': [0.05, 0.1, 0.2, 0.3],
                'weight_decay': [0.95, 0.97, 0.99],
                'error_window_size': [10, 20, 30],
                'min_weight': [0.1, 0.2, 0.3],
                'max_weight': [3.0, 4.0, 5.0]
            }
        
        best_score = -float('inf')
        best_params = None
        history = []
        iteration = 0
        
        # 递归生成所有参数组合
        def generate_combinations(params_dict, current={}):
            nonlocal iteration, best_score, best_params
            
            if not params_dict:
                # 评估当前参数组合
                score = evaluate_function(current)
                
                history.append({
                    'iteration': iteration,
                    'params': current.copy(),
                    'score': score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = current.copy()
                    convergence_iteration = iteration
                
                iteration += 1
                print(f"Combination {iteration}: Score = {score:.4f}")
                return
            
            param_name, values = list(params_dict.items())[0]
            remaining = dict(list(params_dict.items())[1:])
            
            for value in values:
                generate_combinations(remaining, {**current, param_name: value})
        
        generate_combinations(param_grid)
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            history=history,
            convergence_iteration=convergence_iteration
        )
    
    def optimize_layer_configs(self, 
                             agent_performance: Dict[str, Dict[str, float]],
                             target_metric: str = 'sharpe_ratio') -> Dict[str, Dict]:
        """优化层级配置"""
        
        optimized_configs = {}
        
        # 分析每个层级的性能
        layer_performance = {}
        for agent_name, perf in agent_performance.items():
            layer = perf.get('layer', 'analyst')
            if layer not in layer_performance:
                layer_performance[layer] = []
            layer_performance[layer].append(perf.get(target_metric, 0.0))
        
        # 为每个层级生成优化配置
        for layer, performances in layer_performance.items():
            avg_performance = np.mean(performances) if performances else 0.0
            std_performance = np.std(performances) if performances else 1.0
            
            # 基于性能调整配置
            if avg_performance > 0.5:  # 表现好
                config = {
                    'adjust_speed': 0.4,  # 中等调整速度
                    'min_weight': 0.3,
                    'max_weight': 3.0,
                    'volatility_tolerance': 1.0
                }
            elif avg_performance > 0:  # 表现一般
                config = {
                    'adjust_speed': 0.6,  # 更快调整
                    'min_weight': 0.2,
                    'max_weight': 2.5,
                    'volatility_tolerance': 0.8
                }
            else:  # 表现差
                config = {
                    'adjust_speed': 0.2,  # 慢速调整
                    'min_weight': 0.1,
                    'max_weight': 2.0,
                    'volatility_tolerance': 1.2
                }
            
            # 根据波动性调整
            if std_performance > 0.3:  # 波动大
                config['volatility_tolerance'] *= 1.5
            
            optimized_configs[layer] = config
        
        return optimized_configs
    
    def create_evaluation_function(self, historical_data: List[Dict],
                                 weight_manager_class,
                                 metric: str = 'cumulative_return') -> callable:
        """创建参数评估函数"""
        
        def evaluate_params(params: Dict) -> float:
            """评估参数性能"""
            
            # 使用历史数据模拟
            returns = []
            decisions = []
            
            # 这里实现简化的模拟逻辑
            # 在实际应用中，需要完整模拟交易过程
            
            for i in range(len(historical_data) - 1):
                # 模拟决策过程
                current_data = historical_data[i]
                next_data = historical_data[i + 1]
                
                # 这里简化处理，实际需要完整的权重管理
                decision = random.uniform(-1, 1)  # 简化决策
                actual_return = (next_data.get('price', 1) - 
                               current_data.get('price', 1)) / current_data.get('price', 1)
                
                # 假设决策与回报相关
                simulated_return = decision * actual_return * 0.5
                returns.append(simulated_return)
                decisions.append(decision)
            
            if not returns:
                return 0.0
            
            # 计算评估指标
            if metric == 'cumulative_return':
                score = np.sum(returns)
            elif metric == 'sharpe_ratio':
                returns_array = np.array(returns)
                if returns_array.std() > 0:
                    score = returns_array.mean() / returns_array.std() * np.sqrt(252)
                else:
                    score = 0.0
            elif metric == 'win_rate':
                wins = sum(1 for r in returns if r > 0)
                score = wins / len(returns) if returns else 0.0
            else:
                score = np.mean(returns)
            
            return score
        
        return evaluate_params
    
    def optimize_with_genetic_algorithm(self, 
                                      evaluate_function: callable,
                                      population_size: int = 50,
                                      generations: int = 20,
                                      mutation_rate: float = 0.1) -> OptimizationResult:
        """使用遗传算法优化"""
        
        # 初始化种群
        population = []
        for _ in range(population_size):
            individual = {}
            for param_name, (low, high) in self.param_bounds.items():
                if param_name == 'error_window_size':
                    individual[param_name] = random.randint(int(low), int(high))
                else:
                    individual[param_name] = random.uniform(low, high)
            population.append(individual)
        
        best_score = -float('inf')
        best_individual = None
        history = []
        
        for generation in range(generations):
            # 评估适应度
            scores = []
            for individual in population:
                score = evaluate_function(individual)
                scores.append(score)
            
            # 选择最佳个体
            best_idx = np.argmax(scores)
            generation_best_score = scores[best_idx]
            generation_best_individual = population[best_idx].copy()
            
            if generation_best_score > best_score:
                best_score = generation_best_score
                best_individual = generation_best_individual.copy()
                convergence_generation = generation
            
            # 记录历史
            history.append({
                'generation': generation,
                'best_score': generation_best_score,
                'best_params': generation_best_individual,
                'avg_score': np.mean(scores)
            })
            
            print(f"Generation {generation+1}/{generations}: "
                  f"Best = {generation_best_score:.4f}, "
                  f"Avg = {np.mean(scores):.4f}")
            
            # 创建新一代（简化版）
            if generation < generations - 1:
                new_population = []
                
                # 保留最佳个体
                new_population.append(generation_best_individual)
                
                # 选择和交叉
                while len(new_population) < population_size:
                    # 轮盘赌选择
                    parent1 = self._roulette_select(population, scores)
                    parent2 = self._roulette_select(population, scores)
                    
                    # 交叉
                    child = self._crossover(parent1, parent2)
                    
                    # 突变
                    child = self._mutate(child, mutation_rate)
                    
                    new_population.append(child)
                
                population = new_population
        
        return OptimizationResult(
            best_params=best_individual,
            best_score=best_score,
            history=history,
            convergence_iteration=convergence_generation
        )
    
    def _roulette_select(self, population: List[Dict], 
                        scores: List[float]) -> Dict:
        """轮盘赌选择"""
        min_score = min(scores)
        adjusted_scores = [s - min_score + 0.01 for s in scores]
        total = sum(adjusted_scores)
        probabilities = [s / total for s in adjusted_scores]
        
        return random.choices(population, weights=probabilities)[0]
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """交叉操作"""
        child = {}
        for param_name in parent1.keys():
            if random.random() > 0.5:
                child[param_name] = parent1[param_name]
            else:
                child[param_name] = parent2[param_name]
        return child
    
    def _mutate(self, individual: Dict, mutation_rate: float) -> Dict:
        """突变操作"""
        mutated = individual.copy()
        
        for param_name, (low, high) in self.param_bounds.items():
            if random.random() < mutation_rate:
                if param_name == 'error_window_size':
                    mutated[param_name] = random.randint(int(low), int(high))
                else:
                    mutated[param_name] = random.uniform(low, high)
        
        return mutated