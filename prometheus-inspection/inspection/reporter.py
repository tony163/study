"""
Prometheus 巡检系统 - 报告生成器
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Any
from jinja2 import Template


class ReportGenerator:
    """巡检报告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_json_report(self, inspection_result: Dict) -> str:
        """
        生成 JSON 格式报告
        
        Args:
            inspection_result: 巡检结果
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspection_report_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(inspection_result, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def generate_csv_report(self, inspection_result: Dict) -> str:
        """
        生成 CSV 格式报告
        
        Args:
            inspection_result: 巡检结果
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspection_report_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        rows = []
        
        # 添加总体状态
        rows.append(['检查项', '状态', '指标', '值', '问题/警告'])
        rows.append(['总体状态', inspection_result.get('overall_status', 'unknown'), '', '', ''])
        rows.append(['', '', '', '', ''])
        
        # 添加各个检查项
        checks = inspection_result.get('checks', {})
        for check_name, check_data in checks.items():
            status = check_data.get('status', 'unknown')
            metrics = check_data.get('metrics', {})
            issues = check_data.get('issues', [])
            warnings = check_data.get('warnings', [])
            
            # 添加检查项标题行
            rows.append([check_name, status, '', '', ''])
            
            # 添加指标行
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    rows.append(['', '', metric_name, str(metric_value), ''])
                elif isinstance(metric_value, dict):
                    for sub_name, sub_value in metric_value.items():
                        rows.append(['', '', f"{metric_name}.{sub_name}", str(sub_value), ''])
            
            # 添加问题和警告
            for issue in issues:
                if isinstance(issue, dict):
                    issue_str = f"[问题] {issue.get('type', 'unknown')}: {issue.get('instance', '')}"
                else:
                    issue_str = f"[问题] {issue}"
                rows.append(['', '', '', '', issue_str])
            
            for warning in warnings:
                rows.append(['', '', '', '', f"[警告] {warning}"])
            
            rows.append(['', '', '', '', ''])
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        return filepath
    
    def generate_html_report(self, inspection_result: Dict) -> str:
        """
        生成 HTML 格式报告
        
        Args:
            inspection_result: 巡检结果
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspection_report_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        html_template = Template('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prometheus 巡检报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
        }
        .status-healthy {
            background-color: #d4edda;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        .status-critical {
            background-color: #f8d7da;
            color: #721c24;
        }
        .summary-box {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 3px solid #3498db;
        }
        .metric-card.warning {
            border-left-color: #ffc107;
        }
        .metric-card.critical {
            border-left-color: #dc3545;
        }
        .metric-label {
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }
        .check-section {
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .issue-list {
            list-style: none;
            padding: 0;
        }
        .issue-list li {
            padding: 8px 12px;
            margin: 5px 0;
            background: #fff;
            border-radius: 4px;
            border-left: 3px solid #dc3545;
        }
        .warning-list li {
            border-left-color: #ffc107;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background: #343a40;
            color: white;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .timestamp {
            color: #6c757d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Prometheus 巡检报告</h1>
        <p class="timestamp">生成时间：{{ report_time }}</p>
        
        <div class="summary-box">
            <h2>总体状态</h2>
            <p>
                <span class="status-badge status-{{ overall_status }}">
                    {{ overall_status | upper }}
                </span>
            </p>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">健康检查项</div>
                    <div class="metric-value">{{ summary.healthy_count }}</div>
                </div>
                <div class="metric-card warning">
                    <div class="metric-label">警告数量</div>
                    <div class="metric-value">{{ summary.warning_count }}</div>
                </div>
                <div class="metric-card critical">
                    <div class="metric-label">严重问题</div>
                    <div class="metric-value">{{ summary.critical_count }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">总警告数</div>
                    <div class="metric-value">{{ summary.total_warnings }}</div>
                </div>
            </div>
        </div>
        
        <h2>详细检查结果</h2>
        
        {% for check_name, check_data in checks.items() %}
        <div class="check-section">
            <h3>
                {{ check_name | replace('_', ' ') | title }}
                <span class="status-badge status-{{ check_data.status }}">
                    {{ check_data.status | upper }}
                </span>
            </h3>
            
            {% if check_data.metrics %}
            <table>
                <thead>
                    <tr>
                        <th>指标名称</th>
                        <th>指标值</th>
                    </tr>
                </thead>
                <tbody>
                    {% for metric_name, metric_value in check_data.metrics.items() %}
                    <tr>
                        <td>{{ metric_name }}</td>
                        <td>{{ metric_value }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            
            {% if check_data.issues %}
            <h4>⚠️ 问题列表</h4>
            <ul class="issue-list">
                {% for issue in check_data.issues %}
                <li>
                    {% if issue is mapping %}
                        [{{ issue.type }}] {{ instance }} - {{ error }}
                    {% else %}
                        {{ issue }}
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if check_data.warnings %}
            <h4>🔔 警告列表</h4>
            <ul class="issue-list warning-list">
                {% for warning in check_data.warnings %}
                <li>{{ warning }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d;">
            <p>Prometheus 巡检系统 | 自动生成报告</p>
        </div>
    </div>
</body>
</html>
        ''')
        
        # 准备模板数据
        template_data = {
            'report_time': inspection_result.get('check_time', datetime.now().isoformat()),
            'overall_status': inspection_result.get('overall_status', 'unknown'),
            'summary': inspection_result.get('summary', {}),
            'checks': inspection_result.get('checks', {})
        }
        
        html_content = html_template.render(**template_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def generate_all_reports(self, inspection_result: Dict, formats: List[str] = None) -> List[str]:
        """
        生成所有指定格式的报告
        
        Args:
            inspection_result: 巡检结果
            formats: 报告格式列表 ['html', 'json', 'csv']
            
        Returns:
            生成的报告文件路径列表
        """
        if formats is None:
            formats = ['html', 'json']
        
        generated_files = []
        
        for fmt in formats:
            try:
                if fmt.lower() == 'json':
                    filepath = self.generate_json_report(inspection_result)
                    generated_files.append(filepath)
                elif fmt.lower() == 'csv':
                    filepath = self.generate_csv_report(inspection_result)
                    generated_files.append(filepath)
                elif fmt.lower() == 'html':
                    filepath = self.generate_html_report(inspection_result)
                    generated_files.append(filepath)
            except Exception as e:
                print(f"生成 {fmt} 报告失败：{str(e)}")
        
        return generated_files
