"""
可视化监控模块
提供权重、误差和性能的可视化功能
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np


class WeightVisualizer:
    """权重可视化器"""
    
    def __init__(self):
        self.figures = {}
    
    def plot_weights(self, agent_records: Dict[str, Any], 
                    title: str = "智能体权重分布") -> go.Figure:
        """绘制智能体权重分布图"""
        
        # 准备数据
        agent_names = []
        current_weights = []
        avg_errors = []
        colors = []
        
        for name, record in agent_records.items():
            agent_names.append(name)
            current_weights.append(record.current_weight)
            
            # 计算平均误差
            if hasattr(record, 'get_average_error'):
                error = record.get_average_error()
            elif hasattr(record, 'errors') and record.errors:
                error = np.mean(record.errors[-10:])
            else:
                error = 1.0
            
            avg_errors.append(error)
            
            # 根据误差设置颜色（误差越小颜色越绿）
            if error < 0.1:
                colors.append('green')
            elif error < 0.3:
                colors.append('lightgreen')
            elif error < 0.5:
                colors.append('yellow')
            elif error < 0.8:
                colors.append('orange')
            else:
                colors.append('red')
        
        # 创建柱状图
        fig = go.Figure(data=[
            go.Bar(
                x=agent_names,
                y=current_weights,
                marker_color=colors,
                text=[f"误差: {err:.3f}" for err in avg_errors],
                textposition='auto',
                name="当前权重"
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="智能体",
            yaxis_title="权重",
            showlegend=False,
            template="plotly_white"
        )
        
        return fig
    
    def plot_weight_history(self, weight_history: Dict[str, List[float]],
                          title: str = "权重历史变化") -> go.Figure:
        """绘制权重历史变化图"""
        
        fig = go.Figure()
        
        for agent_name, history in weight_history.items():
            fig.add_trace(go.Scatter(
                y=history,
                mode='lines+markers',
                name=agent_name,
                line=dict(width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="更新次数",
            yaxis_title="权重",
            hovermode='x unified',
            template="plotly_white"
        )
        
        return fig
    
    def plot_error_heatmap(self, agent_errors: Dict[str, List[float]],
                          title: str = "智能体误差热图") -> go.Figure:
        """绘制误差热图"""
        
        # 转换为DataFrame
        max_len = max(len(errors) for errors in agent_errors.values())
        
        data = []
        for agent_name, errors in agent_errors.items():
            padded_errors = errors + [np.nan] * (max_len - len(errors))
            data.append(padded_errors)
        
        df = pd.DataFrame(
            data,
            index=list(agent_errors.keys()),
            columns=[f"T-{i}" for i in range(max_len-1, -1, -1)]
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=df.values,
            x=df.columns,
            y=df.index,
            colorscale='RdYlGn_r',  # 红色高误差，绿色低误差
            zmin=0,
            zmax=1,
            colorbar=dict(title="误差值"),
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="时间步长（最近 -> 最早）",
            yaxis_title="智能体",
            template="plotly_white"
        )
        
        return fig
    
    def create_dashboard(self, adaptive_system, 
                        history_length: int = 50) -> go.Figure:
        """创建综合监控仪表板"""
        
        agent_records = adaptive_system.weight_manager.get_all_records()
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '智能体当前权重',
                '权重历史变化',
                '误差热图',
                '权重分布箱线图'
            ),
            specs=[
                [{'type': 'bar'}, {'type': 'scatter'}],
                [{'type': 'heatmap'}, {'type': 'box'}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # 1. 当前权重柱状图
        agent_names = list(agent_records.keys())
        current_weights = [r.current_weight for r in agent_records.values()]
        
        colors = []
        for record in agent_records.values():
            error = record.get_average_error() if hasattr(record, 'get_average_error') else 1.0
            if error < 0.2:
                colors.append('green')
            elif error < 0.4:
                colors.append('lightgreen')
            elif error < 0.6:
                colors.append('yellow')
            elif error < 0.8:
                colors.append('orange')
            else:
                colors.append('red')
        
        fig.add_trace(
            go.Bar(
                x=agent_names,
                y=current_weights,
                marker_color=colors,
                name="当前权重"
            ),
            row=1, col=1
        )
        
        # 2. 权重历史变化
        for agent_name, record in agent_records.items():
            if hasattr(record, 'weight_history') and record.weight_history:
                history = record.weight_history[-history_length:]
                fig.add_trace(
                    go.Scatter(
                        y=history,
                        mode='lines',
                        name=agent_name,
                        line=dict(width=1)
                    ),
                    row=1, col=2
                )
        
        # 3. 误差热图
        error_data = {}
        for agent_name, record in agent_records.items():
            if hasattr(record, 'errors') and record.errors:
                error_data[agent_name] = record.errors[-history_length:]
        
        if error_data:
            max_len = max(len(errors) for errors in error_data.values())
            heatmap_data = []
            
            for agent_name in agent_names:
                if agent_name in error_data:
                    errors = error_data[agent_name]
                    padded = errors + [np.nan] * (max_len - len(errors))
                    heatmap_data.append(padded)
                else:
                    heatmap_data.append([np.nan] * max_len)
            
            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data,
                    x=[f"T-{i}" for i in range(max_len-1, -1, -1)],
                    y=agent_names,
                    colorscale='RdYlGn_r',
                    zmin=0,
                    zmax=1,
                    colorbar=dict(title="误差", len=0.4, y=0.25),
                    showscale=True
                ),
                row=2, col=1
            )
        
        # 4. 权重分布箱线图
        weight_data = []
        for record in agent_records.values():
            if hasattr(record, 'weight_history') and record.weight_history:
                weight_data.append(record.weight_history[-history_length:])
        
        if weight_data:
            fig.add_trace(
                go.Box(
                    y=weight_data,
                    name="权重分布",
                    boxmean='sd',
                    marker_color='lightblue',
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            height=800,
            title_text="自适应权重系统监控面板",
            showlegend=True,
            template="plotly_white"
        )
        
        fig.update_xaxes(title_text="智能体", row=1, col=1)
        fig.update_yaxes(title_text="权重", row=1, col=1)
        fig.update_xaxes(title_text="历史步长", row=1, col=2)
        fig.update_yaxes(title_text="权重", row=1, col=2)
        fig.update_xaxes(title_text="时间步长", row=2, col=1)
        fig.update_yaxes(title_text="智能体", row=2, col=1)
        fig.update_xaxes(title_text="", row=2, col=2)
        fig.update_yaxes(title_text="权重值", row=2, col=2)
        
        return fig
    
    def save_dashboard(self, adaptive_system, 
                      filepath: str = "adaptive_dashboard.html"):
        """保存监控仪表板到HTML文件"""
        fig = self.create_dashboard(adaptive_system)
        fig.write_html(filepath)
        return filepath
    
    def real_time_stream(self, update_callback, interval: int = 5000):
        """设置实时数据流（简化版）"""
        # 这里可以集成Dash或WebSocket实现实时更新
        # 返回一个可以停止的定时器
        
        import threading
        import time
        
        class StreamController:
            def __init__(self):
                self.running = True
            
            def stop(self):
                self.running = False
        
        controller = StreamController()
        
        def stream_loop():
            while controller.running:
                # 调用更新回调
                update_callback()
                time.sleep(interval / 1000)
        
        thread = threading.Thread(target=stream_loop, daemon=True)
        thread.start()
        
        return controller