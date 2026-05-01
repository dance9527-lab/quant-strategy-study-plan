# Main Agent 独立审计报告

> 审计人：Main Agent（金融工程/量化策略/ML/DL/架构设计专家）
> 审计时间：2026-05-01 10:35 CST
> 审计对象：quant_strategy_plan.md（总纲）+ quant_strategy_research_plan_detailed.md（执行规范）
> 数据依据：DATA_USAGE_GUIDE.md + WAREHOUSE_README.md + external_data_sources.csv

---

## 1. 数据基础审计

### 1.1 2026年估值缺口对Holdout的影响（P0问题）

**事实**：`valuation_daily` 在 2026-01-05 至 2026-02-05 缺失约24个交易日。总纲和执行规范均提到此缺口，允许慢变量特征做有界 forward-fill（最长25个交易日）。

**问题**：Holdout 定义为"最后12个月约252个交易日"。若当前数据截至 2026-04-27，则 holdout 窗口约为 2025-04-28 至 2026-04-27。估值缺口恰好落在 holdout 窗口内。执行规范要求"比较有/无 valuation forward-fill 的 IC、RankIC 和组合结果"，但未明确：
1. holdout 验收是否允许 forward-filled 数据？
2. 若 holdout 结果依赖 forward-fill，是否 still valid？

**改进建议**：
- 明确 holdout 验收允许的最大 forward-fill 比例
- 建议 holdout 验收同时报告 drop-gap 和 ffill 两种口径
- 若 ffill 对 holdout 结论有显著影响，holdout 状态应标记为 `holdout_ffill_sensitive`

### 1.2 `valuation_daily` 与 `prices_daily_returns` Key不完全一致

**事实**：`audit_reports/valuation_return_key_diff_summary.csv` 显示估值表 extra 5,562 个 key，missing 146,208 个 key。

**问题**：146,208 个 missing key 意味着相当数量的交易日/股票组合在估值表中没有对应记录。这会影响市值加权、换手率等依赖估值表的因子。文档未量化这些 missing key 对各因子覆盖率的具体影响。

**改进建议**：
- 在 S1 启动前输出 `valuation_coverage_audit`，按年度报告 missing key 比例和受影响股票的市值/行业分布
- 若 missing key 集中在小市值或特定行业，应调整因子覆盖率声明

### 1.3 Benchmark 早期覆盖不足

**事实**：`CN_A_ALL_EQW_PROXY` 1990年仅覆盖1-5只股票，2005年中位约1315只。主窗口从 2005-01-01 开始。

**问题**：2005年覆盖1315只意味着等权代理中每只股票权重约 0.076%，而2024年覆盖5342只时每只权重约 0.019%。早期样本的横截面分散度显著低于近期，可能导致：
1. 早期IC估计方差更大
2. 早期等权组合的集中度风险更高

**改进建议**：
- S1报告必须按年度报告 benchmark coverage_assets
- 对2005-2010年的IC/RankIC结果单独标注置信度
- 考虑在因子IC计算中加入 effective cross-sectional size 作为权重调整

### 1.4 停牌推断精度

**事实**：`is_suspended_inferred=True` 577,900 行，是基于缺失bar推断，不是官方停牌公告。AkShare 停复牌提醒仅覆盖 2023年以来的1,447条记录。

**问题**：推断停牌的精度直接影响可交易universe的质量。如果推断错误地将正常交易日标记为停牌，会错误排除有效样本；反之会将停牌日纳入交易。

**改进建议**：
- S1启动前必须输出 `suspension_inference_validation`：用2023年以来AkShare官方数据对比推断结果，报告 precision/recall
- 对推断停牌中 event_length_bucket=1日 的事件特别关注（单日缺失更可能是数据错误而非停牌）

---

## 2. 标签和验证框架审计

### 2.1 Walk-Forward 总步数未量化

**事实**：执行规范要求"至少24个OOT step"，主窗口从2005-01-01开始，首个OOT约2010年。S1-M 使用20日标签、固定月末调仓。

**问题**：24步只是最低验收门槛，但文档未给出预期总步数。粗略估算：
- 主窗口2005-2026约21年
- 5年训练窗口，首个OOT约2010年
- 月末调仓频率，每年约12步
- OOT窗口约16年 × 12 = 192步
- 扣除最后12个月holdout，约180步

实际总步数约180步，远超24步最低门槛。文档应明确这一数量级，避免误解24步即为完整验证。

**改进建议**：
- 在执行规范中明确给出S1-M和S1-D/S1-R的预期OOT步数估算
- 建议将24步定义为"Phase A0快速smoke test"，180步定义为"Phase A完整验证"

### 2.2 Purge 敏感性的实际作用

