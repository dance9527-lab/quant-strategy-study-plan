# Coder Agent 独立审计报告 R1-V2

> **审计人**: Coder Agent（量化开发/数据工程/架构设计专家）
> **审计日期**: 2026-05-01
> **审计对象**: `quant_strategy_plan.md`（总纲）、`quant_strategy_research_plan_detailed.md`（执行规范）、`DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md`
> **审计类型**: 对更新后文档的独立工程审计（第二轮）
> **上一轮核心共识**: Phase A0 工作量 25-45 工作日、Walk-forward Calendar 基石、SQLite WAL 实验台账、orders_audit 补字段、ModelRegistry、S1-D/S1-R I/O 优化、FRED 替代方案

---

## 总评

| 维度 | 评分 (1-10) | 说明 |
|---|---|---|
| 上一轮意见采纳完整度 | **8/10** | 7 项核心共识中 6 项已正确采纳，1 项部分采纳 |
| 工程可行性 | **7/10** | 大方向正确，但部分新增组件缺少具体实现路径 |
| Phase A0 工作量评估 | **7/10** | 已更新为 25-45 工作日并拆分 A0.1/A0.2，但低估了 SQLite WAL 和 ModelRegistry 的实现复杂度 |
| 文档一致性和可执行性 | **8/10** | 四份文档高度一致，cross-reference 完善 |
| 架构设计合理性 | **8/10** | 分层 sleeve、capital overlay、三层 universe 设计合理 |
| **综合评分** | **7.5/10** | 工程细节仍需补充，但整体架构方向正确 |

---

## 一、上一轮评审意见采纳逐项评估

### 1.1 Phase A0 工作量 25-45 工作日 [P0]

**评分: 8/10 — 已采纳，拆分合理**

采纳情况：
- ✅ 总纲 Section 7 已明确拆分为 A0.1（2-3 周，阻塞 S1 启动）和 A0.2（3-6 周，阻塞 S1 keep）
- ✅ A0.1 包含 `track_registry_v1`、`walk_forward_calendar_S1M_v1`、`WalkForwardCalendarValidator`、`validation_params.json` 参数 hash、`universe_daily_construction_audit`、valuation coverage audit
- ✅ A0.2 包含 `holdout_access_log.tsv`、`test_family_registry`、冻结模型 registry、SQLite WAL `experiment_ledger`、`execution_label_audit`、`execution_audit/orders_audit`、`daily_turnover_capacity_report`

工程评估：
- A0.1 的 2-3 周估计合理。WalkForwardCalendarValidator 是纯校验逻辑，从 exchange calendar + feature/label panel hash + validation_params.json 生成即可，复杂度可控
- A0.2 的 3-6 周可能偏紧。SQLite WAL 实验台账的 schema 定义、migration、并发控制、备份策略需要额外设计时间。orders_audit 的 `execution_price`、`execution_slippage`、`order_status` 字段虽已列出，但实现 T+1 open/proxy、3/5 日分批、未成交 carryover 和解锁反转的完整状态机需要约 2 周独立开发

**建议**: A0.2 拆为 A0.2a（holdout log + test family + experiment ledger schema，2-3 周）和 A0.2b（execution audit + orders audit + capacity report，3-4 周），总计 A0 为 7-10 周更现实

### 1.2 Walk-forward Calendar 是系统基石 [P0]

**评分: 9/10 — 完整采纳，设计到位**

采纳情况：
- ✅ 执行规范 Section 7.1 给出了 `walk_forward_calendar_v1.parquet` 的完整最小字段清单（21 个字段）
- ✅ 明确要求 `WalkForwardCalendarValidator` 逐 track 检查 `computed_purge_days`、embargo、holdout 隔离、label maturity、训练窗口重叠率、`model_refit_flag`、`frozen_model_version`
- ✅ S1-M 和 S1-D/S1-R 必须通过独立 `track_id` 关联，不得共用 OOT/holdout 结果择优
- ✅ 24 步只是 smoke/minimum，完整 OOT 步数按 calendar 计算

