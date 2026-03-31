"""
Prometheus 巡检系统 - 主入口
"""

import argparse
import yaml
import sys
from datetime import datetime
from typing import Dict, Any

from inspection.collector import PrometheusCollector
from inspection.checker import HealthChecker
from inspection.reporter import ReportGenerator


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_inspection(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行巡检
    
    Args:
        config: 配置字典
        
    Returns:
        巡检结果
    """
    print("=" * 60)
    print("Prometheus 巡检系统")
    print("=" * 60)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 获取配置
    prometheus_config = config.get('prometheus', {})
    thresholds = config.get('thresholds', {})
    report_config = config.get('report', {})
    
    prometheus_url = prometheus_config.get('url', 'http://localhost:9090')
    timeout = prometheus_config.get('timeout', 30)
    
    # 初始化组件
    print(f"连接 Prometheus: {prometheus_url}")
    collector = PrometheusCollector(prometheus_url, timeout)
    checker = HealthChecker(thresholds)
    reporter = ReportGenerator(report_config.get('output_dir', 'reports'))
    
    # 收集指标
    print("正在收集指标...")
    try:
        metrics = collector.collect_all_metrics()
        print("✓ 指标收集完成")
    except Exception as e:
        print(f"✗ 指标收集失败：{str(e)}")
        return {'error': str(e)}
    
    # 执行健康检查
    print("正在执行健康检查...")
    inspection_result = checker.run_all_checks(metrics)
    print(f"✓ 健康检查完成 - 总体状态：{inspection_result['overall_status'].upper()}")
    
    # 生成报告
    formats = report_config.get('formats', ['html', 'json'])
    print(f"正在生成报告 (格式：{', '.join(formats)})...")
    report_files = reporter.generate_all_reports(inspection_result, formats)
    print("✓ 报告生成完成:")
    for filepath in report_files:
        print(f"  - {filepath}")
    
    # 打印摘要
    print()
    print("=" * 60)
    print("巡检摘要")
    print("=" * 60)
    summary = inspection_result.get('summary', {})
    print(f"总体状态：{inspection_result.get('overall_status', 'unknown').upper()}")
    print(f"健康检查项：{summary.get('healthy_count', 0)}")
    print(f"警告数量：{summary.get('warning_count', 0)}")
    print(f"严重问题：{summary.get('critical_count', 0)}")
    print(f"总警告数：{summary.get('total_warnings', 0)}")
    print(f"总问题数：{summary.get('total_issues', 0)}")
    print()
    
    # 显示详细问题
    if summary.get('total_issues', 0) > 0:
        print("⚠️  需要关注的问题:")
        for check_name, check_data in inspection_result.get('checks', {}).items():
            for issue in check_data.get('issues', []):
                if isinstance(issue, dict):
                    print(f"  - [{check_name}] {issue.get('type')}: {issue.get('instance', '')}")
                else:
                    print(f"  - [{check_name}] {issue}")
        print()
    
    if summary.get('total_warnings', 0) > 0:
        print("🔔 警告信息:")
        for check_name, check_data in inspection_result.get('checks', {}).items():
            for warning in check_data.get('warnings', []):
                print(f"  - [{check_name}] {warning}")
        print()
    
    print("=" * 60)
    print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return inspection_result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Prometheus 巡检系统')
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config/inspection_config.yml',
        help='配置文件路径 (默认：config/inspection_config.yml)'
    )
    parser.add_argument(
        '--url', '-u',
        type=str,
        help='Prometheus 服务器 URL (覆盖配置文件中的设置)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='报告输出目录 (覆盖配置文件中的设置)'
    )
    parser.add_argument(
        '--format', '-f',
        type=str,
        nargs='+',
        choices=['html', 'json', 'csv'],
        help='报告输出格式 (默认：html json)'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"错误：配置文件不存在 - {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"错误：加载配置文件失败 - {str(e)}")
        sys.exit(1)
    
    # 覆盖配置
    if args.url:
        config['prometheus']['url'] = args.url
    if args.output:
        config['report']['output_dir'] = args.output
    if args.format:
        config['report']['formats'] = args.format
    
    # 执行巡检
    result = run_inspection(config)
    
    # 根据检查结果设置退出码
    if 'error' in result:
        sys.exit(2)
    elif result.get('overall_status') == 'critical':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
