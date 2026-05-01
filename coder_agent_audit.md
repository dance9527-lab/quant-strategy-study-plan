# Coder Agent 独立审计报告

> 审计人角色：量化开发/数据工程/架构设计专家
> 审计日期：2026-05-01
> 审计范围：quant_strategy_plan.md、quant_strategy_research_plan_detailed.md、DATA_USAGE_GUIDE.md、WAREHOUSE_README.md
> 审计依据：文档内容 + 量化系统工程实践经验

---

## 1. 数据架构审计

### 1.1 分区策略评估

**现状**：核心表（`prices_daily_unadjusted`、`prices_daily_returns`、`valuation_daily`、`tradability_daily`）按年度分区 Parquet 存储。`features/market_daily_v1` 和 `labels/forward_returns_v1` 同样按年度分区，各 15,420,654 行。

**评估**：

- **年度分区粒度合理**。A 股日频数据从 1990 年至今约 36 年，每年分区大小在 2,553 行（1991）到 1,313,629 行（2025）之间。早期年份分区过小（<10,000 行），Parquet 文件元数据开销占比偏高，但对整体性能影响有限。
- **跨年度查询是主要性能瓶颈**。walk-forward 训练窗口为 5 年，意味着每次训练需要读取 5 个分区。24 步 OOT × 5 分区/步 = 至少 120 次分区读取。如果做全量 OOT step（约 40-60 步），分区读取次数可达 200-300 次。
- **建议**：考虑对高频访问的 `features` 和 `labels` 表增加一个按 `(year, month)` 的二级分区，或预生成 5 年滚动窗口的内存映射缓存（memory-mapped parquet），减少 walk-forward 过程中的重复 I/O。

### 1.2 数据一致性与完整性

**现状**：文档声称 `prices_daily_unadjusted` 和 `prices_daily_returns` 行数一致（17,599,789），`tradability_daily` 和 `universe_daily` 行数一致（18,177,689），features 和 labels 行数一致（15,420,654）。

**评估**：

- **行数一致性检查是必要但不充分的**。仅检查总行数一致不等于 `(asset_id, trade_date)` 主键完全对齐。应增加主键交叉验证：`prices` 表的每个 `(asset_id, trade_date)` 是否都在 `returns` 表中有对应行，反之亦然。
- **`valuation_daily` 与收益表 key 不完全一致**（文档已披露：extra 5,562 key, missing 146,208 key）。146,208 个缺失 key 是一个显著的数据缺口，假设 2000-2026 共约 6,500 个交易日 × 5,000 只股票 = 32,500,000 行，缺失率约 0.45%。虽然绝对比例不高，但如果缺失集中在特定年份或板块，会导致因子覆盖率偏差。
- **建议**：生成一份 `(asset_id, trade_date)` 级别的跨表对齐审计报告，按年份和板块统计缺失分布，确认缺失是随机还是系统性的。

### 1.3 Source Status 与 PIT 审计

**现状**：已建立 `source_status_audit_r7.json`、`pit_feature_audit_market_daily_v1.json`、`label_audit_forward_returns_v1.json` 等审计产物。`valuation_daily` 字段已拆分为 `market_derived_pit_candidate` 和 `financial_statement_dependent_unverified_pit`。

**评估**：

- **PIT 分层设计优秀**。将估值字段按数据来源和 PIT 可靠性分层，是防止基本面数据泄漏的有效工程手段。
- **审计产物为 JSON 格式，缺乏机器可读的 schema 版本控制**。当前审计产物是静态 JSON 快照，没有版本号、diff 机制或变更追踪。当 warehouse 重建时，需要手动比对新旧审计结果。
- **建议**：为审计产物引入 schema version 和 content hash，建立审计结果的增量比对机制（类似数据库 migration），每次重建后自动生成审计 diff 报告。

### 1.4 外部数据接入架构

**现状**：`external_data_sources.csv` 使用 `availability_bucket`（available_now / candidate_etl / missing / blocked_by_source_gap）四级状态管理。GMSL 已完成 Cboe VIX/OVX/GVZ 局部入仓，FRED 全部超时。

**评估**：

