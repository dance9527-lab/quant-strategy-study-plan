# Coder Agent 第七轮工程审计报告

> 审计时间：2026-04-30 15:55 CST
> 审计角色：Coder Agent（代码架构和工程实现专家）
> 审计对象：quant_strategy_plan.md + quant_strategy_research_plan_detailed.md
> 审计范围：日调仓、模型更新训练、数据流、测试方案的工程实现可行性

---

## 总体工程评估

### 评分：7.0/10

**优势**：数据底座扎实（17.6M行价格、16.6M行估值、15.4M行特征/标签已入仓），验证框架设计严谨（walk-forward、purge/embargo、PIT审计），审计追踪体系完备（manifest/hash/access log）。

**核心工程风险**：日选股（S1-D）的工程复杂度被严重低估——它不是"把月选股改成每天跑"，而是一个全新的实时数据管道、订单状态机和持仓会计系统。

---

## 1. 日调仓的工程实现

### 1.1 需要新增的代码模块

文档中 S1-D 日选股要求"每日盘后重算分数并生成 T+1 候选"，工程上需要以下新模块：

| 模块 | 功能 | 复杂度 | 估算工期 |
|------|------|--------|---------|
| `DailyScoringEngine` | 每日盘后读取最新行情→因子计算→模型预测→输出候选清单 | 中 | 3-5天 |
| `DailyOrderStateMachine` | 订单生命周期管理：挂单→成交/失败→延迟→解锁→反转统计 | 高 | 5-8天 |
| `DailyPositionLedger` | 每日持仓会计：重叠持仓、T+1约束、100股整数手、现金结算 | 高 | 5-8天 |
| `DailyTurnoverCapacityReport` | 日换手、成本拖累、ADV参与率、成交失败率、容量上限 | 中 | 3-5天 |
| `DailySelectionRebalanceV1` | 候选清单格式：as_of_date/trade_date/asset_id/score/rank/selected_flag/target_weight/model_version/feature_cutoff/label_cutoff/no_trade_reason | 低 | 1-2天 |
| `DailyOrdersAudit` | 涨停买失败、跌停卖失败、停牌延迟、解锁后收益统计 | 中 | 3-5天 |

**小计**：约 20-33 人天（单人），或 2-3 周密集开发。

### 1.2 与现有 Walk-Forward 框架的集成难度

**核心困难**：现有 walk-forward 框架是为月选股设计的——每个 step 约 21 个交易日、训练窗口 5 年、每 63 个交易日重训。日选股需要：

1. **日度决策日历生成**：`walk_forward_calendar_S1D_v1` 需要为每个交易日生成 step，而非每月。从 2010 年到 2025 年约 3,600+ 个交易日 = 3,600+ 个 step。这与"24 步最低验收"的表述存在语义冲突——文档说"24 步只是最低验收门槛"，但日选股的 OOT 步数是月选股的 ~20 倍。

2. **训练窗口重叠问题**：S1-D 每日预测但每 63 个交易日重训。这意味着相邻 62 天的预测使用同一个冻结模型。需要工程上实现"模型版本管理"：记录哪个预测用了哪个冻结模型版本。

3. **Purge 计算**：文档规定 `purge_days >= max(label_horizon*3, 40)`。对 1 日标签，purge 仍是 40 个交易日（不是 3 天）。这是正确的保守设计，但需要在代码中显式实现，避免有人误用 `purge_days=3`。

**集成难度评估**：中高。主要工作不在模型训练本身，而在日度预测管线、订单状态机和持仓会计的工程实现。

### 1.3 日频数据处理的性能要求

| 数据操作 | 数据量 | 频率 | 性能要求 |
|---------|--------|------|---------|
| 因子计算（9 类 P1） | 15.4M 行特征面板 | 每日增量 | < 30秒（增量只算最新截面） |
| 模型预测 | ~5000 只股票 × 9+ 因子 | 每日 | < 10秒 |
| Walk-forward 全量回测 | 15.4M 行 × 3600+ step | 一次性 | 8-24 小时（取决于模型复杂度） |
| 订单状态机更新 | 当日 ~100-500 笔订单 | 每日 | < 5秒 |