**事实**：20日标签 official purge=60个交易日。40/60/80 purge 敏感性"阻塞正式keep/晋级结论"。

**问题**：执行规范说"40对20日标签属于under-purge诊断，不能支持keep"，但又说purge敏感性"阻塞正式keep/晋级结论"。这两句话的逻辑关系不清晰——如果40日purge结果不好，是否阻塞keep？还是只有60日purge结果不好才阻塞？

**改进建议**：
- 明确purge敏感性的决策逻辑：只有默认60日purge通过才可keep；40/80日结果只作robustness报告
- 建议增加purge敏感性的具体报告模板：列出每个purge值下的训练样本数、IC、HAC t-stat、bootstrap p、holdout结果

### 2.3 标签成熟度定义缺失

**事实**：执行规范多次提到"label maturity"，walk-forward calendar 模板包含 `label_maturity_date` 字段。

**问题**：`label_maturity_date` 的具体计算规则未在执行规范中明确定义。例如，20日forward return的label_maturity_date是 decision_date + 20 个交易日？还是 decision_date + 20 + 某个buffer？

**改进建议**：
- 在执行规范中明确定义：`label_maturity_date = decision_date + label_horizon + maturity_buffer`
- 建议 `maturity_buffer` 默认为0（即label_horizon结束日即为成熟日），但需在validation_params.json中显式声明

### 2.4 S1-D/S1-R 与 S1-M 的交互规则需强化

**事实**：S1-D/S1-R 是日频风险/执行主线，不得用于选择S1-M的模型、阈值、半衰期或窗口。

**问题**：虽然文档多次强调两者隔离，但未明确以下场景：
1. 若S1-D发现某因子在日频IC持续为负，是否可以建议S1-M重新评估该因子？
2. S1-D的 execution_label_audit 结果是否可以用于调整S1-M的执行规则？

**改进建议**：
- 明确S1-D/S1-R对S1-M的影响路径：只能通过 revalidation report 触发人工复核，不能直接修改S1-M参数
- 建议建立 `cross_track_influence_log`，记录任何跨track的信息流动

---

## 3. 因子库审计

### 3.1 Momentum 因子与 Total-Return 的矛盾

**事实**：文档明确"公司行为、除权除息、分红送配尚未形成独立主表；`return_adjusted_pit` 当前只能声明为 adjusted-return proxy，不能宣称完整 total-return accounting 已闭环"。同时，动量因子使用 `return_adjusted_pit` 计算5/20/60/120日收益。

**问题**：如果 `return_adjusted_pit` 只是 adjusted-return proxy，那么基于它的动量因子在除权除息频繁的股票上可能有系统性偏差。特别是高分红股票的长期动量（120日）可能被低估。

**改进建议**：
- 在因子PIT审计中明确标注：动量因子使用 adjusted-return proxy，受公司行为source gap影响
- 建议在公司行为主表入仓前，对高分红（股息率>5%）股票的动量因子单独做敏感性分析

### 3.2 因子数量与FDR触发

**事实**：P1核心因子约10类（市值、估值、流动性、动量、反转、波动率、风险、交易约束、行业），每类可能有多个变体。执行规范要求"候选因子>20个时必须做FDR校正"。

**问题**：如果P1因子变体超过20个（例如5/20/60/120日动量 × 4种计算方式 = 16个仅动量因子），FDR校正会大幅降低统计功效。文档未明确"候选因子"的计数口径——是按类别还是按变体？

**改进建议**：
- 明确因子计数口径：建议按"独立信息来源"计数，而非按变体
- 建议预注册因子相关性矩阵，对高相关（r>0.7）因子组只保留ICIR最高的一个
- 在实验台账中记录 `factor_count_methodology` 和 `effective_hypothesis_count`

### 3.3 行业中性化的分类标准选择

**事实**：`pit_industry_intervals_akshare` 覆盖12个分类标准，使用时必须指定标准。

**问题**：文档未明确默认使用哪个分类标准。不同分类标准（证监会、申万一级、申万二级、巨潮等）的行业粒度差异很大，直接影响行业中性化效果。

**改进建议**：
- 预注册默认分类标准（建议申万一级，110个行业中等粒度）
- 在validation_params.json中记录 `default_classification_standard_code`
- 对分类标准做敏感性分析（证监会 vs 申万一级 vs 申万二级）

---

## 4. 模型体系审计

### 4.1 指数衰减半衰期的理论依据

**事实**：默认半衰期12个月，18个月为敏感性，6/24/36月为诊断。

**问题**：12个月半衰期的选择缺乏理论或实证依据。A股市场因子衰减速度因因子类型而异：
- 短期反转：半衰期可能仅1-3个月
- 动量：半衰期可能3-6个月
- 价值/市值：半衰期可能12-24个月