- **四级状态分层清晰**，但 `candidate_etl` 和 `missing` 之间的边界模糊。例如 `limit_events` 是 candidate_etl（有计划但未入仓），而 `walk_forward_calendar_v1` 是 missing（应有但没有）。建议增加 `planned` 状态区分"已有 ETL 脚本但未运行"和"连 ETL 脚本都没有"。
- **FRED 超时问题需要工程解决方案**。FRED 是 GMSL 能源/利率/FX 数据的核心源，全部超时意味着 GMSL 层严重不完整。建议：(1) 使用 FRED 官方 Python 包 `fredapi` 替代直接 HTTP 抓取；(2) 设置本地 FRED 数据镜像或使用 Quandl/Nasdaq Data Link 作为备用源；(3) 对超时源实施离线批量下载策略而非实时抓取。

---

## 2. 工程可行性审计

### 2.1 Phase A0 工作量评估

Phase A0 是 S1 启动前的审计和日历固化阶段，需要产出：

| 产出物 | 工程复杂度 | 估计实现工作量 |
|---|---|---|
| `track_registry_v1` | 低：配置表，定义 track_id、label、cadence 等 | 1-2 天 |
| `walk_forward_calendar_v1` | **高**：需要精确计算每个 OOT step 的 train_start/end、purge、embargo、label_maturity | 5-8 天 |
| `holdout_access_log.tsv` | 低：TSV 文件 + 访问控制逻辑 | 1-2 天 |
| `universe_daily_construction_audit` | 中：需要审计构造脚本、字段来源、PIT 输入 | 3-5 天 |
| `execution_label_audit` | **高**：需要构建 T+1 open/proxy、分批执行、未成交 carryover 等复杂会计逻辑 | 5-10 天 |
| `orders_audit` | **高**：订单状态机、涨跌停/停牌成交失败、解锁反转统计 | 5-8 天 |
| `daily_turnover_capacity_report` | 中：日换手、ADV 参与率、成本拖累 | 3-5 天 |
| benchmark/ADV/valuation 审计 | 中 | 2-3 天 |

**总计估计**：Phase A0 的纯工程实现工作量约 **25-45 个工作日**，其中 walk-forward calendar、execution label audit 和 orders audit 是三个最高复杂度的工程模块。

### 2.2 模型训练管线可行性

**现状**：文档要求每 63 个交易日重训一次，5 年训练窗口，20 日标签 purge 60 个交易日。

**评估**：

- **计算量估算**：假设 S1-M 有 24 个 OOT step（最低门槛），每个 step 需要训练 7 种模型（单因子→LightGBM Ranker），每种模型需要做权重敏感性（等权/12月/18月）= 7 × 3 = 21 次训练。24 × 21 = 504 次模型训练。如果全量 OOT step 约 40-60 步，则为 840-1,260 次训练。
- **单次训练时间**：5 年训练窗口约 1,260 个交易日 × 5,000 只股票 = 6,300,000 样本。LightGBM 在此规模下单次训练约 30-120 秒（取决于超参数和硬件）。线性模型更快（<10 秒）。
- **总训练时间**：24 步 × 21 次 × 平均 60 秒 ≈ 8.4 小时。全量 60 步约 21 小时。这在单机上是可行的。
- **内存瓶颈**：5 年面板约 630 万行 × 50+ 特征 ≈ 2.5 GB（float32）。加上标签和元数据，峰值内存约 4-6 GB。Intel Arc B390 有 16.5 GB 显存，但 CPU 端内存需要至少 16 GB RAM。
- **建议**：预生成 walk-forward 每步的 train/val/test 索引文件（parquet 或 pickle），避免每次训练时重新计算 purge/embargo 边界。

### 2.3 依赖管理

**现状**：已安装 lightgbm、xgboost、sklearn、qlib、cvxpy、torch、statsmodels。未安装 arch、vectorbt、riskfolio-lib、PyPortfolioOpt、catboost。

**评估**：

- **statsmodels 是 Newey-West HAC 和 block bootstrap 的关键依赖**，必须确认已安装且版本兼容。
- **cvxpy 用于组合优化**，但文档中的组合构建主要是等权/ICIR 加权，cvxpy 在 S1 阶段可能用不上，S2/S3 的约束优化才需要。
- **建议**：在 Phase A0 阶段就验证 statsmodels 的 `Newey-West` 实现是否满足需求（带宽计算、小样本修正），避免在 S1 运行时发现统计检验实现不一致。

---

## 3. Walk-forward 实现审计

### 3.1 Calendar 生成复杂度