**性能瓶颈**：walk-forward 全量回测。月选股 24-50 步 × 5 年训练窗口，每步训练一次模型。日选股若按日度 step，3600+ 步 × 每步重新计算因子截面 = 计算量巨大。**建议**：日选股回测时，因子计算可以预计算整个面板（已有 `features/market_daily_v1`），只需在每个重训 step（63 个交易日）做模型训练，中间步只做预测。

### 1.4 日频因子计算的计算成本

当前 P1 因子（市值、流动性、动量、反转、波动率、beta、行业中性）大部分是滚动窗口计算，增量更新成本低。但：

- **ADV 计算**：需要 20/60/120 日滚动窗口，每个交易日更新约 O(N) 复杂度，N ≈ 5000 只股票。
- **行业中性化**：需要每日横截面回归，O(N×K) 复杂度，K = 行业数 ≈ 30-50。
- **Gram-Schmidt 正交化**：每个调仓日需要矩阵运算，O(N×F²)，F = 因子数。

**估算**：日频因子增量计算约 5-15 秒/天，可接受。全量重算（含正交化）约 5-10 分钟/次。

---

## 2. 模型更新训练的工程实现

### 2.1 每日模型更新的代码架构

文档规定"默认每 63 个交易日重训一次"，S1-D "每日重训只作后置敏感性，不作为 S1-D 默认"。这意味着：

```
Day 1-63: 使用 Model_v1 预测
Day 64: 重训 → Model_v2
Day 64-126: 使用 Model_v2 预测
...
```

**需要的架构**：

```python
class ModelVersionManager:
    """管理模型版本和冻结模型"""
    
    def __init__(self, refit_interval=63):
        self.refit_interval = refit_interval
        self.models = {}  # version -> model
        self.metadata = {}  # version -> {train_end, params_hash, ...}
    
    def should_refit(self, current_day, last_refit_day):
        return (current_day - last_refit_day) >= self.refit_interval
    
    def get_active_model(self, prediction_date):
        """返回 prediction_date 时可用的最新冻结模型"""
        # 必须确保 model.train_end + purge_days <= prediction_date
        pass
    
    def save_model(self, model, version, metadata):
        """持久化模型和元数据"""
        pass
```

**工程难点**：
1. 模型持久化格式（pickle/joblib/onnx）和版本索引
2. 训练截止日与 purge/embargo 的约束检查
3. 重训触发条件（交易日计数 vs 日历日）

### 2.2 模型版本管理和回滚机制

**当前状态**：文档提到了 `model_version`、`train_rows_hash`、`params_hash`、`feature_cutoff`、`label_cutoff`，但没有具体的版本管理实现方案。

**建议架构**：

```
models/
├── S1-M/
│   ├── v001/
│   │   ├── model.joblib
│   │   ├── metadata.json  # train_end, params_hash, feature_hash, etc.
│   │   └── training_log.txt
│   ├── v002/
│   └── ...
├── S1-D/
│   ├── v001/
│   └── ...
└── registry.json  # version -> {track_id, train_end, status, ...}
```

**回滚机制**：
- 保留最近 3 个版本的模型文件
- `registry.json` 记录每个版本的状态：`active`/`frozen`/`deprecated`/`quarantined`
- 当 concept shift 告警触发 red quarantine 时，回滚到上一个 stable 版本

**工期估算**：3-5 天实现基础版本管理，2-3 天实现回滚机制。

### 2.3 模型更新的自动化流程

需要一个调度器来管理日频管线：

