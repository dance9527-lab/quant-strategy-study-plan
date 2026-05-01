# 量化策略研究计划评审意见报告

> 评审日期：2026-05-01
> 评审方法：四位专家独立审计 + 多轮共识讨论
> 评审人：Main Agent（金融工程/量化策略/ML/DL/架构设计）、Review Agent（量化策略/代码review）、DeepSeek Agent（量化策略/深度学习）、Coder Agent（量化开发/数据工程/架构设计）
> 审计对象：quant_strategy_plan.md（总纲）、quant_strategy_research_plan_detailed.md（执行规范）
> 数据依据：DATA_USAGE_GUIDE.md、WAREHOUSE_README.md、external_data_sources.csv

---

## 一、总体评价

| 评审人 | 评分 | 核心评价 |
|---|---|---|
| Main Agent | 8.0/10 | 治理框架和验证体系达专业水平，主要改进空间在参数量化和执行节奏 |
| Review Agent | 7.5/10 | 数据治理优秀，24步OOT统计功效偏低，P0治理工件全部missing |
| DeepSeek Agent | 8.0/10 | 高标准高纪律性，概念shift检测功效不足，GMSL数据严重缺失 |
| Coder Agent | 7.5/10 | 策略严谨性优秀，工程落地需重点突破calendar和orders audit |
| **共识评分** | **7.8/10** | **整体优秀，具备落地基础，需在统计功效、工程实现和GMSL数据三方面加强** |

---

## 二、四方共识（所有评审人一致同意）

### 共识 1：GMSL 数据基础严重不完整

**现状**：GMSL 仅完成 Cboe VIX/OVX/GVZ 候选源入仓（17,526行），FRED 全部超时，geopolitical_event_calendar 0 行。oil_shock、fx_shock、rate_shock、commodity_shock 均无法计算。

**共识结论**：GMSL 当前只能作为概念框架。建议分两阶段：
- **GMSL-v1**：基于现有 VIX/OVX/GVZ + 国债收益率 + Shibor，输出简单 stress report
- **GMSL-v2**：完整外生冲击层，需 FRED 替代源（fredapi/Quandl/Nasdaq Data Link）+ 地缘事件日历

### 共识 2：Phase A0 工作量被严重低估

**现状**：Phase A0 列出 17 个产出项，包括 walk-forward calendar、holdout log、execution label audit、orders audit 等，但未给出时间估算。

**共识结论**：
- Phase A0 纯工程实现工作量约 **25-45 个工作日**
- Walk-forward calendar（5-8天）、execution label audit（5-10天）、orders audit（5-8天）是三个最高复杂度模块
- **建议分为 A0.1（阻塞S1启动）和 A0.2（阻塞S1 keep）**：
  - A0.1（2-3周）：walk-forward calendar、track registry、validation params hash、universe construction audit
  - A0.2（3-6周）：execution label audit、orders audit、daily turnover capacity report、benchmark/ADV/valuation audit

### 共识 3：Walk-forward Calendar 是系统基石

**共识结论**：Walk-forward calendar 的 purge/embargo 计算必须精确到交易日，任何错误都会导致后续所有结论无效。建议：
- 先实现 S1-M 的月频 calendar，验证 purge/embargo 逻辑正确后再扩展到 S1-D/S1-R
- S1-M 和 S1-D 使用独立 calendar 文件，通过 track_id 关联
- 预计算每个 step 的 train/val/test 行索引，训练时直接使用索引切片

### 共识 4：Concept Shift 状态机误报率过高

**现状**：yellow 告警阈值为"最近6步中至少4步IC<0"，在零假设下误报率约 34%。

**共识结论**：
- 提高 yellow 门槛为 **"最近6步中至少5步IC<0"**（误报率约 10.9%）
- 或增加 IC 幅度要求：不仅要求 IC<0，还要求 |IC| > 0.5 标准误
- 在 validation_params.json 中记录状态机的预期误报率

### 共识 5：24 步 OOT 只是 Smoke Test