工程评估：
- 字段清单完整，覆盖了所有必要的元数据
- `WalkForwardCalendarValidator` 可以作为独立 Python 脚本/类实现，校验逻辑明确
- 建议增加 `calendar_version` 和 `generated_at` 字段，支持后续版本迭代

**唯一不足**: 未明确 calendar 的生成时机——是在 A0.1 结束时一次性生成，还是随 validation_params 变更时动态重新生成？建议文档明确"calendar 在 A0.1 结束时一次性生成并 hash，后续 validation_params 变更必须重新生成并更新 hash"

### 1.3 实验台账升级为 SQLite WAL [P0]

**评分: 7/10 — 已采纳，但实现细节不足**

采纳情况：
- ✅ 执行规范 Section 11 明确实验台账使用 SQLite WAL，推荐路径 `D:\quantum_a0\experiment_ledger.sqlite`
- ✅ DuckDB 只用于只读分析查询，TSV/CSV 只作为报告导出
- ✅ 给出了完整的 TSV 字段模板（60+ 字段），按四层组织（核心层、验证层、审计层、元数据层）

工程评估：
- **缺少 schema DDL**: 文档只给出了 TSV 列名，没有给出 SQLite 的 CREATE TABLE 语句、索引定义和约束。SQLite WAL 模式需要明确 WAL checkpoint 策略和并发读写规则
- **缺少 migration 策略**: 当 schema 需要扩展时（如新增字段），如何做 migration？建议使用 Alembic 或自定义 migration 脚本
- **缺少备份策略**: SQLite WAL 模式下，备份需要 `VACUUM INTO` 或文件级 copy + checkpoint
- **缺少并发控制**: 多个实验同时写入时的锁策略未说明。建议使用 `BEGIN IMMEDIATE` 事务模式
- **字段过多**: 60+ 字段的单表设计会导致大量 NULL 值。建议拆为 `runs`（核心）、`validation_results`（验证指标）、`audit_status`（审计状态）、`metadata`（元数据）四张表，通过 `run_id` 关联

**建议**:
1. 补充 SQLite schema DDL（CREATE TABLE + 索引）
2. 补充 migration 和 backup 策略
3. 考虑拆表设计，减少 NULL 值
4. 明确 WAL checkpoint 策略（建议 `PRAGMA wal_autocheckpoint=1000`）

### 1.4 orders_audit 补充 execution_price、execution_slippage、order_status [P0]

**评分: 9/10 — 完整采纳**

采纳情况：
- ✅ 执行规范 Section 10.2 的 `execution_audit/orders_audit` schema 已包含 `execution_price`、`execution_slippage`、`order_status`
- ✅ 补充了 `blocked_reason`、`filled_value`、`unfilled_value`、`delay_days`、`limit_lock_chain_length`、`unlock_date`、`post_unlock_return_1d/3d/5d`
- ✅ 明确 S1.5 可补 `cost_breakdown`、`prev_weight`、`turnover_contribution`
- ✅ 明确生产订单接口禁用 `target_weight`，未来只能使用 `risk_overlay_action/risk_overlay_reason` 等风控字段

工程评估：
- 字段设计完整，覆盖了从订单生成到成交确认的全链路
- `order_status` 建议定义枚举值：`pending`、`filled`、`partial_filled`、`blocked_limit_up`、`blocked_limit_down`、`blocked_suspended`、`cancelled_expired`
- `execution_slippage` 的计算基准需要明确：是相对 `open`、`vwap` 还是 `close`？建议文档定义 `slippage基准 = execution_price / decision_price - 1`

**唯一建议**: 补充 `order_status` 的枚举值定义和 `execution_slippage` 的计算基准

### 1.5 ModelRegistry 管理 refit/rebalance 不同步 [P0]

**评分: 7/10 — 已采纳，但实现路径不清晰**

采纳情况：
- ✅ 执行规范 Section 6.1.5 提到"所有模型版本写入 ModelRegistry/frozen model registry"
- ✅ 冻结模型必须登记 `model_version`、`track_id`、`model_family`、`train_start/end`、label horizon、feature/label panel hash、`validation_params_hash`、代码提交、artifact hash、随机种子、依赖 lock hash 和替换/回滚原因
- ✅ 命名建议 `{track_id}_{model_family}_{train_end}_{validation_params_hash8}_{code_commit8}`