```python
class DailyPipeline:
    """每日盘后管线"""
    
    def run(self, trade_date):
        # 1. 数据检查：确认当日行情已入库
        self.check_data_availability(trade_date)
        
        # 2. 因子计算：增量更新当日截面因子
        factors = self.compute_factors(trade_date)
        
        # 3. 模型检查：是否需要重训
        if self.model_manager.should_refit(trade_date):
            self.retrain_model(trade_date)
        
        # 4. 预测：生成候选清单
        candidates = self.predict(trade_date, factors)
        
        # 5. 订单生成：根据信号生成目标仓位
        orders = self.generate_orders(candidates, trade_date)
        
        # 6. 审计：记录所有决策
        self.audit(trade_date, factors, candidates, orders)
```

**工期估算**：5-8 天（含错误处理、日志、重试机制）。

### 2.4 与现有训练管道的集成

当前仓库中有 `build_warehouse.py`、`apply_r7_feature_label_panel.py` 等脚本，但没有独立的模型训练管道。qant-codex-20260429 中有 `ml/` 目录但未审计其代码质量。

**集成策略**：
1. 新建 `D:\quantum_a0\quant-strategy-study-plan\pipeline\` 目录
2. 复用 warehouse 的数据加载逻辑（`prices_daily_returns`、`valuation_daily` 等 Parquet 读取）
3. 新建训练/预测/回测模块
4. 不直接依赖 qant-codex 的旧代码（已被判定为反例）

**工期估算**：2-3 天搭建项目骨架。

---

## 3. 数据流设计

### 3.1 日频数据的 ETL 流程

当前 warehouse 数据更新流程不明确。文档提到 `warehouse_build_manifest.json` 记录"最大数据日期"为 2026-04-27，但没有自动化的日频数据更新管线。

**需要的 ETL 流程**：

```
T日 16:00 后
  ↓
[数据源] Tushare 日频行情 → prices_daily_unadjusted (增量)
  ↓
[ETL] 计算收益 → prices_daily_returns (增量)
  ↓
[ETL] 更新估值 → valuation_daily (增量)
  ↓
[ETL] 更新可交易性 → tradability_daily_enriched (增量)
  ↓
[ETL] 更新 universe → universe_daily (增量)
  ↓
[因子计算] 更新 features/market_daily_v1 (增量)
  ↓
[模型预测] 生成候选清单 → daily_selection_rebalance_v1
  ↓
[订单审计] daily_orders_audit
```

**工程难点**：
1. Tushare 数据拉取的可靠性和延迟（部分接口需要更高积分）
2. 增量更新 vs 全量重算的边界
3. 数据质量检查（缺失值、异常值、重复键）的自动化

**工期估算**：5-8 天实现基础 ETL，3-5 天实现质量检查。

### 3.2 因子计算的调度机制

文档中 9 类 P1 因子的计算依赖关系：

```
独立因子（可并行）：
  - 市值 ← valuation_daily.total_mv
  - 流动性 ← tradability_daily_enriched.amount + valuation_daily.turnover_rate
  - 动量 ← prices_daily_returns.return_adjusted_pit (多窗口)
  - 反转 ← prices_daily_returns.return_adjusted_pit (短窗口)
  - 波动率 ← prices_daily_returns (滚动标准差)
  - 风险 ← prices_daily_returns + benchmarks (回归)
  - 交易约束 ← tradability_daily_enriched (直接读取)
  - 行业 ← industry_classification (直接映射)

依赖因子（需要先计算）：
  - 行业中性化 ← 行业因子 + 所有其他因子 (横截面回归)
  - 正交化 ← 所有因子 (Gram-Schmidt)
```

**建议**：使用 DAG 调度器（如 Airflow 的简化版或自定义 TaskGraph），支持因子级别的并行计算和依赖管理。

**工期估算**：3-5 天实现基础 DAG 调度。

### 3.3 模型训练的触发条件

文档明确：
- 默认每 63 个交易日重训
- S1-M 每 21 个交易日调仓/预测
- S1-D 每日预测但不默认每日重训

**触发逻辑**：

```python
def should_retrain(trade_day_index, refit_interval=63):
    """trade_day_index: 从 walk-forward 起点开始的交易日序号"""
    return trade_day_index % refit_interval == 0