**现状**：文档要求生成 `walk_forward_calendar_v1.parquet`，字段包括 step_id、track_id、prediction_start/end、train_start/end、label_horizon、base_purge_days、purge_multiplier、computed_purge_days、embargo_days、label_maturity_date、decision_frequency、rebalance_interval、holding_period、execution_rule_id、panel_hash、model_refit_flag、frozen_model_version、holdout_flag。

**评估**：

- **这是整个系统中工程复杂度最高的单一组件**。原因：
  1. **多 track 并行**：S1-M（月频）和 S1-D/S1-R（日频）有不同的 decision_frequency、rebalance_interval 和 purge 规则，但共享同一个 walk-forward 框架。
  2. **Purge 计算的精确性**：`computed_purge_days = max(label_horizon * 3, 40)` 对于 20 日标签是 60 个交易日。但 purge 的起点是 `train_end`，终点是 `oot_start`，需要精确对齐到交易日历，不能用自然日近似。
  3. **Label maturity 约束**：OOT step k 的标签在 `label_end_date` 才成熟，而 `label_end_date = oot_start + label_horizon`。这意味着 OOT step k 的评估必须等到标签成熟后才能进行，形成异步评估管线。
  4. **Holdout 剥离**：最后 12 个月（约 252 个交易日）必须从 OOT step 中剥离，且不能参与任何模型选择。这要求 calendar 生成时就知道 holdout 的精确起始日期。

- **实现建议**：
  ```python
  # 伪代码：walk-forward calendar 生成逻辑
  def generate_wf_calendar(trade_dates, train_window_days, 
                           purge_days, embargo_days, 
                           refit_interval_days, holdout_days):
      steps = []
      train_end = trade_dates[train_window_days - 1]  # 首个 train_end
      step_id = 0
      
      while True:
          # 找到下一个 refit 点
          oot_start_idx = find_next_refit(trade_dates, train_end, 
                                          refit_interval_days)
          oot_start = trade_dates[oot_start_idx]
          
          # 验证 purge 约束
          assert train_end <= oot_start - purge_days - embargo_days
          
          # 检查是否进入 holdout
          if oot_start >= holdout_start:
              break
          
          # 计算 label maturity
          label_maturity_idx = oot_start_idx + label_horizon
          if label_maturity_idx >= len(trade_dates):
              break
          
          steps.append({
              'step_id': step_id,
              'train_start': trade_dates[oot_start_idx - train_window_days],
              'train_end': train_end,
              'prediction_start': oot_start,
              'label_maturity_date': trade_dates[label_maturity_idx],
              'computed_purge_days': purge_days,
              'holdout_flag': False,
          })
          
          train_end = oot_start  # 或 train_end += refit_interval_days
          step_id += 1
      
      return steps
  ```

- **关键风险**：如果 `refit_interval_days`（63 个交易日）和 `rebalance_interval`（月频约 21 个交易日）不整除，会导致 refit 和 rebalance 错位。文档中 S1-M 是"固定月末/月初调仓"但"每 63 个交易日重训"，这两个频率不同步，需要明确：当 refit 和 rebalance 不在同一天时，使用哪个模型版本？文档说"非重训 step 使用冻结模型"，这在工程上需要维护一个模型版本注册表。

### 3.2 Purge/Embargo 实现

**评估**：

- **Purge 计算必须精确到交易日**。`computed_purge_days = max(label_horizon * 3, 40)` 对于 20 日标签是 60 个交易日。这意味着训练窗口的最后 60 个交易日的样本必须被剔除，因为这些样本的标签可能与 OOT step 的标签重叠。
- **Embargo 是 purge 的补充**。embargo = 10 个交易日，在 purge 之后额外剔除 10 个交易日的样本，防止 purge 边界附近的特征泄漏。
- **实现复杂度**：purge 和 embargo 的计算必须在每个 walk-forward step 的训练窗口生成时动态执行，不能预先计算一次。因为每个 step 的 `train_end` 不同，purge 边界也不同。
- **建议**：在 walk-forward calendar 中预计算每个 step 的 `purge_start_idx` 和 `train_end_idx`，训练时直接使用索引切片，避免每次训练时重新计算。

### 3.3 S1-D/S1-R 日频 Calendar 特殊性

**评估**：