**共识结论**：
- 24 步只是最低验收门槛，不是完整验证
- S1-M 完整 OOT 步数约 **180 步**（2005-2026，月末调仓，扣除 holdout）
- S1-D/S1-R 约 **4,000+ 步**（日频输出）
- 建议将 24 步定义为"Phase A0 快速 smoke test"，180 步定义为"Phase A 完整验证"

### 共识 6：实验台账需升级

**共识结论**：70+ 字段 TSV 格式不可维护，建议升级为 SQLite 或 DuckDB，支持 SQL 查询、schema evolution 和并发写入。字段分四层：核心层（15字段必填）、验证层（20字段自动填充）、审计层（15字段自动填充）、元数据层（20字段自动填充）。

---

## 三、关键分歧裁决

### 裁决 1：1 日标签 Purge 规则

| 立场 | 来源 |
|---|---|
| 40天（原文） | 总纲/执行规范 |
| 10天 | DeepSeek Agent |
| 20天（折中） | Main Agent |

**裁决结果：20天折中方案**

**依据**：
- DeepSeek 的理论正确：1日 forward return 的 label overlap 仅1天，40天 purge 确实过度保守
- 但 A 股 microstructure（散户主导、T+1制度、日内动量/反转效应）可能导致短期信息泄漏超出标签窗口
- 10天过于激进，无法覆盖 A 股 microstructure 效应

**执行方案**：
- 默认 purge：`max(label_horizon*5, 20)` = 20天
- 报告 10/20/40 天 purge 的样本损失、IC、HAC t-stat、bootstrap p、holdout 结果
- 若 10/20/40 天结论一致，purge 选择不影响 keep 决策

### 裁决 2：Block Bootstrap 的 block_days

| 立场 | 来源 |
|---|---|
| max(label_horizon, rebalance_interval) = 21天 | 总纲/执行规范 |
| 基于 IC 的 empirical ACF | DeepSeek Agent |

**裁决结果：IC 序列用 empirical ACF，组合收益保持原规则**

**依据**：
- DeepSeek 的理论正确：IC 是横截面统计量，其自相关结构不同于收益序列
- 但 24 步小样本下 empirical ACF 估计不可靠

**执行方案**：
- IC 序列 block_days：`max(label_horizon, empirical_acf_cutoff)`，其中 empirical_acf_cutoff 基于 IC 序列的 ACF 估计；24步小样本下 fallback 到 `max(label_horizon, 21)`
- 组合收益 block_days：保持 `max(label_horizon, rebalance_interval)`
- 报告 10/21/40 日 block_days 敏感性，晋级或生产 tighten-only 使用最保守结论

### 裁决 3：Refit/Rebalance 频率不同步

**裁决结果：不需要同步频率，用模型版本管理**

**执行方案**：
- 在 walk-forward calendar 中增加 `model_refit_flag`（布尔值）和 `frozen_model_version`（字符串）
- 每个 rebalance step 使用最近一次符合 purge 规则的冻结模型版本
- 冻结模型命名：`{track_id}_{model_family}_{train_end}_{validation_params_hash8}_{commit8}`

### 裁决 4：因子方向预注册

**裁决结果：分类要求**

**执行方案**：
- **高置信因子**（有大量 A 股文献支持）：必须预注册方向和经济学机制
  - 市值（小盘溢价，regime-dependent）
  - 价值（EP/BP，A股长期有效但不稳定）
  - 流动性（低换手异象，A股特色）
  - 短期反转（1-5日，A股显著）
- **探索性因子**：只记录方向，不强制预注册
  - 动量（A股长期弱于美股）
  - 波动率、beta、规模等
- 在实验台账中记录 `factor_direction_pre_registered` 和 `direction_confidence_level`

### 裁决 5：Newey-West 带宽选择

**裁决结果：增加敏感性分析**

**执行方案**：
- 在 validation_params.json 中增加 `nw_bandwidth_sensitivity` 字段
- 报告四种带宽下的 t-stat：`default_formula`、`andrews_1991`、`lag_6`、`lag_12`
- keep 决策使用最保守结论