def should_predict_s1m(trade_day_index, predict_interval=21):
    return trade_day_index % predict_interval == 0

def should_predict_s1d(trade_day_index):
    return True  # 每日预测
```

### 3.4 预测结果的输出格式

文档定义了 `daily_selection_rebalance_v1` 的字段：

```
as_of_date, trade_date, asset_id, score, rank, horizon,
selected_flag, target_weight, model_version, feature_cutoff,
label_cutoff, no_trade_reason
```

**工程建议**：
- 输出格式：Parquet（高效、schema 自描述）
- 目录结构：`outputs/S1-D/daily_selection/{YYYY-MM-DD}.parquet`
- 增量写入：每日一个文件，避免大文件追加

---

## 4. 测试方案

### 4.1 单元测试覆盖范围

| 模块 | 测试重点 | 优先级 |
|------|---------|--------|
| 因子计算 | 单因子值与手工计算一致、缺失处理、winsorize 边界 | P0 |
| 标签计算 | forward return 方向正确、purge 边界、label maturity | P0 |
| 股票池过滤 | 涨跌停/停牌/ST/上市年龄的过滤逻辑 | P0 |
| 订单状态机 | 涨停买失败、跌停卖失败、T+1 约束、100 股整数手 | P0 |
| 持仓会计 | 现金结算、持仓市值、收益率计算 | P0 |
| 成本计算 | 佣金/印花税/过户费/滑点的分档计算 | P1 |
| Walk-forward 日历 | step 边界、purge/embargo 约束、holdout 隔离 | P0 |
| 模型版本管理 | 版本索引、冻结模型查询、回滚 | P1 |
| PIT 合规检查 | available_at <= decision_time、未来信息检测 | P0 |

**建议覆盖率目标**：核心模块 > 90%，辅助模块 > 70%。

### 4.2 集成测试方案

| 测试场景 | 验证内容 | 频率 |
|---------|---------|------|
| 端到端日度管线 | 数据入库→因子计算→预测→订单→审计 的完整流程 | 每次代码变更 |
| Walk-forward 一致性 | 相同参数多次运行结果一致（确定性） | 每次代码变更 |
| 数据质量门禁 | leakage_check PASS、无重复键、available_at 合规 | 每次数据更新 |
| 模型重训触发 | 63 个交易日后正确触发重训 | 每次代码变更 |
| 订单失败处理 | 涨跌停/停牌场景下的订单状态正确 | 每次代码变更 |

### 4.3 回测验证流程

```
1. 数据准备
   - 确认 warehouse 数据完整
   - 运行 leakage_check
   - 生成 walk-forward calendar

2. 因子计算
   - 计算全量面板因子
   - 因子 PIT 审计
   - 因子覆盖率报告

3. 模型训练
   - 按 walk-forward step 逐步训练
   - 记录每个 step 的模型版本和参数

4. 组合回测
   - 按日/月调仓
   - 计算成本后收益
   - 订单状态机审计

5. 统计检验
   - Newey-West HAC IC t-stat
   - Block bootstrap p-value
   - Deflated Sharpe Ratio

6. 报告生成
   - 分年度/市场状态/市值
   - 拥挤容量分析
   - Concept shift 诊断