工程评估：
- **缺少持久化方案**: ModelRegistry 是文件系统目录、SQLite 表、还是独立服务？文档未明确
- **缺少 artifact 存储**: 模型文件（pkl/lgb/torch）存放在哪里？建议使用 `D:\quantum_a0\model_artifacts\{model_version}\` 目录结构
- **缺少版本查询接口**: 如何查询"最近一次符合 computed purge 规则的冻结模型版本"？建议实现 `ModelRegistry.get_latest_frozen(track_id, train_end, purge_days)` 方法
- **refit/rebalance 不同步的处理逻辑**: 当 refit 和 rebalance 的时间点不同时，如何选择正确的 frozen model？文档提到了"非重训 step 使用最近一次符合 computed purge 规则的冻结模型版本"，但缺少具体的匹配算法

**建议**:
1. 明确 ModelRegistry 的持久化方案（建议 SQLite 表 + 文件系统 artifact）
2. 补充 artifact 存储目录结构
3. 实现 `get_latest_frozen()` 查询接口
4. 补充 refit/rebalance 不同步时的模型选择算法

### 1.6 S1-D/S1-R I/O 优化方案 [P0]

**评分: 8/10 — 已采纳，设计合理**

采纳情况：
- ✅ 总纲和执行规范均明确 S1-D/S1-R 是日频风险/执行主线，不是 alpha keep 主线
- ✅ 每日盘后输出 `candidate_score`、`risk_signal`、`alert_state`、`gmsl_shock_state` 和执行审计
- ✅ `S1-D_daily_risk_execution_offline` 定义了完整的输出字段：`as_of_date`、`trade_date`、`asset_id`、`score`、`rank`、`horizon`、`risk_signal`、`alert_state`、`gmsl_shock_state`、`model_version`、`feature_cutoff`、`label_cutoff`、`no_trade_reason`
- ✅ 离线权重字段命名为 `offline_sim_target_weight`，不得接入生产订单接口

工程评估：
- I/O 设计清晰，输入输出边界明确
- 日频处理的性能考虑：15M+ 行的 feature panel 每日全量重算分数可能需要优化。建议：
  - 增量计算：只重算当日新增数据的分数
  - 缓存机制：非重训 step 使用 frozen model 的缓存预测
  - 并行化：按 asset_id 或日期分片并行预测
- `daily_orders_audit` 和 `daily_turnover_capacity_report` 的生成频率和存储方式未明确

**建议**:
1. 补充日频处理的性能优化方案（增量计算、缓存、并行化）
2. 明确 `daily_orders_audit` 和 `daily_turnover_capacity_report` 的存储格式和保留策略

### 1.7 FRED 替代方案（fredapi/Quandl）[P0]

**评分: 7/10 — 已提及，但方案不完整**

采纳情况：
- ✅ 执行规范 Section 13 Step 5 提到"GMSL-v2 为 FRED 超时源准备 fredapi、Nasdaq Data Link/Quandl、vendor mirror 或下载替代"
- ✅ WAREHOUSE_README.md 也提到 FRED 配置源全部 `ReadTimeout`
- ✅ 明确 GMSL-v1 只用 Cboe VIX/OVX/GVZ、国债收益率和 Shibor

工程评估：
- **fredapi 方案可行但需验证**: fredapi 是 Python 官方客户端，需要 API key（免费注册）。当前 FRED 超时可能是 `fredgraph.csv` 端点的问题，fredapi 可能走不同的 API 端点
- **Quandl 已更名为 Nasdaq Data Link**: 文档同时提到 Quandl 和 Nasdaq Data Link，建议统一为 Nasdaq Data Link
- **缺少具体实施计划**: 哪些 FRED series 需要替代？优先级如何？建议列出 GMSL-v2 需要的 FRED series ID 列表
- **缺少离线方案**: 建议同时准备离线 CSV 下载方案（FRED 网页手动下载），作为 API 失败的 fallback

**建议**:
1. 列出 GMSL-v2 需要的 FRED series ID 列表（Brent/WTI、DXY、UST 2Y/10Y 等）
2. 统一使用 Nasdaq Data Link（原 Quandl）
3. 准备离线 CSV 下载 fallback
4. 在 A0 阶段做一次 fredapi smoke test

---

## 二、新增内容工程可行性评估

### 2.1 分层 Sleeve 实现

**评分: 8/10 — 设计合理，实现可行**

总纲 Section 4.1 和执行规范 Section 3.1.1 定义了分层 sleeve：
- 分数分段：`score_p95_p100_top_extreme`、`score_p80_p95_upper_middle`、`score_p60_p80_middle_high`、`score_p40_p60_middle_diagnostic`、`score_below_p40`
- 市值分段：`mv_p0_p20_micro`、`mv_p20_p40_small`、`mv_p40_p60_mid`、`mv_p60_p80_large_mid`、`mv_p80_p100_large`
- 5 个预注册组合 sleeve

工程评估：
- ✅ 所有 sleeve 必须使用同一训练窗、同一成本、同一交易规则和同一 walk-forward calendar
- ✅ 阈值必须在训练前写入实验登记，不能根据 OOT/holdout 结果挑选最优分段
- ✅ 每个 sleeve 记录 `sleeve_id`、分数分位阈值、市值分位阈值、持仓数或权重上限、`test_family_id` 和 `attempt_count`
- 实现上，sleeve 只是组合构建阶段的 filter/weighting 逻辑，不涉及模型训练变更，复杂度可控

**建议**: 补充 sleeve 的 `attempt_count` 计数规则——每个 sleeve 是否独立计入 `attempt_count`？还是共享同一 `test_family_id`？

### 2.2 Capital Overlay

**评分: 7/10 — 设计清晰，但实现边界需明确**

总纲 Section 9.3 和执行规范 Section 9.1.5 定义了资金仓位控制模块：
- 选股模型先生成目标股票篮子，资金模块再按市场状态给组合目标市值乘以 `capital_multiplier`
- 现金部分不追买、不加杠杆、不参与收益承诺
- 保守映射：牛市 80%-100% / 震荡 40%-70% / 熊市 0%-30% / 极端风险 0%

工程评估：
- ✅ 明确资金模块不参与选股模型训练、特征筛选或标签构造
- ✅ 明确市场状态定义必须预注册
- ✅ 明确 `capital_multiplier` 的映射表
- **实现复杂度**: capital overlay 本质上是组合后处理层，实现简单。但需要考虑：
  - 现金部分的无风险收益率计算
  - 市场状态判定的滞后性（T 日状态何时可用？）
  - 仓位调整的执行约束（减仓可以 T+0 吗？A 股 T+1 限制如何处理？）
- **文档未明确**: 当市场状态从牛市切换到熊市时，减仓是立即执行还是受 T+1 约束？建议文档明确"减仓受 T+1 约束，T 日判定状态变化，T+1 执行减仓"

**建议**:
1. 补充市场状态判定的时点约束
2. 补充减仓的 T+1 执行约束
3. 补充现金部分的收益率处理

### 2.3 SQLite WAL 实验台账

**评分: 7/10 — 方向正确，细节不足**（详见 1.3 节）

### 2.4 ModelRegistry

**评分: 7/10 — 方向正确，实现路径不清晰**（详见 1.5 节）

### 2.5 WalkForwardCalendarValidator

**评分: 9/10 — 设计完整，实现可行**（详见 1.2 节）

---

## 三、Phase A0 工作量评估

### 当前评估

文档给出的 A0 工作量为 25-45 工作日（约 5-9 周），拆分为：
- A0.1：2-3 周（阻塞 S1 启动）
- A0.2：3-6 周（阻塞 S1 keep）

### 工程师独立评估

| 子任务 | 乐观估计 | 最可能估计 | 悲观估计 | 说明 |
|---|---|---|---|---|
| A0.1: track_registry + calendar + validator | 1 周 | 1.5 周 | 2 周 | 纯数据处理和校验逻辑 |
| A0.1: universe_daily_construction_audit | 0.5 周 | 1 周 | 1.5 周 | 需要复核构造脚本和 PIT 输入 |
| A0.1: valuation coverage audit + 指数衰减权重登记 | 0.5 周 | 1 周 | 1.5 周 | 估值缺口三口径实验 |
| A0.2: holdout_access_log + test_family_registry | 0.5 周 | 1 周 | 1.5 周 | TSV/SQLite schema 设计 |
| A0.2: SQLite WAL experiment_ledger | 1 周 | 2 周 | 3 周 | schema DDL + migration + backup + 并发 |
| A0.2: ModelRegistry | 1 周 | 1.5 周 | 2 周 | 持久化 + 查询接口 + artifact 存储 |
| A0.2: execution_label_audit + orders_audit | 1.5 周 | 2.5 周 | 3.5 周 | T+1 open/proxy + 分批 + carryover + 解锁反转 |
| A0.2: daily_turnover_capacity_report | 0.5 周 | 1 周 | 1.5 周 | 日换手 + ADV + 成交失败 |
| **总计** | **6.5 周** | **11.5 周** | **16.5 周** | — |

### 评估结论

- 文档的 25-45 工作日（5-9 周）估计偏乐观
- 最可能估计为 **11-12 周**（约 55-60 工作日）
- 主要低估了 SQLite WAL 实验台账（需要 schema 设计 + migration + backup + 并发控制）和 execution audit（需要完整的订单状态机实现）
- **建议更新为 35-60 工作日**，或拆分为 A0.1（2-3 周）+ A0.2a（3-4 周）+ A0.2b（3-4 周）

---

## 四、仍需改进的工程问题

### 4.1 缺少 SQLite Schema DDL [P1]

**问题**: 执行规范 Section 11 给出了 TSV 字段模板，但没有给出 SQLite 的 CREATE TABLE 语句、索引定义和约束。

**建议**:
```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL,
    label_id TEXT NOT NULL,
    calendar_id TEXT NOT NULL,
    hypothesis TEXT,
    commit TEXT,
    status TEXT DEFAULT 'pending',
    decision TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    -- ... 核心层字段
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);