- S1-D/S1-R 使用 1/5 日标签，purge = max(1*3, 40) = 40 个交易日。这比 S1-M 的 60 个交易日 purge 更短，意味着 S1-D/S1-R 的训练窗口可以使用更多近期样本。
- 但 S1-D/S1-R 是"每日盘后输出"，意味着每个交易日都是一个 OOT step。从 2005 到 2026 约 5,000 个交易日，减去 5 年训练窗口和 12 个月 holdout，约有 4,000+ 个 OOT step。这远超 S1-M 的 24-60 步。
- **工程影响**：S1-D/S1-R 的 walk-forward calendar 行数是 S1-M 的 100+ 倍。如果每个 step 都存储完整的元数据，calendar 文件会很大。建议对 S1-D/S1-R 使用压缩存储（只记录 refit 点，中间 step 由 refit 点派生）。

---

## 4. 执行审计系统设计审计

### 4.1 Orders Audit 设计

**现状**：文档定义了 `execution_audit/orders_audit` 的最小字段：run_id、step_id、asset_id、trade_date、side、offline_sim_target_weight、intended_order_value、blocked_reason、filled_value、unfilled_value、delay_days、limit_lock_chain_length、unlock_date、post_unlock_return_1d/3d/5d。

**评估**：

- **字段设计合理但不完整**。缺少以下关键字段：
  1. `execution_price`：实际成交价格（T+1 open 或 close-based proxy）
  2. `execution_slippage`：相对于决策价格的滑点
  3. `order_status`：枚举值（filled/partial_fill/blocked/cancelled/expired）
  4. `cost_breakdown`：佣金、印花税、过户费、规费的分项
  5. `prev_weight`：调仓前持仓权重（用于计算换手）
  6. `turnover_contribution`：本订单对组合换手的贡献

- **订单状态机复杂度**：文档描述了涨停买不到、跌停卖不出、停牌延迟、连续锁死、解锁后反转等状态。这需要实现一个完整的有限状态机（FSM）：
  ```
  States: pending → filled | blocked | partial_fill | expired
  blocked → retry_next_day | cancel
  retry_next_day → filled | blocked | expired (after max_delay)
  ```
  每个状态转换都需要记录 timestamp、reason 和 next_action。

- **实现建议**：使用 Python 的 `enum` 和 `dataclass` 实现订单状态机，确保状态转换的可审计性和可回溯性。每个状态转换写入日志，支持事后审计。

### 4.2 Execution Label Audit

**现状**：文档要求比较 `close_to_close_adjusted`、`t_plus_1_open_or_proxy`、`vwap_or_split_execution_proxy` 三类标签/会计。

**评估**：

- **这是防止"纸面 alpha"的关键工程组件**。close-to-close 收益假设在收盘价成交，但 A 股 T+1 制度下实际执行在 T+1 开盘或盘中。两者的差异可能很大（尤其是高波动股票）。
- **T+1 open proxy 的数据可用性**：`prices_daily_unadjusted` 有 `open` 字段，可以构建 T+1 open-to-next-rebalance 的收益标签。但需要精确对齐：T 日信号 → T+1 开盘执行 → 持有到下一个调仓日。
- **分批执行的工程复杂度**：文档要求报告 T+1 单日执行、3 日分批、5 日分批。分批执行意味着一个调仓信号产生多个订单，每个订单在不同日期执行，需要：
  1. 拆分目标权重为每日等额订单
  2. 每个订单独立跟踪成交状态
  3. 合并多个订单的加权平均成交价
  4. 处理分批期间的涨跌停/停牌

- **建议**：先实现最简单的 T+1 单日执行，验证管线正确性后再扩展到分批执行。分批执行的增量复杂度很高，但对 S1-M 月选股（低换手）的影响相对有限。

### 4.3 Daily Turnover Capacity Report

**评估**：

- **三层换手控制**（重叠率 >=85%、单票日变动 <=2%、单边日换手 <=10%）需要维护前一日持仓快照和当日目标持仓的逐票比较。这在工程上需要一个持仓状态管理器。
- **ADV 参与率计算**：`tradability_daily_enriched.amount` 提供日成交额，但需要计算 trailing ADV（20/60/120 日窗口）。对于每个调仓日，需要回溯 N 个交易日计算 ADV，这对数据访问模式有要求（需要随机访问历史数据）。
- **建议**：预计算 trailing ADV 并写入 `features` 表的一个字段（如 `adv_20d`、`adv_60d`），避免在回测时重复计算。

---

## 5. 实验台账设计审计