```

### 4.4 A/B 测试框架

文档中 S1-M 和 S1-D 本身就是两条平行主线，可以视为 A/B 测试：

| 维度 | S1-M（对照） | S1-D（实验） |
|------|------------|------------|
| 调仓频率 | ~21 交易日 | 每日 |
| 标签 | 20 日 forward | 1/5 日 forward |
| 换手 | 低 | 高 |
| 成本敏感性 | 低 | 高 |

**工程实现**：
- 共享同一数据底座和因子库
- 独立的 walk-forward calendar
- 独立的订单审计和容量报告
- 共享统计检验框架

---

## 5. 整体方案审查

### 5.1 技术方案实现困难评估

| 方案 | 实现难度 | 主要困难 | 建议 |
|------|---------|---------|------|
| 月选股 walk-forward | 中 | 面板已就绪，主要工作是训练和回测框架 | 可立即启动 |
| 日选股 walk-forward | **高** | 日度订单状态机、持仓会计、容量报告是全新模块 | 先实现月选股，再扩展日选股 |
| 因子正交化 | 低 | Gram-Schmidt 实现简单，`scipy.linalg.qr` 即可 | 1-2天 |
| 指数衰减权重 | 低 | 公式明确，sklearn/LightGBM 支持 sample_weight | 1天 |
| Concept shift 告警 | 中 | 需要实现成熟 IC 状态机和 yellow/red 触发 | 3-5天 |
| Walk-forward 日历生成 | 中 | 交易日计算、purge/embargo 约束、holdout 隔离 | 3-5天 |
| 三层 universe 审计 | 中 | 需要审计现有 `universe_daily` 构造逻辑 | 3-5天 |
| 拥挤容量分析 | 中 | 因子重叠、成交额占比、左尾 CVaR 计算 | 3-5天 |
| 每日 ETL 管线 | **高** | 数据可靠性、增量更新、质量检查 | 5-8天 |
| 模型版本管理 | 中 | 持久化、索引、回滚 | 3-5天 |

### 5.2 工期和资源需求估算

#### Phase A0：审计和日历固化（阻塞项）

| 任务 | 工期 | 依赖 |
|------|------|------|
| walk-forward 日历生成（S1-M + S1-D） | 3-5天 | 交易日历数据 |
| holdout access log 建立 | 1天 | 无 |
| universe_daily 构造审计 | 3-5天 | 脚本源码 |
| 三层 universe 分离 | 2-3天 | universe_daily 审计 |
| benchmark 覆盖审计 | 1天 | benchmarks 数据 |
| validation_params.json 对齐 | 1天 | 文档参数 |
| **小计** | **11-16天** | |

#### Phase A-M：月选股强基线

| 任务 | 工期 | 依赖 |
|------|------|------|
| 单因子 IC/RankIC/ICIR 计算 | 3-5天 | 面板数据 |
| 等权/ICIR/正交化复合因子 | 3-5天 | 单因子结果 |
| 线性模型（Ridge/ElasticNet） | 2-3天 | 因子面板 |
| LightGBM/Ranker | 2-3天 | 因子面板 |
| 组合回测引擎（月度） | 5-8天 | 预测结果 |
| 订单审计（月度） | 3-5天 | 回测引擎 |
| 容量压力测试 | 3-5天 | 回测引擎 |
| 统计检验（HAC/bootstrap/DSR） | 3-5天 | OOT 结果 |
| **小计** | **24-39天** | |

#### Phase A-D：日选股强基线

| 任务 | 工期 | 依赖 |
|------|------|------|
| 日度决策日历 | 2-3天 | 交易日历 |
| 日度因子计算管线 | 3-5天 | 因子代码复用 |
| 日度预测管线 | 3-5天 | 模型代码复用 |
| 日度订单状态机 | 5-8天 | 无（全新） |
| 日度持仓会计 | 5-8天 | 订单状态机 |
| 日度换手/容量报告 | 3-5天 | 持仓会计 |
| 日度回测集成 | 5-8天 | 以上所有 |
| 统计检验（日度 IC 序列） | 3-5天 | OOT 结果 |
| **小计** | **29-47天** | |

#### Phase B-E：后续阶段

| 阶段 | 工期估算 | 说明 |
|------|---------|------|
| Phase B：风险状态和组合约束 | 15-25天 | 市场状态变量、仓位开关、熔断规则 |
| Phase C：外部数据 ETL | 15-25天 | 5-7 个数据源的 ETL + PIT 审计 |
| Phase D：特色 alpha | 20-30天 | 筹码/涨停/分钟/期权 |
| Phase E：高级模型 | 15-20天 | LSTM/1D-CNN 对照 |

#### 总工期估算

| 场景 | 工期 | 说明 |
|------|------|------|
| 最小可行（仅 S1-M） | 35-55 天 | 5-8 周 |
| 双主线（S1-M + S1-D） | 64-102 天 | 10-16 周 |
| 含风险和外部数据 | 94-152 天 | 15-24 周 |

**注意**：以上为单人全职估算。若两人并行（一人 S1-M、一人 S1-D + ETL），双主线可压缩到 6-10 周。

### 5.3 资源需求

| 资源 | 当前状态 | 缺口 |
|------|---------|------|
| Python 环境 | ptorch conda 已就绪 | 无 |
| 核心包 | lightgbm/xgboost/sklearn/torch 已安装 | 无 |
| 数据 | warehouse 17.6M 行已入仓 | ETL 自动化管线缺失 |
| 计算资源 | Intel Arc B390 16.5GB | walk-forward 全量回测可能需要 8-24 小时 |
| 代码仓库 | quant-strategy-study-plan Git 项目 | 缺少 pipeline 代码目录 |
| 测试框架 | 无 | 需要从零搭建 |

### 5.4 关键工程风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 日选股订单状态机过于复杂 | 延期 1-2 周 | 先实现简化版（只处理涨跌停/停牌），后续迭代 |
| Walk-forward 全量回测耗时过长 | 调试周期拉长 | 先用 24 步 smoke test，再跑全量 |
| Tushare 数据拉取不稳定 | ETL 管线中断 | 实现重试机制和数据完整性检查 |
| 模型版本管理混乱 | 结果不可复现 | 强制 metadata 记录和 hash 校验 |
| 估值缺口处理不当 | 因子计算错误 | 严格执行 drop-gap/no-valuation/ffill 三口径 |
| 代码质量不可控 | 审计困难 | 强制单元测试和代码审查 |

---

## 6. 工程建议

### 6.1 优先级调整建议

1. **先 S1-M 后 S1-D**：月选股的工程复杂度远低于日选股。先完成 S1-M 的完整管线（因子→模型→回测→审计），再扩展到 S1-D，可以复用大量代码。

2. **Walk-forward 框架先行**：在写任何模型代码之前，先把 walk-forward 日历生成、purge/embargo 逻辑、holdout 隔离做好。这是所有验证的基础。

3. **因子计算与模型训练解耦**：因子面板可以预计算并缓存（已有 `features/market_daily_v1`），模型训练只读取缓存面板。这样因子计算和模型训练可以独立迭代。

4. **订单状态机独立模块**：订单状态机是日选股的核心难点，应该作为独立模块设计和测试，不要嵌入回测引擎。

### 6.2 代码架构建议

```
D:\quantum_a0\quant-strategy-study-plan\
├── pipeline/
│   ├── __init__.py
│   ├── config.py              # 全局配置和参数
│   ├── data/
│   │   ├── warehouse_loader.py  # warehouse 数据加载
│   │   ├── daily_etl.py         # 日频 ETL 管线
│   │   └── quality_checks.py    # 数据质量检查
│   ├── factors/
│   │   ├── base.py              # 因子基类
│   │   ├── market_factors.py    # 市值/流动性/动量等
│   │   ├── risk_factors.py      # beta/波动率等
│   │   ├── industry.py          # 行业中性化
│   │   └── orthogonalize.py     # Gram-Schmidt 正交化
│   ├── models/
│   │   ├── base.py              # 模型基类
│   │   ├── linear.py            # Ridge/ElasticNet
│   │   ├── tree.py              # LightGBM/XGBoost
│   │   ├── ranker.py            # LightGBM Ranker
│   │   └── version_manager.py   # 模型版本管理
│   ├── validation/
│   │   ├── walk_forward.py      # Walk-forward 日历和执行
│   │   ├── ic_analysis.py       # IC/RankIC/ICIR/HAC
│   │   ├── bootstrap.py         # Block bootstrap
│   │   ├── overfitting.py       # DSR/PBO
│   │   └── holdout.py           # Holdout 管理
│   ├── portfolio/
│   │   ├── universe.py          # 三层 universe
│   │   ├── order_engine.py      # 订单生成
│   │   ├── order_state_machine.py  # 订单状态机
│   │   ├── position_ledger.py   # 持仓会计
│   │   └── cost_model.py        # 成本模型
│   ├── reporting/
│   │   ├── ic_report.py         # IC 报告
│   │   ├── portfolio_report.py  # 组合报告
│   │   ├── capacity_report.py   # 容量报告
│   │   └── concept_shift.py     # Concept shift 诊断
│   └── daily_pipeline.py        # 日度管线调度
├── tests/
│   ├── test_factors.py
│   ├── test_labels.py
│   ├── test_universe.py
│   ├── test_order_state_machine.py
│   ├── test_position_ledger.py
│   ├── test_walk_forward.py
│   └── test_cost_model.py
├── configs/
│   ├── s1m_config.yaml          # S1-M 配置
│   └── s1d_config.yaml          # S1-D 配置
└── outputs/
    ├── S1-M/
    └── S1-D/