CREATE INDEX idx_runs_track_status ON runs(track_id, status);
CREATE INDEX idx_runs_family ON runs(test_family_id, trial_index_in_family);
```

### 4.2 缺少 ModelRegistry 持久化方案 [P1]

**问题**: 文档提到 ModelRegistry 但未明确持久化方案。

**建议**:
```
D:\quantum_a0\model_registry\
├── registry.sqlite          # 模型元数据
├── artifacts/
│   ├── S1-M_lgb_20260101_a1b2c3d4_e5f6g7h8/
│   │   ├── model.lgb
│   │   ├── params.json
│   │   ├── feature_importance.csv
│   │   └── metadata.json
│   └── ...
└── backups/
```

### 4.3 缺少 execution_slippage 计算基准 [P2]

**问题**: orders_audit 包含 `execution_slippage`，但未定义计算基准。

**建议**: 定义 `slippage基准 = execution_price / decision_price - 1`，其中 `decision_price` 默认为 T 日 `open`（开盘执行）或 T 日 `close`（收盘执行）

### 4.4 缺少日频处理性能优化方案 [P2]

**问题**: S1-D/S1-R 每日盘后需要对 15M+ 行 feature panel 全量计算分数，性能可能成为瓶颈。

**建议**:
1. 增量计算：非重训 step 只计算新增数据
2. 缓存机制：frozen model 的预测结果缓存
3. 并行化：按日期分片并行预测
4. 预估：15M 行 × 50 特征 × LightGBM 预测约需 5-10 分钟（单线程），并行后可降至 1-2 分钟

### 4.5 sleeve 的 attempt_count 计数规则不明确 [P2]

**问题**: 分层 sleeve 的 `attempt_count` 是否独立计入？5 个 sleeve × 多个模型 = 多少个 attempt？

**建议**: 明确每个 sleeve 独立计入 `attempt_count`，但共享同一 `test_family_id`。即 `total_trials_in_family` 包含所有 sleeve 和模型组合

### 4.6 capital overlay 的市场状态判定时点 [P2]

**问题**: 市场状态判定的时点未明确。T 日盘后判定状态，T+1 执行？还是 T 日开盘前判定？

**建议**: 明确"T 日盘后使用 T 日数据判定市场状态，T+1 执行仓位调整；减仓受 T+1 约束，不得 T+0 卖出"

### 4.7 GMSL FRED 替代方案缺少具体 series 列表 [P2]

**问题**: 文档提到 fredapi/Nasdaq Data Link 作为替代，但未列出需要的具体 FRED series ID。

**建议**: 列出 GMSL-v2 需要的 FRED series：
- Brent: `DCOILBRENTEU`
- WTI: `DCOILWTICO`
- DXY: `DTWEXBGS`
- UST 2Y: `DGS2`
- UST 10Y: `DGS10`

### 4.8 四份文档的 cross-reference 可以更精确 [P3]

**问题**: 总纲和执行规范之间有大量重复内容（如验证参数、模型顺序、S1 定义），维护时容易分叉。

**建议**: 总纲只保留方向和优先级，具体参数和规则全部引用执行规范的 section 编号

---

## 五、文档一致性检查

### 5.1 总纲 vs 执行规范

| 检查项 | 一致性 | 说明 |
|---|---|---|
| Phase A0 工作量 | ✅ 一致 | 均为 25-45 工作日 |
| S1-M/S1-D/S1-R 定义 | ✅ 一致 | 双主线治理定义完全一致 |
| 验证参数 | ✅ 一致 | purge/embargo/OOT/HAC/bootstrap 均一致 |
| 模型顺序 | ✅ 一致 | 单因子→等权→ICIR→Gram-Schmidt→Ridge→LightGBM→Ranker |
| 禁止事项 | ✅ 一致 | 19 条禁止事项完全一致 |
| sleeve 定义 | ✅ 一致 | 分数分段和市值分段定义一致 |

### 5.2 DATA_USAGE_GUIDE.md vs WAREHOUSE_README.md

| 检查项 | 一致性 | 说明 |
|---|---|---|
| 表行数 | ✅ 一致 | 所有表行数一致 |
| 数据范围 | ✅ 一致 | 均为 1990-12-19 至 2026-04-27 |
| GMSL 状态 | ✅ 一致 | 均描述为 candidate_etl，FRED 超时 |
| 使用限制 | ✅ 一致 | 禁止用法列表一致 |

---

## 六、总结与建议

### 6.1 整体评价

文档在上一轮评审后有显著改进：
1. Phase A0 拆分清晰，任务边界明确
2. Walk-forward Calendar 设计完整，字段清单全面
3. orders_audit 字段补充到位
4. 分层 sleeve 和 capital overlay 设计合理
5. 四份文档高度一致，cross-reference 完善

### 6.2 需要优先补充的内容

| 优先级 | 内容 | 建议 |
|---|---|---|
| P0 | SQLite Schema DDL | 补充 CREATE TABLE、索引、约束和 WAL 配置 |
| P0 | ModelRegistry 持久化方案 | 明确 SQLite + 文件系统 artifact 的存储结构 |
| P1 | Phase A0 工作量更新 | 建议更新为 35-60 工作日 |
| P1 | execution_slippage 计算基准 | 定义 slippage = execution_price / decision_price - 1 |
| P1 | sleeve attempt_count 规则 | 明确每个 sleeve 独立计数 |
| P2 | 日频性能优化方案 | 增量计算 + 缓存 + 并行化 |
| P2 | capital overlay 时点约束 | 明确 T+1 执行约束 |
| P2 | FRED 替代方案具体 series 列表 | 列出 GMSL-v2 需要的 FRED series ID |

### 6.3 对下一轮评审的建议

1. 请 Strategy Agent 重点评审 sleeve 的 `attempt_count` 和 FDR 计数规则
2. 请 Data Agent 重点评审 GMSL FRED 替代方案的可行性
3. 下一轮应产出 SQLite Schema DDL 和 ModelRegistry 的具体实现代码

---

*本报告由 Coder Agent 独立完成，未参考其他 agent 的评审意见。*