### 5.1 Schema 评估

**现状**：实验台账 TSV 文件包含 70+ 字段，涵盖 run_id、track_id、label_id、calendar_id、panel_hash、execution_rule_id、hypothesis、commit、changed_files、各种 hash、验证参数、统计指标、审计状态等。

**评估**：

- **字段数量过多（70+），维护成本高**。每次实验需要填写 70+ 个字段，其中很多是自动派生的（如各种 hash）。建议分层：
  1. **核心层（必填，约 15 字段）**：run_id、track_id、label_id、hypothesis、commit、primary_metric、status、decision
  2. **验证层（自动填充，约 20 字段）**：purge_days、embargo_days、IC t-stat、bootstrap p、Sharpe、max_drawdown 等
  3. **审计层（自动填充，约 15 字段）**：leak_audit_status、pit_factor_audit_status、holdout_burned_flag 等
  4. **元数据层（自动填充，约 20 字段）**：各种 hash、panel_hash、validation_params_hash 等

- **TSV 格式的局限性**：
  1. 不支持嵌套结构（如 cost_breakdown、shock_state 摘要）
  2. 不支持版本控制和 diff（TSV 是纯文本，修改后无法追踪变更）
  3. 不支持查询和过滤（需要加载整个文件到 pandas）

- **建议**：考虑使用 SQLite 或 DuckDB 作为实验台账的存储后端。优势：
  1. 支持 SQL 查询（"找出所有 Sharpe > 1 且 holdout 未污染的实验"）
  2. 支持 schema evolution（添加新字段不需要重写整个文件）
  3. 支持并发写入（多个实验并行记录）
  4. DuckDB 可以直接查询 Parquet 文件，与 warehouse 数据格式一致

### 5.2 Keep/Discard 规则的工程实现

**现状**：文档定义了详细的 keep/discard 规则，包括 HAC t-stat >= 1.65、bootstrap p < 0.10、holdout 方向一致、成本后超额 > 0 等。

**评估**：

- **规则数量多且有逻辑依赖**。keep 规则包含 10+ 个条件，其中一些是 AND 关系（全部通过），一些是 OR 关系（任一通过即 inconclusive）。这需要一个决策引擎来自动评估。
- **建议**：实现一个 `KeepDecisionEngine` 类，将所有规则编码为可配置的条件树，自动从实验结果中提取指标并输出 keep/discard/inconclusive 决策。避免人工逐项检查，减少人为错误。

```python
class KeepDecisionEngine:
    def evaluate(self, experiment_result):
        # Hard Gate 检查
        if not self.check_hac_tstat(experiment_result, threshold=1.65):
            return 'inconclusive', 'HAC t-stat < 1.65'
        if not self.check_bootstrap_p(experiment_result, threshold=0.10):
            return 'inconclusive', 'bootstrap p >= 0.10'
        if not self.check_holdout(experiment_result):
            return 'discard', 'holdout failed'
        # ... 更多规则
        return 'keep', 'all gates passed'
```

### 5.3 Test Family Registry

**现状**：文档提到 `test_family_id`、`hypothesis_family`、`trial_index_in_family`、`total_trials_in_family`，用于 FDR 校正和 attempt_count 追踪。

**评估**：

- **这是防止 p-hacking 和数据窥探的关键工程组件**。每个因子/模型/参数组合的尝试都必须被记录和计数。
- **工程挑战**：如何定义"一个测试族"？如果一个研究者尝试了 10 个因子、3 种模型、5 种参数组合，这是 1 个族还是 150 个族？文档没有明确定义族的边界。
- **建议**：定义清晰的族规则，例如：(1) 同一个 `track_id` + `label_id` + `model_family` 构成一个族；(2) 族内的每个参数组合是一个 trial；(3) FDR 在族级别应用。将这些规则硬编码到 `test_family_registry` 的生成逻辑中。

---

## 6. 性能和可扩展性审计

### 6.1 数据 I/O 瓶颈

**现状**：核心表总行数约 1,700 万行，features/labels 各 1,542 万行。按年度 Parquet 分区存储。

**评估**：