统一12个月半衰期可能对不同因子产生截然不同的效果。

**改进建议**：
- 建议对不同因子类别分别估算empirical IC half-life，作为半衰期选择的参考
- 在S1.5中增加"per-factor decay sensitivity"，对核心因子分别测试6/12/18/24月半衰期

### 4.2 模型重训频率的合理性

**事实**：默认每63个交易日重训一次。

**问题**：63个交易日约3个月。对于20日标签、月末调仓的S1-M，这意味着：
- 每次重训后约3个月使用同一冻结模型
- 期间约3次月度调仓使用同一模型

如果市场结构在3个月内发生变化（如2024年量化拥挤），冻结模型可能失效。

**改进建议**：
- 建议将重训频率也纳入敏感性分析：21/42/63/126个交易日
- 特别关注在市场状态切换时（如牛市转熊市）重训频率对结果的影响

### 4.3 LightGBM Ranker 的 group 定义

**事实**：S1-D/S1-R 使用 LightGBM Ranker，group 必须是日期截面。

**问题**：文档提到"Ranker 的 group 必须是日期截面，不能做 random row split"，但未明确：
1. 每个日期截面的样本量差异如何处理？（2005年可能只有几百只，2024年有5000+只）
2. 是否需要对日期截面内样本做采样或加权？

**改进建议**：
- 明确Ranker训练中日期截面的样本量处理规则
- 建议对截面样本量超过某阈值（如3000）的日期做随机采样，避免大截面主导梯度

---

## 5. 回测和执行审计

### 5.1 成本模型的保守性

**事实**：`trading_costs.equity_cost_history` 23行，佣金、滑点、冲击成本仍含研究假设。

**问题**：文档要求"分档滑点和冲击成本"，但当前成本表只有23行记录，可能无法覆盖不同市值、流动性、市场状态下的成本差异。

**改进建议**：
- 建议在S1阶段至少使用P50和P80两档成本分别报告结果
- 在S2中进一步细化为市值/流动性分档成本

### 5.2 容量测试的1000万门槛

**事实**：S1最小容量1000万、5000万、1亿。

**问题**：1000万资金门槛对于个人投资者可能偏高，对于机构投资者可能偏低。文档未说明这个门槛的来源。

**改进建议**：
- 明确1000万门槛的来源（个人投资者典型规模？）
- 建议增加500万档，覆盖更广泛的个人投资者场景

### 5.3 L1到L2/L3执行模型的过渡路径

**事实**：L1日频保守模型立即可用，L2/L3需要分钟/集合竞价数据。

**问题**：文档未明确L1到L2/L3的过渡条件和验证标准。如果L1结果已经通过keep，但L2/L3数据尚未入仓，是否仍然keep？

**改进建议**：
- 明确：L1通过keep的结论在L2/L3可用后必须重验
- 建议在keep报告中标注 `execution_model_level=L1`，并在L2/L3可用后触发 `execution_model_upgrade_audit`

---

## 6. 风险控制审计

### 6.1 GMSL 的实际可操作性

**事实**：GMSL当前只完成Cboe VIX/OVX/GVZ候选源入仓，FRED全部超时，geopolitical_event_calendar 0行。

**问题**：GMSL 设计为"报告→审计→tighten-only"三阶段，但当前数据基础极弱：
- 只有3个volatility指数，没有能源、FX、利率、商品数据
- 地缘事件日历为空
- 即使FRED源恢复，时区/session cutoff审计也需要大量工作

这意味着GMSL在可预见的未来只能是"概念框架"，无法产生有实际价值的stress报告。

**改进建议**：
- 建议将GMSL分为两个子阶段：
  - GMSL-v1：基于现有VIX/OVX/GVZ + 国债收益率 + Shibor，输出简单stress报告
  - GMSL-v2：完整外生冲击层，需FRED替代源+地缘事件日历
- 明确GMSL-v1的交付时间和预期产出

### 6.2 Concept Shift 状态机的误报率

**事实**：连续6步IC<0触发red quarantine，最近6步中至少4步为负触发yellow。

**问题**：在24步OOT中，假设IC均值为0（无alpha），每步IC符号随机，那么：
- P(连续6步IC<0) = 0.5^6 = 1.56%
- P(最近6步中至少4步为负) = C(6,4)×0.5^6 + C(6,5)×0.5^6 + C(6,6)×0.5^6 = 34.4%

34.4%的误报率意味着即使没有concept shift，约1/3的因子会被标记为yellow。这会导致大量不必要的revalidation。

**改进建议**：
- 建议调整yellow阈值为"最近6步中至少5步为负"（误报率约10.9%）
- 或增加IC幅度要求：不仅要求IC<0，还要求|IC| > 某阈值
- 在validation_params.json中记录状态机的预期误报率

