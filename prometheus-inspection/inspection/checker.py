"""
Prometheus 巡检系统 - 健康检查器
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class HealthChecker:
    """Prometheus 健康检查器"""
    
    def __init__(self, thresholds: Dict[str, Any]):
        """
        初始化检查器
        
        Args:
            thresholds: 阈值配置字典
        """
        self.thresholds = thresholds
    
    def check_target_health(self, target_data: Dict) -> Dict[str, Any]:
        """
        检查目标健康状态
        
        Args:
            target_data: 目标数据
            
        Returns:
            检查结果
        """
        result = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': {}
        }
        
        total_targets = target_data.get('total', 0)
        up_targets = target_data.get('up', 0)
        down_targets = target_data.get('down', 0)
        
        result['metrics'] = {
            'total_targets': total_targets,
            'up_targets': up_targets,
            'down_targets': down_targets,
            'health_rate': (up_targets / total_targets * 100) if total_targets > 0 else 0
        }
        
        # 检查是否有目标下线
        if down_targets > 0:
            threshold_seconds = self.thresholds.get('target_down_seconds', 60)
            result['warnings'].append(f"{down_targets} 个目标已下线")
            
            # 检查详细的目标状态
            details = target_data.get('details', [])
            for detail in details:
                if detail.get('health') != 'up':
                    result['issues'].append({
                        'type': 'target_down',
                        'job': detail.get('job'),
                        'instance': detail.get('instance'),
                        'error': detail.get('last_error', 'Unknown error')
                    })
        
        # 计算健康率并判断状态
        health_rate = result['metrics']['health_rate']
        if health_rate < 80:
            result['status'] = 'critical'
        elif health_rate < 95:
            result['status'] = 'warning'
        
        return result
    
    def check_scrape_metrics(self, scrape_data: Dict) -> Dict[str, Any]:
        """
        检查抓取指标
        
        Args:
            scrape_data: 抓取指标数据
            
        Returns:
            检查结果
        """
        result = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': scrape_data
        }
        
        # 检查抓取失败率
        failure_rate = scrape_data.get('scrape_failure_rate')
        if failure_rate is not None:
            warning_threshold = self.thresholds.get('scrape_failure_rate_warning', 5)
            critical_threshold = self.thresholds.get('scrape_failure_rate_critical', 20)
            
            if failure_rate > critical_threshold:
                result['status'] = 'critical'
                result['issues'].append(f"抓取失败率过高：{failure_rate:.2f}% (临界值：{critical_threshold}%)")
            elif failure_rate > warning_threshold:
                if result['status'] != 'critical':
                    result['status'] = 'warning'
                result['warnings'].append(f"抓取失败率偏高：{failure_rate:.2f}% (警告值：{warning_threshold}%)")
        
        # 检查平均抓取时长
        avg_duration = scrape_data.get('avg_scrape_duration')
        if avg_duration is not None and avg_duration > 30:
            result['warnings'].append(f"平均抓取时长较长：{avg_duration:.2f}s")
        
        return result
    
    def check_rule_evaluation(self, rule_data: Dict) -> Dict[str, Any]:
        """
        检查规则评估状态（检查 alert_rules 中的所有规则项）
        
        Args:
            rule_data: 规则评估数据，包含 groups 和 rules 信息
            
        Returns:
            检查结果
        """
        result = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': {},
            'rule_checks': []
        }
        
        # 检查评估延迟
        max_duration = rule_data.get('max_evaluation_duration')
        if max_duration is not None:
            warning_threshold = self.thresholds.get('evaluation_delay_warning', 30)
            critical_threshold = self.thresholds.get('evaluation_delay_critical', 120)
            
            if max_duration > critical_threshold:
                result['status'] = 'critical'
                result['issues'].append(f"规则评估延迟过高：{max_duration:.2f}s (临界值：{critical_threshold}s)")
            elif max_duration > warning_threshold:
                if result['status'] != 'critical':
                    result['status'] = 'warning'
                result['warnings'].append(f"规则评估延迟偏高：{max_duration:.2f}s (警告值：{warning_threshold}s)")
        
        # 检查评估失败次数
        failures = rule_data.get('evaluation_failures')
        if failures is not None and failures > 0:
            result['warnings'].append(f"规则评估失败次数：{failures}")
        
        # 检查所有告警规则项
        groups = rule_data.get('groups', [])
        total_rules = 0
        active_alerts = 0
        pending_alerts = 0
        inactive_rules = 0
        
        for group in groups:
            group_name = group.get('name', 'unknown')
            rules = group.get('rules', [])
            
            for rule in rules:
                total_rules += 1
                rule_check = {
                    'group': group_name,
                    'rule_name': rule.get('name', 'unknown'),
                    'rule_type': rule.get('type', 'alerting'),
                    'state': rule.get('state', 'unknown'),
                    'health': 'healthy',
                    'issue': None
                }
                
                # 检查规则状态
                state = rule.get('state', '').lower()
                if state == 'firing':
                    active_alerts += 1
                    rule_check['health'] = 'critical'
                    rule_check['issue'] = f"告警正在触发：{rule.get('labels', {}).get('severity', 'unknown')} severity"
                    result['issues'].append({
                        'type': 'alert_firing',
                        'group': group_name,
                        'rule': rule.get('name'),
                        'severity': rule.get('labels', {}).get('severity', 'unknown'),
                        'value': rule.get('value'),
                        'labels': rule.get('labels', {}),
                        'annotations': rule.get('annotations', {})
                    })
                elif state == 'pending':
                    pending_alerts += 1
                    rule_check['health'] = 'warning'
                    rule_check['issue'] = f"告警等待中 (for: {rule.get('duration', 0)}s)"
                    result['warnings'].append({
                        'type': 'alert_pending',
                        'group': group_name,
                        'rule': rule.get('name'),
                        'duration': rule.get('duration', 0)
                    })
                else:
                    inactive_rules += 1
                
                result['rule_checks'].append(rule_check)
        
        # 添加规则统计指标
        result['metrics']['total_rules'] = total_rules
        result['metrics']['active_alerts'] = active_alerts
        result['metrics']['pending_alerts'] = pending_alerts
        result['metrics']['inactive_rules'] = inactive_rules
        result['metrics']['rule_groups'] = len(groups)
        
        # 根据活跃告警数量调整整体状态
        if active_alerts > 0:
            result['status'] = 'critical'
        elif pending_alerts > 0 and result['status'] != 'critical':
            result['status'] = 'warning'
        
        return result
    
    def check_tsdb_metrics(self, tsdb_data: Dict) -> Dict[str, Any]:
        """
        检查 TSDB 状态
        
        Args:
            tsdb_data: TSDB 指标数据
            
        Returns:
            检查结果
        """
        result = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': {}
        }
        
        # 检查头部 chunk 数量
        head_chunks = tsdb_data.get('head_chunks')
        if head_chunks is not None:
            warning_threshold = self.thresholds.get('tsdb_head_chunks_warning', 1000000)
            critical_threshold = self.thresholds.get('tsdb_head_chunks_critical', 5000000)
            
            result['metrics']['head_chunks'] = head_chunks
            
            if head_chunks > critical_threshold:
                result['status'] = 'critical'
                result['issues'].append(f"TSDB 头部 chunk 数量过多：{head_chunks} (临界值：{critical_threshold})")
            elif head_chunks > warning_threshold:
                if result['status'] != 'critical':
                    result['status'] = 'warning'
                result['warnings'].append(f"TSDB 头部 chunk 数量偏多：{head_chunks} (警告值：{warning_threshold})")
        
        # 添加其他 TSDB 指标
        result['metrics']['head_series'] = tsdb_data.get('head_series')
        result['metrics']['wal_segments'] = tsdb_data.get('wal_segments')
        
        # 检查 TSDB 状态错误
        tsdb_status = tsdb_data.get('tsdb_status', {})
        if 'error' in tsdb_status:
            result['warnings'].append(f"无法获取 TSDB 状态：{tsdb_status['error']}")
        
        return result
    
    def check_query_performance(self, query_data: Dict) -> Dict[str, Any]:
        """
        检查查询性能
        
        Args:
            query_data: 查询性能数据
            
        Returns:
            检查结果
        """
        result = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': query_data
        }
        
        # 检查 P99 查询延迟
        p99_latency = query_data.get('p99_query_latency')
        if p99_latency is not None:
            warning_threshold = self.thresholds.get('query_latency_warning', 5)
            critical_threshold = self.thresholds.get('query_latency_critical', 30)
            
            if p99_latency > critical_threshold:
                result['status'] = 'critical'
                result['issues'].append(f"查询延迟过高：{p99_latency:.2f}s (临界值：{critical_threshold}s)")
            elif p99_latency > warning_threshold:
                if result['status'] != 'critical':
                    result['status'] = 'warning'
                result['warnings'].append(f"查询延迟偏高：{p99_latency:.2f}s (警告值：{warning_threshold}s)")
        
        # 检查并发查询数
        concurrent = query_data.get('concurrent_queries')
        if concurrent is not None and concurrent > 100:
            result['warnings'].append(f"并发查询数较高：{concurrent}")
        
        return result
    
    def check_memory_usage(self, memory_data: Dict) -> Dict[str, Any]:
        """
        检查内存使用情况
        
        Args:
            memory_data: 内存使用数据
            
        Returns:
            检查结果
        """
        result = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': memory_data
        }
        
        memory_gb = memory_data.get('memory_gb')
        if memory_gb is not None:
            if memory_gb > 8:
                result['status'] = 'warning'
                result['warnings'].append(f"内存使用量较大：{memory_gb:.2f}GB")
            elif memory_gb > 16:
                result['status'] = 'critical'
                result['issues'].append(f"内存使用量过大：{memory_gb:.2f}GB")
        
        return result
    
    def run_all_checks(self, metrics: Dict) -> Dict[str, Any]:
        """
        运行所有健康检查
        
        Args:
            metrics: 收集的指标数据
            
        Returns:
            综合检查结果
        """
        check_time = datetime.now().isoformat()
        
        results = {
            'check_time': check_time,
            'overall_status': 'healthy',
            'checks': {},
            'summary': {
                'total_issues': 0,
                'total_warnings': 0,
                'critical_count': 0,
                'warning_count': 0,
                'healthy_count': 0
            }
        }
        
        # 执行各项检查
        checks = [
            ('target_health', self.check_target_health, metrics.get('target_health', {})),
            ('scrape_metrics', self.check_scrape_metrics, metrics.get('scrape_metrics', {})),
            ('rule_evaluation', self.check_rule_evaluation, metrics.get('rule_evaluation', {})),
            ('tsdb_metrics', self.check_tsdb_metrics, metrics.get('tsdb_metrics', {})),
            ('query_performance', self.check_query_performance, metrics.get('query_performance', {})),
            ('memory_usage', self.check_memory_usage, metrics.get('memory_metrics', {}))
        ]
        
        for check_name, check_func, check_data in checks:
            check_result = check_func(check_data)
            results['checks'][check_name] = check_result
            
            # 更新统计
            if check_result['status'] == 'critical':
                results['summary']['critical_count'] += 1
                results['summary']['total_issues'] += len(check_result['issues'])
            elif check_result['status'] == 'warning':
                results['summary']['warning_count'] += 1
                results['summary']['total_warnings'] += len(check_result['warnings'])
            else:
                results['summary']['healthy_count'] += 1
            
            results['summary']['total_issues'] += len(check_result['issues'])
            results['summary']['total_warnings'] += len(check_result['warnings'])
        
        # 确定总体状态
        if results['summary']['critical_count'] > 0:
            results['overall_status'] = 'critical'
        elif results['summary']['warning_count'] > 0:
            results['overall_status'] = 'warning'
        
        return results