- **单次全量读取**：1,542 万行 × 50 列 × 4 字节/float32 ≈ 3 GB。在 NVMe SSD 上读取时间约 5-10 秒。
- **Walk-forward 训练**：每个 step 读取 5 年数据（约 300 万行），I/O 时间约 1-2 秒。24 步 × 2 秒 = 48 秒 I/O 开销。可接受。
- **S1-D/S1-R 日频**：4,000+ 个 OOT step，每个 step 读取 5 年数据。如果每次重新读取，总 I/O 时间约 4,000 × 2 秒 = 2.2 小时。这是一个显著的性能瓶颈。
- **建议**：
  1. 对 S1-D/S1-R，预加载整个 features/labels 面板到内存（3 GB），然后用索引切片，避免重复 I/O。
  2. 使用 memory-mapped parquet（`pd.read_parquet` 的 `memory_map=True` 参数）减少内存拷贝。
  3. 对 walk-forward 的训练/测试索引使用预计算缓存。

### 6.2 模型训练并行化

**评估**：

- **单因子 IC 计算**可以高度并行化。50+ 个因子的 IC 计算相互独立，可以用 `multiprocessing.Pool` 或 `joblib.Parallel` 并行。
- **LightGBM/XGBoost 训练**本身已支持多线程（`n_jobs` 参数），但多个模型的训练可以进一步并行化。
- **内存约束**：Intel Arc B390 有 16.5 GB 显存，但 LightGBM/XGBoost 的 CPU 训练主要消耗系统内存。如果并行训练 4 个模型，每个需要 3 GB，总内存需求约 12 GB，加上操作系统和其他进程，需要至少 16 GB RAM。
- **建议**：实现一个任务调度器，根据可用内存动态控制并行训练数量，避免 OOM。

### 6.3 Block Bootstrap 计算量

**现状**：要求至少 5,000 次 block bootstrap 重抽样，block_days = max(label_horizon, rebalance_interval) = 21 个交易日。

**评估**：

- **计算量**：假设 IC 序列长度为 24（OOT step 数），block_size = 21，每次重抽样需要重新计算 IC 均值和标准误。5,000 次 × 24 个样本 ≈ 120,000 次计算。单次计算时间 < 1 毫秒，总时间 < 5 秒。可忽略。
- **但如果 IC 序列更长**（S1-D/S1-R 有 4,000+ 个日度 IC），block bootstrap 的计算量会显著增加：5,000 × 4,000 = 20,000,000 次计算，约 20 秒。仍然可接受。
- **Newey-West HAC 带宽计算**：`lag = max(1, floor(4*(n/100)^(2/9)))`，对于 n=24，lag=1；对于 n=4,000，lag=3。计算量可忽略。

---

## 7. 代码复用性和维护性审计

### 7.1 模块化设计评估

**现状**：文档描述了多个独立但相互依赖的模块：walk-forward calendar、execution label audit、orders audit、experiment ledger、keep decision engine 等。

**评估**：

- **模块间耦合度需要控制**。例如：
  - walk-forward calendar 依赖 exchange_calendar 和 feature/label panel hash
  - execution label audit 依赖 prices_daily_unadjusted、tradability_daily_enriched 和 trading_costs
  - orders audit 依赖 execution label audit 的输出
  - experiment ledger 依赖以上所有模块的输出

- **建议**：采用 DAG（有向无环图）设计，明确每个模块的输入/输出接口：
  ```
  exchange_calendar → walk_forward_calendar → model_training → experiment_ledger
  prices_daily → execution_label_audit → orders_audit → experiment_ledger
  universe_daily → universe_audit → experiment_ledger
  ```

### 7.2 配置管理

**现状**：`validation_params.json` 作为机器可读的验证参数镜像，文档说"若镜像与本文档冲突，以本文档为准"。

**评估**：

- **配置源不唯一是工程风险**。如果 `validation_params.json` 和文档有冲突，需要人工判断哪个是正确的。这在自动化管线中容易出错。
- **建议**：
  1. 将所有验证参数统一存储在 `validation_params.json` 中，文档只引用该文件
  2. 实现参数校验脚本，在每次实验启动前自动验证参数一致性
  3. 为 `validation_params.json` 引入 schema validation（使用 JSON Schema 或 pydantic）

### 7.3 版本控制和可复现性

**现状**：文档要求记录 `model_version`、`train_rows_hash`、`params_hash`、`feature_cutoff`、`label_cutoff`、代码提交、依赖 lock hash 等。

**评估**：