```

### 6.3 测试策略建议

1. **TDD（测试驱动开发）**：先写测试再写实现，特别是订单状态机和持仓会计。
2. **快照测试**：walk-forward 日历、因子面板等确定性输出用快照测试（golden file）。
3. **回归测试**：每次代码变更后自动运行 leakage_check + 核心模块单元测试。
4. **性能基准**：记录每个模块的运行时间，设置性能回归告警。

### 6.4 文档中需要补充的工程细节

1. **日度 OOT 步数**：文档说"24 步最低验收"，但日选股的 OOT 步数应为 ~3600 步。需要明确：日选股的"步"是交易日还是月度汇总？
2. **模型重训与预测的解耦**：需要明确"冻结模型"的工程含义——是保存模型文件还是只保存预测结果？
3. **日度 ETL 的数据依赖**：需要明确 Tushare 数据拉取的 SLA（最晚几点数据可用？延迟如何处理？）
4. **增量 vs 全量**：因子计算、模型预测、回测哪些是增量的、哪些是全量的？

---

## 7. 总结

### 可行性结论

方案整体**可行**，但工程实现量被低估。核心风险在日选股（S1-D）的订单状态机、持仓会计和容量报告——这些是全新的工程模块，不是简单修改月选股代码。

### 推荐执行路径

```
Week 1-2:  Phase A0（审计和日历固化）
Week 3-5:  S1-M 因子+模型+回测框架
Week 6-8:  S1-M 组合回测+统计检验+审计
Week 9-11: S1-D 扩展（复用 S1-M 框架，新增订单状态机和持仓会计）
Week 12-14: S1-D 完整回测+容量报告
Week 15+:  Phase B/C（风险状态、外部数据）
```

### 与前几轮审计的工程视角补充

前几轮审计主要关注统计和策略层面的正确性。本轮从工程实现角度补充：

1. **日选股不是"把月选股改成每天跑"**：它需要全新的订单状态机、持仓会计和容量报告模块。
2. **Walk-forward 日历生成是基础设施**：没有它，所有验证都无法进行。应最先完成。
3. **因子面板预计算是性能关键**：15.4M 行的因子面板应该预计算并缓存，不要在每次回测时重新计算。
4. **模型版本管理不可忽视**：63 个交易日重训一次意味着 S1-D 有 ~60 个模型版本，S1-M 有 ~12 个。没有版本管理，结果不可复现。
5. **测试先行**：订单状态机和持仓会计是最容易出 bug 的模块，必须 TDD。

---

*审计完成。以上评估基于对两份策略文档和现有代码结构的工程分析。*
