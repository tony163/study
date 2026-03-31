"""
Prometheus 巡检系统 - 指标收集器
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional


class PrometheusCollector:
    """Prometheus 指标收集器"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化收集器
        
        Args:
            base_url: Prometheus 服务器地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送 HTTP 请求到 Prometheus API"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', {})
            else:
                raise Exception(f"API error: {data.get('error', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def query(self, query: str, timestamp: Optional[int] = None) -> List[Dict]:
        """
        执行即时查询
        
        Args:
            query: PromQL 查询语句
            timestamp: 可选的时间戳（Unix 时间戳）
            
        Returns:
            查询结果列表
        """
        params = {'query': query}
        if timestamp:
            params['time'] = timestamp
        result = self._make_request('query', params)
        return result.get('result', [])
    
    def query_range(self, query: str, start: int, end: int, step: int) -> List[Dict]:
        """
        执行范围查询
        
        Args:
            query: PromQL 查询语句
            start: 开始时间戳
            end: 结束时间戳
            step: 步长（秒）
            
        Returns:
            查询结果列表
        """
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        result = self._make_request('query_range', params)
        return result.get('result', [])
    
    def get_targets(self) -> List[Dict]:
        """获取所有监控目标状态"""
        return self._make_request('targets')
    
    def get_rules(self) -> Dict:
        """获取所有告警规则"""
        return self._make_request('rules')
    
    def get_alerts(self) -> List[Dict]:
        """获取当前活跃的告警"""
        return self._make_request('alerts')
    
    def get_metadata(self) -> Dict:
        """获取 Prometheus 元数据"""
        return self._make_request('status/config')
    
    def get_tsdb_status(self) -> Dict:
        """获取 TSDB 状态"""
        return self._make_request('status/tsdb')
    
    # ========== 健康检查指标收集方法 ==========
    
    def collect_target_health(self) -> Dict[str, Any]:
        """
        收集目标健康状态
        
        Returns:
            目标健康状态字典
        """
        targets_data = self.get_targets()
        targets = targets_data.get('activeTargets', [])
        
        health_summary = {
            'total': len(targets),
            'up': 0,
            'down': 0,
            'details': []
        }
        
        for target in targets:
            is_up = target.get('health', '').lower() == 'up'
            if is_up:
                health_summary['up'] += 1
            else:
                health_summary['down'] += 1
            
            health_summary['details'].append({
                'job': target.get('labels', {}).get('job', 'unknown'),
                'instance': target.get('labels', {}).get('instance', 'unknown'),
                'health': target.get('health', 'unknown'),
                'last_scrape': target.get('lastScrape', ''),
                'last_error': target.get('lastError', ''),
                'scrape_duration': target.get('lastScrapeDuration', 0)
            })
        
        return health_summary
    
    def collect_scrape_metrics(self) -> Dict[str, Any]:
        """
        收集抓取相关指标
        
        Returns:
            抓取指标字典
        """
        metrics = {}
        
        # 抓取失败率
        failure_query = '''
            sum(rate(prometheus_target_scrapes_exceeded_sample_limit_total[5m])) 
            / sum(rate(prometheus_target_scrapes_total[5m])) * 100
        '''
        try:
            result = self.query(failure_query)
            if result:
                metrics['scrape_failure_rate'] = float(result[0].get('value', [None, 0])[1])
        except Exception:
            metrics['scrape_failure_rate'] = None
        
        # 平均抓取时长
        duration_query = '''
            avg(prometheus_target_interval_length_seconds{quantile="0.5"})
        '''
        try:
            result = self.query(duration_query)
            if result:
                metrics['avg_scrape_duration'] = float(result[0].get('value', [None, 0])[1])
        except Exception:
            metrics['avg_scrape_duration'] = None
        
        # 抓取间隔
        interval_query = '''
            avg(prometheus_target_interval_length_seconds_count)
        '''
        try:
            result = self.query(interval_query)
            if result:
                metrics['scrape_interval'] = float(result[0].get('value', [None, 0])[1])
        except Exception:
            metrics['scrape_interval'] = None
        
        return metrics
    
    def collect_rule_evaluation_metrics(self) -> Dict[str, Any]:
        """
        收集规则评估相关指标（包括所有 alert_rules 的详细信息）
        
        Returns:
            规则评估指标字典
        """
        metrics = {}
        
        # 获取所有规则组及其详细规则信息
        rules_data = self.get_rules()
        groups = rules_data.get('groups', [])
        metrics['groups'] = groups  # 包含所有规则的详细信息（状态、类型等）
        metrics['rule_groups_count'] = len(groups)
        
        # 总规则数
        total_rules = sum(len(group.get('rules', [])) for group in groups)
        metrics['total_rules'] = total_rules
        
        # 评估延迟
        delay_query = '''
            max(prometheus_rule_group_last_duration_seconds)
        '''
        try:
            result = self.query(delay_query)
            if result:
                metrics['max_evaluation_duration'] = float(result[0].get('value', [None, 0])[1])
        except Exception:
            metrics['max_evaluation_duration'] = None
        
        # 规则评估失败次数
        fail_query = '''
            sum(increase(prometheus_rule_evaluation_failures_total[1h]))
        '''
        try:
            result = self.query(fail_query)
            if result:
                metrics['evaluation_failures'] = int(float(result[0].get('value', [None, 0])[1]))
        except Exception:
            metrics['evaluation_failures'] = None
        
        return metrics
    
    def collect_tsdb_metrics(self) -> Dict[str, Any]:
        """
        收集 TSDB 相关指标
        
        Returns:
            TSDB 指标字典
        """
        metrics = {}
        
        # TSDB 状态
        try:
            tsdb_status = self.get_tsdb_status()
            metrics['tsdb_status'] = tsdb_status
        except Exception as e:
            metrics['tsdb_status'] = {'error': str(e)}
        
        # 头部 chunk 数量
        chunks_query = '''
            prometheus_tsdb_head_chunks
        '''
        try:
            result = self.query(chunks_query)
            if result:
                metrics['head_chunks'] = int(float(result[0].get('value', [None, 0])[1]))
        except Exception:
            metrics['head_chunks'] = None
        
        # 活跃序列数
        series_query = '''
            prometheus_tsdb_head_series
        '''
        try:
            result = self.query(series_query)
            if result:
                metrics['head_series'] = int(float(result[0].get('value', [None, 0])[1]))
        except Exception:
            metrics['head_series'] = None
        
        # WAL 大小
        wal_size_query = '''
            prometheus_tsdb_wal_segment_current
        '''
        try:
            result = self.query(wal_size_query)
            if result:
                metrics['wal_segments'] = int(float(result[0].get('value', [None, 0])[1]))
        except Exception:
            metrics['wal_segments'] = None
        
        return metrics
    
    def collect_query_performance(self) -> Dict[str, Any]:
        """
        收集查询性能指标
        
        Returns:
            查询性能指标字典
        """
        metrics = {}
        
        # P99 查询延迟
        latency_query = '''
            histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket{handler="/api/v1/query"}[5m]))
        '''
        try:
            result = self.query(latency_query)
            if result:
                metrics['p99_query_latency'] = float(result[0].get('value', [None, 0])[1])
        except Exception:
            metrics['p99_query_latency'] = None
        
        # 当前并发查询数
        concurrent_query = '''
            prometheus_engine_queries
        '''
        try:
            result = self.query(concurrent_query)
            if result:
                metrics['concurrent_queries'] = int(float(result[0].get('value', [None, 0])[1]))
        except Exception:
            metrics['concurrent_queries'] = None
        
        # 查询队列长度
        queue_query = '''
            prometheus_engine_query_queue_length
        '''
        try:
            result = self.query(queue_query)
            if result:
                metrics['query_queue_length'] = int(float(result[0].get('value', [None, 0])[1]))
        except Exception:
            metrics['query_queue_length'] = None
        
        return metrics
    
    def collect_memory_metrics(self) -> Dict[str, Any]:
        """
        收集内存使用指标
        
        Returns:
            内存指标字典
        """
        metrics = {}
        
        # 进程内存使用
        memory_query = '''
            process_resident_memory_bytes{job="prometheus"}
        '''
        try:
            result = self.query(memory_query)
            if result:
                metrics['memory_bytes'] = int(float(result[0].get('value', [None, 0])[1]))
                metrics['memory_mb'] = metrics['memory_bytes'] / (1024 * 1024)
                metrics['memory_gb'] = metrics['memory_bytes'] / (1024 * 1024 * 1024)
        except Exception:
            metrics['memory_bytes'] = None
            metrics['memory_mb'] = None
            metrics['memory_gb'] = None
        
        # Go GC 统计
        gc_query = '''
            go_gc_duration_seconds{quantile="0.5"}
        '''
        try:
            result = self.query(gc_query)
            if result:
                metrics['gc_duration'] = float(result[0].get('value', [None, 0])[1])
        except Exception:
            metrics['gc_duration'] = None
        
        return metrics
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """
        收集所有指标
        
        Returns:
            包含所有指标的字典
        """
        collection_time = datetime.now().isoformat()
        
        return {
            'collection_time': collection_time,
            'target_health': self.collect_target_health(),
            'scrape_metrics': self.collect_scrape_metrics(),
            'rule_evaluation': self.collect_rule_evaluation_metrics(),
            'tsdb_metrics': self.collect_tsdb_metrics(),
            'query_performance': self.collect_query_performance(),
            'memory_metrics': self.collect_memory_metrics()
        }
