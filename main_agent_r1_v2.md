# Main Agent 独立审计（v2 — 更新后文档）

> 角色：Main Agent（金融工程/量化策略/ML/DL/架构设计专家）
> 日期：2026-05-01
> 审计对象：更新后的 quant_strategy_plan.md 和 quant_strategy_research_plan_detailed.md

---

## 一、上一轮共识采纳审查

| # | 共识 | 采纳状态 | 评估 |
|---|---|---|---|
| 1 | GMSL 数据不完整 | ✅ 已采纳 | §1.2、§9.1.6 明确 GMSL-v1/v2 分阶段，FRED 替代方案（fredapi/Nasdaq Data Link） |
| 2 | Phase A0 25-45工作日 | ✅ 已采纳 | §7 Phase A0 明确拆分 A0.1（2-3周）和 A0.2（3-6周） |
| 3 | Walk-forward Calendar 系统基石 | ✅ 已采纳 | §7.1 完整字段列表 + WalkForwardCalendarValidator |
| 4 | Concept shift 5/6 门槛 | ✅ 已采纳 | §4.1"最近6步中至少5步为负触发yellow" |
| 5 | 24步OOT只是smoke test | ✅ 已采纳 | §5.5"24步只是最低验收门槛...完整S1-M OOT步数约180步" |
| 6 | SQLite WAL实验台账 | ✅ 已采纳 | §11 明确 SQLite WAL + DuckDB 只读分析 |
| 7 | 1日标签purge=20天 | ✅ 已采纳 | §4.3"S1-D/S1-R的1日标签...默认20个交易日purge" |
| 8 | Block bootstrap敏感性 | ✅ 已采纳 | §5.5"敏感性10/21/42日" |
| 9 | 因子方向Tier 1/2/3 | ✅ 已采纳 | §5.1 详细分层规则和首批因子分类 |
| 10 | 多重检验完整实验族 | ✅ 已采纳 | §7.1 因子×标签×模型×半衰期×训练窗口×正交化分支×执行规则 |
| 11 | 标签misalignment P0 | ✅ 已采纳 | §4.4 增加 `rebalance_to_rebalance_execution_aligned` 标签 |

**采纳率：11/11，全部正确采纳。**

---

## 二、新增内容审计

### 2.1 分层持仓 Sleeve [§3.1.1]

**评估**：设计合理。分数分段（P95-P100/P80-P95/P60-P80/P40-P60/Below-P40）和市值分段（P0-P20微盘到P80-P100大盘）形成了5×5=25种交叉，但文档明确预注册了5种首批组合sleeve，避免了自由度过高。

**问题**：
- P1：sleeve间重叠度未要求报告。如果 `baseline_top_score` 和 `upper_middle_score_p80_p95` 的持仓重叠80%+，则后者的增量信息有限。应要求报告 sleeve 间持仓重叠率。
- P2：score分位是在entry_eligible_universe内计算还是research_observable_universe内计算？微盘诊断如果用entry_eligible_universe的分位，P0-P20的定义可能因ST/涨跌停过滤而偏移。

### 2.2 资本配置 Overlay [§9.3]

**评估**：保守映射（牛80-100%/震40-70%/熊0-30%/极端0%）和挑战映射（100/60/30/0）的预注册设计合理。25/25/25/25均匀权重占位避免了在S3之前用主观判断。

**问题**：
- P1：市场状态定义的阈值如何预注册？文档说"市场状态定义必须预注册"，但未给出具体的预注册指标和阈值候选。建议在validation_params.json中增加market_state_indicators和threshold_candidates字段。
- P2：capital_multiplier是否四舍五入到最近的5%或10%？如果牛市目标87%、震荡市53%，则频繁小幅度变化会产生额外换手。

### 2.3 CSRP 误报率监控 [§9.1.5]

**评估**：`false_positive_rate = 1 - hit_rate` + Wilson置信区间 + 随机shuffle baseline 的方法论正确。

**问题**：
- P1：命中窗口长度未指定。如果信号触发后5个交易日、10个交易日、20个交易日都可以算"命中"，应预注册主口径和敏感性。
- P2：排列检验的shuffle次数未指定（建议至少1000次）。

### 2.4 Exploratory Tracking [§9.1]

**评估**：65%方向一致性 + 6个月冷却期 + 不入组合 + 完整记录的设计合理。

**问题**：
- P1：方向一致性的计算基准不明确。"OOT 24步中IC与对应训练窗口IC同号的步数/24"——如果训练窗口IC的符号在不同step间变化（如前12步正、后12步负），则exploratory tracking可能产生矛盾信号。
- P2：冷却期是否跨walk-forward重置？文档说"从首次进入Exploratory Tracking的日期起算，后续walk-forward step不重置"，这是正确的。

