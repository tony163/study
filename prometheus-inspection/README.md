# Prometheus 巡检系统

## 项目概述

这是一个基于 Python 的 Prometheus 监控巡检系统，用于自动化检查 Prometheus 服务器的健康状态、性能指标和配置完整性。

## 功能特性

- ✅ **自动指标收集**: 通过 Prometheus API 自动收集关键指标
- ✅ **健康检查**: 多维度健康状态检查（目标、抓取、规则、TSDB、查询性能、内存）
- ✅ **阈值告警**: 可配置的阈值，自动判断警告和严重状态
- ✅ **多格式报告**: 支持 HTML、JSON、CSV 格式报告生成
- ✅ **可视化仪表板**: 提供 Grafana 仪表板模板
- ✅ **告警规则**: 内置完整的 Prometheus 告警规则
- ✅ **易于集成**: 支持命令行、定时任务、CI/CD 集成

## 目录结构

```
prometheus-inspection/
├── inspection/
│   ├── __init__.py           # 包初始化
│   ├── collector.py          # 指标收集器
│   ├── checker.py            # 健康检查器
│   └── reporter.py           # 报告生成器
├── config/
│   ├── prometheus.yml        # Prometheus 配置示例
│   ├── alert_rules.yml       # 告警规则配置
│   └── inspection_config.yml # 巡检配置
├── grafana/
│   └── dashboard.json        # Grafana 仪表板
├── scripts/
│   └── run_inspection.sh     # 巡检执行脚本
├── reports/                  # 报告输出目录
├── requirements.txt          # Python 依赖
├── main.py                   # 主入口
└── README.md                 # 使用说明
```

## 快速开始

### 1. 安装依赖

```bash
cd prometheus-inspection
pip install -r requirements.txt
```

### 2. 配置巡检参数

编辑 `config/inspection_config.yml` 文件：

```yaml
prometheus:
  url: "http://localhost:9090"  # Prometheus 服务器地址
  timeout: 30

thresholds:
  target_down_seconds: 60
  scrape_failure_rate_warning: 5
  scrape_failure_rate_critical: 20
  # ... 其他阈值配置
```

### 3. 运行巡检

#### 方式一：使用 Python 直接运行

```bash
python main.py --config config/inspection_config.yml
```

#### 方式二：使用 Shell 脚本

```bash
chmod +x scripts/run_inspection.sh
./scripts/run_inspection.sh
```

#### 方式三：指定 Prometheus 地址

```bash
python main.py --url http://your-prometheus:9090
```

### 4. 查看报告

报告将生成在 `reports/` 目录下：

- HTML 报告：适合浏览器查看
- JSON 报告：适合程序处理
- CSV 报告：适合 Excel 分析

## 命令行参数

```
用法：python main.py [选项]

选项:
  -c, --config FILE    配置文件路径 (默认：config/inspection_config.yml)
  -u, --url URL        Prometheus 服务器 URL (覆盖配置文件)
  -o, --output DIR     报告输出目录 (默认：reports)
  -f, --format FMTS    报告格式：html json csv (默认：html json)
  -h, --help           显示帮助信息
```

## 检查项目

### 1. 目标健康检查
- 监控目标在线状态
- 目标健康率统计
- 下线目标详情

### 2. 抓取指标检查
- 抓取失败率
- 平均抓取时长
- 抓取间隔

### 3. 规则评估检查
- 规则组数量
- 规则评估延迟
- 评估失败次数

### 4. TSDB 状态检查
- 头部 chunk 数量
- 活跃序列数
- WAL 段数量

### 5. 查询性能检查
- P99 查询延迟
- 并发查询数
- 查询队列长度

### 6. 内存使用检查
- 进程内存使用
- GC 持续时间

## 配置说明

### 阈值配置 (thresholds)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| target_down_seconds | 60 | 目标离线判定时间（秒） |
| scrape_failure_rate_warning | 5 | 抓取失败率警告阈值（%） |
| scrape_failure_rate_critical | 20 | 抓取失败率严重阈值（%） |
| evaluation_delay_warning | 30 | 评估延迟警告阈值（秒） |
| evaluation_delay_critical | 120 | 评估延迟严重阈值（秒） |
| tsdb_head_chunks_warning | 1000000 | TSDB 头部 chunk 警告阈值 |
| tsdb_head_chunks_critical | 5000000 | TSDB 头部 chunk 严重阈值 |
| query_latency_warning | 5 | 查询延迟警告阈值（秒） |
| query_latency_critical | 30 | 查询延迟严重阈值（秒） |

## Grafana 仪表板

导入 `grafana/dashboard.json` 到 Grafana，可以实时查看：

- 目标健康率
- 抓取失败率
- 规则评估延迟
- Prometheus 内存使用
- 目标状态趋势
- 查询延迟趋势
- 目标列表详情

## 告警规则

`config/alert_rules.yml` 包含以下告警：

### Prometheus 告警
- PrometheusTargetDown: 目标下线
- PrometheusConfigReloadFailed: 配置重载失败
- PrometheusScrapeFailureRateHigh: 抓取失败率高
- PrometheusRuleEvaluationSlow: 规则评估缓慢
- PrometheusTSDBCompactionsFailed: TSDB 压缩失败
- PrometheusHighMemoryUsage: 内存使用过高
- PrometheusQueryLatencyHigh: 查询延迟高

### Node 告警
- NodeDown: 节点下线
- NodeCPUHigh: CPU 使用率高
- NodeMemoryHigh: 内存使用率高
- NodeDiskUsageHigh: 磁盘使用率高
- NodeDiskSpaceLow: 磁盘空间即将耗尽

## 定时任务示例

### Cron 定时巡检

```bash
# 每 5 分钟执行一次巡检
*/5 * * * * cd /path/to/prometheus-inspection && ./scripts/run_inspection.sh >> /var/log/prometheus-inspection.log 2>&1
```

### Systemd Timer

创建 `/etc/systemd/system/prometheus-inspection.service`:

```ini
[Unit]
Description=Prometheus Inspection Service
After=network.target

[Service]
Type=oneshot
User=prometheus
WorkingDirectory=/path/to/prometheus-inspection
ExecStart=/usr/bin/python3 main.py --config config/inspection_config.yml
```

创建 `/etc/systemd/system/prometheus-inspection.timer`:

```ini
[Unit]
Description=Run Prometheus Inspection every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=prometheus-inspection.service

[Install]
WantedBy=timers.target
```

启用定时器：

```bash
sudo systemctl enable prometheus-inspection.timer
sudo systemctl start prometheus-inspection.timer
```

## 集成示例

### Docker 运行

```bash
docker run --rm \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/reports:/app/reports \
  python:3.9-slim \
  bash -c "pip install -r /app/requirements.txt && python /app/main.py"
```

### CI/CD 集成 (GitLab CI)

```yaml
prometheus-inspection:
  stage: monitor
  script:
    - pip install -r requirements.txt
    - python main.py --url $PROMETHEUS_URL
  artifacts:
    paths:
      - reports/
    expire_in: 1 week
```

## 故障排除

### 常见问题

1. **连接 Prometheus 失败**
   - 检查 Prometheus 服务是否运行
   - 确认 URL 和端口正确
   - 检查网络连通性和防火墙设置

2. **指标收集不完整**
   - 增加超时时间配置
   - 检查 Prometheus 日志
   - 确认 API 权限

3. **报告生成失败**
   - 检查输出目录权限
   - 确认依赖包已安装
   - 查看错误日志

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