- **版本控制设计完善**，但工程实现需要自动化支持。
- **建议**：
  1. 实现一个 `ModelArtifact` 类，自动收集和记录所有版本元数据
  2. 使用 `git commit hash` + `validation_params hash` + `panel hash` 作为模型的全局唯一标识
  3. 将训练好的模型和元数据一起序列化（pickle/joblib），支持从 artifact 完全复现

---

## 8. 关键改进建议（按优先级排序）

### P0（阻塞 S1 启动）

1. **实现 walk-forward calendar 生成器**：这是所有后续工作的基础。建议先实现 S1-M 的月频 calendar，验证 purge/embargo 逻辑正确后再扩展到 S1-D/S1-R。

2. **实现 orders_audit 状态机**：使用 `enum` + `dataclass` 实现完整的订单状态机，支持涨停买不到、跌停卖不出、停牌延迟、连续锁死等状态转换。

3. **实现 execution_label_audit**：先实现 T+1 open proxy 的简单版本，验证管线正确性后再扩展到分批执行。

4. **统一配置源**：将所有验证参数统一到 `validation_params.json`，实现自动校验脚本。

### P1（提升效率和质量）

5. **预计算 trailing ADV**：将 ADV_20d、ADV_60d、ADV_120d 作为 features 表的字段，避免回测时重复计算。

6. **实现 KeepDecisionEngine**：将 keep/discard 规则编码为可配置的决策引擎，自动化评估实验结果。

7. **实验台账升级为 SQLite/DuckDB**：支持 SQL 查询、schema evolution 和并发写入。

8. **预计算 walk-forward 索引**：为每个 OOT step 预计算 train/val/test 的行索引，训练时直接使用索引切片。

### P2（长期可维护性）

9. **审计产物版本控制**：为审计结果引入 schema version 和 content hash，建立增量比对机制。

10. **DAG 任务调度**：将整个 S1 管线设计为 DAG，明确模块间依赖，支持断点续跑和并行执行。

11. **FRED 数据源替代方案**：调研 FRED 官方 Python 包或备用数据源，解决 GMSL 数据超时问题。

12. **内存优化**：对 S1-D/S1-R 的大规模日频 walk-forward，实现内存映射或流式处理，避免 OOM。

---

## 9. 总体评价和评分（1-10）

### 评分

| 维度 | 评分 (1-10) | 说明 |
|---|---|---|
| 数据架构完整性 | **8** | 分层清晰、PIT 审计完善、source registry 设计优秀。扣分项：跨表对齐审计不足、GMSL 数据严重缺失。 |
| 工程可行性 | **7** | 核心管线在单机上可行，但 Phase A0 工作量被低估。walk-forward calendar 和 orders audit 的复杂度最高。 |
| Walk-forward 设计 | **8.5** | purge/embargo 规则严谨、多 track 隔离设计合理。扣分项：refit/rebalance 频率不同步的处理未明确。 |
| 执行审计系统 | **7** | orders_audit 字段设计合理但不完整，execution_label_audit 的分批执行复杂度高。 |
| 实验台账设计 | **6** | 字段过多（70+）、TSV 格式局限性大、缺少自动化决策引擎。 |
| 性能和可扩展性 | **7.5** | 单机 S1-M 可行，S1-D/S1-R 的 I/O 和内存需要优化。 |
| 代码复用性 | **7** | 模块化设计方向正确，但配置管理和版本控制需要工程落地。 |
| **综合评分** | **7.5** | 文档的策略严谨性和审计意识在量化研究领域属于优秀水平。主要扣分在工程实现的细节和自动化程度上。 |

### 总体评价

这是一份在策略严谨性和审计意识上非常出色的量化研究规划。文档对数据泄漏、PIT 合规、overfitting 防御和可复现性的重视程度远超大多数量化研究项目。三层 universe 分离、purge/embargo 规则、holdout access log、execution label audit 等设计都是行业最佳实践。

主要的工程挑战在于：
1. **walk-forward calendar 的精确实现**：这是整个系统的基石，任何 purge/embargo 计算错误都会导致后续所有结论无效。
2. **orders_audit 状态机的完整性**：需要处理 A 股特有的涨跌停、停牌、T+1 等复杂场景。
3. **实验台账的可维护性**：70+ 字段的 TSV 文件在长期使用中会变得难以管理。

建议的工程优先级是：先用 2-3 周实现 walk-forward calendar 和 orders audit 的最小可用版本，用合成数据验证管线正确性，再逐步扩展到完整功能。不要试图一次性实现所有功能。