### 裁决 6：其他改进项

| 项目 | 来源 | 裁决 |
|---|---|---|
| valuation缺口对holdout影响 | Main | holdout 验收同时报告 drop-gap 和 ffill 两种口径 |
| valuation missing key影响 | Main/Coder | S1启动前输出 valuation_coverage_audit，按年度和板块报告缺失分布 |
| 停牌推断精度 | Main/Review | S1启动前用2023以来AkShare官方数据对比推断结果，报告 precision/recall |
| 冲击成本模型 | DeepSeek | S1阶段至少报告 square-root impact model 结果，与固定比例滑点对照 |
| 事件触发重训 | DeepSeek | 当 GMSL shock state 触发 red 或成熟 IC 连续 3 步为负时，提前重训 |
| orders_audit 字段补充 | Coder | 增加 execution_price、execution_slippage、order_status、cost_breakdown、prev_weight、turnover_contribution |
| FRED 替代方案 | Coder | 调研 fredapi、Quandl/Nasdaq Data Link 作为备用源 |
| 审计产物版本控制 | Coder | 为审计结果引入 schema version 和 content hash |

---

## 四、策略计划改进建议

### 4.1 总纲（quant_strategy_plan.md）改进

1. **§1.1 数据底座**：增加 2026 估值缺口对 holdout 的影响说明，明确 holdout 验收允许 forward-fill 的条件和限制
2. **§1.2 数据缺口**：补充停牌推断精度验证要求（S1启动前完成）
3. **§1.4 执行规则**：增加"1日标签 purge 默认20天，报告10/20/40敏感性"
4. **§4.1 第一阶段模型**：增加"事件触发重训"机制（GMSL red 或 IC 连续3步为负）
5. **§5.5 验证参数**：
   - 明确 S1-M 预期 OOT 步数约 180 步（非 24 步）
   - 增加 Newey-West 带宽敏感性参数
   - 增加 block bootstrap block_days 对 IC 序列和收益序列的不同规则
6. **§5.5 Concept Shift**：将 yellow 门槛从"6步中4步"提高到"6步中5步"

### 4.2 执行规范（quant_strategy_research_plan_detailed.md）改进

1. **§2.3 数据质量门槛**：增加 valuation 缺口对 holdout 的验收规则
2. **§4.1 默认标签**：修改 1 日标签 purge 为 `max(label_horizon*5, 20)` = 20天
3. **§5.1 P1 核心因子**：
   - 为高置信因子（市值、价值、流动性、短期反转）预注册方向
   - 增加因子计数口径说明（按独立信息来源计数，非按变体）
   - 增加行业默认分类标准（建议申万一级）
4. **§7.1 默认验证**：
   - 增加 IC 序列 block bootstrap 的 empirical ACF block_days 规则
   - 增加 Newey-West 带宽敏感性报告
   - 明确 refit/rebalance 不同步时的模型版本管理规则
5. **§7.2 最小报告指标**：增加 per-factor decay sensitivity、execution-aligned PnL 指标
6. **§9.1 S1 启动前置条件**：
   - 将 Phase A0 分为 A0.1（阻塞启动）和 A0.2（阻塞 keep）
   - 为每个产出项估算工作量
7. **§11 实验台账**：将 TSV 格式升级为 SQLite/DuckDB，定义四层字段结构
8. **orders_audit 字段**：补充 execution_price、execution_slippage、order_status、cost_breakdown、prev_weight、turnover_contribution

### 4.3 数据依据文档改进

1. **DATA_USAGE_GUIDE.md**：
   - 增加 valuation 缺口对 holdout 影响的说明
   - 补充停牌推断精度验证方法
   - 增加冲击成本 square-root model 说明
2. **external_data_sources.csv**：
   - 为 FRED 超时源标记替代方案（fredapi/Quandl）
   - 增加 `planned` 状态区分"已有ETL脚本"和"连ETL脚本都没有"

---

## 五、工程实施路线建议

### Phase A0.1：S1 启动最小集（2-3 周）