### 2.5 动态IC换手公式 [§4.1, §9.1.5]

**评估**：`raw_report_only_formula = 0.10 * min(max(0.5, trailing_matured_ic / 0.03), 1.5)` + 有效上限 `min(0.10, raw)` 的设计保守合理。

**问题**：
- P1：`trailing_matured_ic / 0.03` 中的0.03是预注册的IC"正常水平"基准。如果实际IC中位数远高于或远低于0.03，公式的行为会显著不同。建议在validation_params.json中记录这个基准值的来源。
- P1：如果 trailing IC 为负（策略恶化），公式输出为负值 × 0.10 = 负换手上限？文档未明确。应添加 `max(0, ...)` 约束。

### 2.6 Rebalance-to-Rebalance 执行标签 [§4.4]

**评估**：新增 `rebalance_to_rebalance_execution_aligned` 标签是解决 misalignment P0 的正确方案。

**问题**：
- P1：如果固定20日标签与调仓间隔标签的IC delta显著，是否意味着必须放弃20日标签？文档说"只能使用调仓间隔收益或标记为inconclusive"，但未定义"显著"的统计标准。建议增加IC delta的HAC t-test或bootstrap检验。

### 2.7 分层裁剪算法 [§7.1]

**评估**：优先级规则3>2>1 + 每层等比例缩减 + 归一化的设计正确。

**问题**：
- P2：裁剪后的权重归一化可能导致目标总敞口偏离100%。如果三层裁剪后实际可投资权重只有80%，剩余20%是现金还是缩小组合？

---

## 三、总纲与执行规范一致性检查

| 检查项 | 状态 | 说明 |
|---|---|---|
| purge 规则 | ✅ 一致 | 20日标签=60天，1日标签=20天（+10/20/40敏感性） |
| OOT 步数 | ✅ 一致 | 24步为smoke test，约180步为完整验证 |
| Concept shift 阈值 | ✅ 一致 | 5/6步为负触发yellow |
| 因子方向 | ✅ 一致 | Tier 1/2/3分类在两份文档中一致 |
| Phase A0 拆分 | ✅ 一致 | A0.1(2-3周) + A0.2(3-6周) |
| 实验台账 | ✅ 一致 | SQLite WAL |
| 半衰期 | ✅ 一致 | 12月默认，18月敏感性，6/24诊断 |
| GMSL | ✅ 一致 | S1报告，S1.5审计，S3后tighten-only |
| block_days | ⚠️ 微差异 | 总纲§1.4说"block=max(label_horizon, rebalance_interval)"，执行规范§7.1说"默认block=21日"——20日标签×月度调仓=21天，但总纲未明确说21天 |
| 探索性因子方向 | ⚠️ 微差异 | 总纲§5.1提到"限测2个方向"，执行规范§5.1提到"最多测试两个方向"——一致，但未明确是否允许先测一侧再测另一侧（顺序效应） |

**总体一致性：优秀，2处微差异不影响执行。**

---

## 四、评分与总结

| 维度 | 评分 | 说明 |
|---|---|---|
| 上一轮共识采纳 | 9.5/10 | 11/11全部正确采纳，新增内容与共识一致 |
| 新增内容质量 | 8.0/10 | sleeve/overlay/CSRP/ET设计合理，但有若干细节需补充 |
| 统计严谨性 | 8.0/10 | 多重检验、block bootstrap、HAC等已完善，exploratory tracking有小问题 |
| 工程可行性 | 8.0/10 | Phase A0拆分明确，SQLite WAL可行，动态IC换手有边界case |
| 文档一致性 | 9.0/10 | 总纲与执行规范高度一致，2处微差异 |
| 文档完备性 | 8.0/10 | 覆盖面广，sleeve/overlay/CSRP新增部分仍有细节待补充 |
| **综合评分** | **8.5/10** | **从上一轮7.6/10提升至8.5/10，改进显著** |

### 需改进项

**P1**：
1. Sleeve间持仓重叠率报告要求
2. 市场状态阈值预注册的具体候选
3. CSRP命中窗口长度预注册
4. Exploratory Tracking方向一致性计算基准
5. 动态IC换手公式对负IC的处理
6. Rebalance-to-rebalance IC delta"显著"的统计标准
7. capital_multiplier精度（是否四舍五入到5%/10%）

**P2**：
1. Score分位计算的universe选择
2. 裁剪后权重归一化与现金处理
3. 排列检验shuffle次数

---

*Main Agent 独立审计完成。评分8.5/10，上一轮11项共识全部正确采纳，新增内容质量高，有7项P1改进和3项P2改进。*