### 6.3 风险开关v1的均匀权重占位

**事实**：S3前使用25/25/25/25均匀权重占位，S3验证后替换为数据驱动仓位比例。

**问题**：文档未明确25/25/25/25对应的四个状态是什么。从上下文推测可能是"牛市/熊市/震荡/高波动"，但未显式定义。

**改进建议**：
- 明确定义四个市场状态及其触发条件
- 建议在S1阶段就输出市场状态分类结果，即使不用于仓位决策，也为S3做准备

---

## 7. 执行可行性审计

### 7.1 Phase A0 工作量估算

**事实**：Phase A0 列出17个产出项，包括manifest、track registry、universe审计、walk-forward日历、holdout log、PIT审计、benchmark审计等。

**问题**：文档未给出Phase A0的时间估算。从经验判断，仅`universe_daily_construction_audit`和`walk_forward_calendar_v1`的实现+测试可能就需要1-2周。全部17项完成可能需要4-6周。

**改进建议**：
- 为Phase A0的每个产出项估算工作量
- 建议将Phase A0分为A0.1（阻塞S1启动的最小集）和A0.2（阻塞S1 keep的完整集）

### 7.2 实验台账的可维护性

**事实**：实验台账TSV模板有约60个字段。

**问题**：60个字段的TSV文件极易出错（字段对齐、缺失值、转义字符）。随着实验数量增长，手工维护几乎不可能。

**改进建议**：
- 建议将实验台账改为SQLite数据库或JSONL格式
- 建议开发自动化脚本从walk-forward输出自动生成台账记录
- 将台账schema注册到 `schemas/schema_registry.csv`

### 7.3 Walk-Forward Calendar 的实现复杂度

**事实**：`walk_forward_calendar_v1` 最小字段22个，需要同时支持S1-M和S1-D/S1-R。

**问题**：S1-M是月度调仓、20日标签、60日purge；S1-D是日度输出、1/5日标签、40日purge。两个track的calendar结构不同，但文档建议可以合并为统一 `walk_forward_calendar_v1`。

**改进建议**：
- 建议S1-M和S1-D使用独立的calendar文件，通过 `track_id` 关联
- 统一calendar的schema但允许不同track有不同 `rebalance_interval` 和 `purge_days`
- 在calendar中增加 `step_status` 字段（pending/completed/failed），支持增量执行

---

## 8. 关键改进建议（按优先级排序）

| 优先级 | 建议 | 理由 |
|---|---|---|
| P0 | 明确holdout对forward-fill的容忍度 | 估值缺口落在holdout窗口内，直接影响验收标准 |
| P0 | 量化concept shift状态机误报率 | 34.4%的yellow误报率会导致大量无效revalidation |
| P0 | 明确S1-M预期OOT步数 | 24步vs180步的数量级差异影响验证充分性判断 |
| P1 | 量化valuation missing key对因子覆盖率的影响 | 146,208个missing key可能影响特定市值/行业分组 |
| P1 | 明确因子计数口径和FDR触发规则 | 避免因计数方式不同导致FDR校正结果差异 |
| P1 | 增加per-factor decay sensitivity | 统一半衰期对不同因子效果差异大 |
| P1 | 明确默认行业分类标准 | 12个分类标准的选择直接影响行业中性化效果 |
| P2 | 将实验台账改为SQLite/JSONL | 60字段TSV不可维护 |
| P2 | 增加500万容量档 | 覆盖个人投资者场景 |
| P2 | GMSL分阶段交付 | 当前数据基础无法支撑完整GMSL |

---

## 9. 总体评价

**评分：8.0/10**

**优势**：
- 数据治理框架极其严格，PIT审计、source registry、manifest/hash 体系完整
- 验证框架严谨，walk-forward + purge + embargo + holdout + FDR + DSR/PBO 多层防护
- 概念清晰，S1-M/S1-D/S1-R 双主线治理、CSRP/GMSL 分层、三层 universe 分离
- 风险控制意识强，禁止事项列表详尽且有明确教训来源

**不足**：
- 部分关键参数缺乏理论/实证依据（半衰期12月、24步OOT、63日重训）
- 概念shift状态机误报率偏高
- Phase A0 工作量未量化，执行节奏不清晰
- GMSL数据基础薄弱，短期内无法产生实际价值

**总体判断**：这份策略计划在治理框架和验证体系上达到了专业量化基金的水平，甚至在某些方面（如PIT审计、holdout access log、experiment ledger）更为严格。主要改进空间在于：(1)量化关键参数的选择依据，(2)降低概念shift状态机的误报率，(3)明确Phase A0的执行节奏和工作量。计划的整体方向正确，具备落地基础。