| 产出物 | 复杂度 | 工作量 | 依赖 |
|---|---|---|---|
| track_registry_v1 | 低 | 1-2天 | 无 |
| walk_forward_calendar_S1M_v1 | **高** | 5-8天 | exchange_calendar, validation_params.json |
| validation_params.json 更新 | 低 | 1天 | 无 |
| universe_daily_construction_audit | 中 | 3-5天 | universe_daily 构造脚本 |
| valuation_coverage_audit | 中 | 1-2天 | valuation_daily, prices_daily_returns |
| suspension_inference_validation | 中 | 1天 | tradability_daily, AkShare official |

### Phase A0.2：S1 keep 完整集（3-6 周）

| 产出物 | 复杂度 | 工作量 | 依赖 |
|---|---|---|---|
| execution_label_audit | **高** | 5-10天 | prices_daily_unadjusted, tradability_daily, trading_costs |
| orders_audit | **高** | 5-8天 | execution_label_audit |
| daily_turnover_capacity_report | 中 | 3-5天 | orders_audit, tradability_daily |
| benchmark_coverage_audit | 中 | 1-2天 | benchmarks |
| ADV 新股不足标记 | 低 | 1天 | tradability_daily_enriched |
| experiment_ledger (SQLite) | 中 | 2-3天 | 无 |
| factor_direction_registry | 低 | 1天 | 无 |

### Phase A：S1 完整验证（6-12 周）

| 阶段 | 内容 | 预计耗时 |
|---|---|---|
| A-M Step 1 | 单因子 IC/RankIC/ICIR | 2-3 周 |
| A-M Step 2 | 等权/ICIR/正交化复合因子 | 1-2 周 |
| A-M Step 3 | 线性/GBDT/Ranker 对照 | 2-3 周 |
| A-M Step 4 | 组合回测 + 成本/容量 | 2-3 周 |
| A-R | 日频风险/执行主线（并行） | 3-4 周 |

---

## 六、风险提示

1. **最大风险**：P0 治理工件全部 missing，S1 无法正式启动。Phase A0 的完成质量直接决定后续所有结论的有效性。
2. **统计风险**：24 步 OOT 的有效独立样本量因 95% 训练窗口重叠率远小于 24。完整 180 步验证才能产生可靠结论。
3. **数据风险**：GMSL 数据严重不完整，concept shift 检测和外生冲击分析只能基于有限数据。
4. **工程风险**：walk-forward calendar 和 orders audit 的实现复杂度被严重低估，任何 purge/embargo 计算错误都会导致后续结论无效。
5. **过拟合风险**：多标签×多模型×多半衰期×多训练窗口的组合搜索会产生巨大多重比较问题，attempt_count 和 test_family_id 机制必须严格执行。

---

## 七、评审结论

本策略计划在**治理框架和验证体系上达到了专业量化基金的水平**，在 PIT 审计、holdout access log、experiment ledger、三层 universe 分离等方面甚至更为严格。核心优势在于：
- 数据治理严格（canonical 数据源、manifest/hash 追踪、leakage check）
- 验证纪律强（purge/embargo + HAC/bootstrap 双重门槛 + FDR + DSR/PBO）
- 自我纠正意识强（qant 随机 8/2 的 label leakage 诊断和修正）
- 渐进式设计（market-only → 外部数据，日频保守 → 分钟精细，report-only → tighten-only）

主要改进空间集中在：
1. **量化关键参数的选择依据**（半衰期12月、24步OOT、63日重训、block_days=21）
2. **降低概念 shift 状态机的误报率**（从34%降至约11%）
3. **明确 Phase A0 的执行节奏和工作量**（分为A0.1和A0.2）
4. **补齐 GMSL 数据基础**（FRED替代方案）
5. **升级实验台账**（TSV → SQLite/DuckDB）

**总体判断**：计划整体方向正确，具备落地基础。严格执行并落实上述改进后，有较大概率产出**稳健、可复现、可审计**的策略结论。

---

*本报告由四位专家独立审计后经多轮讨论达成共识，所有观点均有事实/数据/理论支持。*
