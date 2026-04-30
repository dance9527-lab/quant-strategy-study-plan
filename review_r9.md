# R9 审计报告：三个专项审查

**审计时间**：2026-04-30
**审计员**：Review Subagent（独立审查）
**审查范围**：仅限以下3点，不得扩展

---

## 审查点 1：S1-M Walk-Forward 设计

### 评分：7 / 10

### 具体发现

**24 步 OOT 是否足够？**

数据来源：alidation_params.json + quant_strategy_research_plan_detailed.md 第7节

- 主窗口起点：2005-01-01
- 训练窗口：5 年（约 1260 交易日）
- 首个 OOT 起点：约 2010 年（5年训练 + purge约束后实际推算）
- 每步测试窗口：约 21 交易日（S1-M 月选股）
- **总 OOT 步数 = floor((last_non_holdout_date - first_oot_date) / 21)**
- holdout：最后 12 个月（约 252 交易日）不参与 OOT 步数计数

推算：
- 数据终点 2026-04-27，holdout 起点约 2025-04-28
- OOT 可用窗口约 2010-2025.4 ≈ 15 年
- 15年 × 252交易日 / 21 ≈ **约 180 步**（理论最大值）
- 文档明确："24步只是最低验收门槛，不是总步数"
- **结论：24步作为最低门槛合理；但实际可运行步数远大于24步，应披露实际步数**

**5 年训练窗口是否合理？**

数据来源：同上

- 5 年窗口覆盖约 1260 交易日
- A股典型周期：约 3-5 年一个牛熊周期（2007、2015、2024等大周期）
- 5 年窗口理论上可覆盖 1-2 个完整周期，但部分极端情况（如 2015 牛市+熊市）可能跨越 2 个周期
- **结论：5 年是平衡统计显著性和市场适应的折中，基准合理；但未说明为何选 5 年而非 4 年或 6 年**

### 改进建议

1. **披露实际 OOT 步数**：应在 walk-forward calendar 中明确计算并披露实际可运行步数，而非仅声明"不少于 24 步"
2. **敏感性分析**：应增加 4 年 / 6 年训练窗口的 OOT 对比，验证 5 年的稳健性（虽然不作为 keep 决策依据）
3. **首个 OOT 起点**：应在文档中明确计算首个 OOT 的实际日期（考虑 purge 和 label maturity）

---

## 审查点 2：S1-D 换手率控制

### 评分：5 / 10

### 具体发现

**文档中是否明确日换手率上限？**

数据来源：quant_strategy_research_plan_detailed.md、consensus_audit_r8.md、alidation_params.json

- alidation_params.json 中 S1-D 配置：ebalance_interval_trading_days: 1，daily_turnover_capacity_report_required: true
- consensus_audit_r8.md 第4节明确指出："**日换手率控制方案缺失（需要明确上限）**"
- 成本分析（R8 第2.2节，数据来自 	rading_costs/equity_cost_history.csv）：
  - 日换手 5% → 年化成本 2.6%（与月调仓相当）
  - 日换手 10% → 年化成本 5.19%
  - 日换手 20% → 年化成本 10.38%
  - 日换手 30% → 年化成本 15.57%
  - 日换手 50% → 年化成本 25.96%
- 文档只要求报告 daily_turnover_capacity_report，但**没有设定换手率上限**
- S1-D 的 nnual_turnover_max: 3.0（Soft Floor）是**年化指标**，不是日换手率上限

**关键缺口**：
- 缺乏日度换手率上限
- 缺乏日度换手率控制机制（如 top-N 持仓重叠约束）
- 成本敏感性（1x/2x/3x）虽有要求，但缺乏决策规则

### 改进建议

1. **明确日换手率上限**：建议设置日换手率上限（如单边 20%/日），对应年化约 50x ≈ 不可接受；但需结合实际策略IC论证
2. **控制机制**：通过 top-N 持仓数量和持仓重叠率（与上一日持仓的重叠比例）间接控制日换手
3. **明确决策规则**：当日换手率超过阈值时，应有明确的处理规则（如减少调仓比例、仅调整部分持仓等）
4. **披露实际日换手率**：在 daily_orders_audit 和 daily_turnover_capacity_report 中必须包含日换手率统计

---

## 审查点 3：指数衰减加权半衰期选择

### 评分：6 / 10

### 具体发现

**半衰期 12-18 月的选择依据**

数据来源：quant_strategy_research_plan_detailed.md 第6.1.5节、alidation_params.json 第 	raining_weighting 节

- alidation_params.json：default_half_life_months: 12，llowed_half_life_sensitivity_months: [12, 18]
- 公式：ow_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))
- 文档说明：
  - 12 个月为默认半衰期
  - 18 个月为预注册敏感性
  - 6/24/36 个月只能作为研究网格，不能进入 keep

**问题：选择 12 个月的依据是什么？**

- 文档未引用任何文献或实证研究支持 12 个月半衰期
- 未说明 12 个月与 A股市场特征（如 3-5 年牛熊周期）的对应关系
- "6/24/36 个月只作研究网格" 暗示这些值未被认真考虑，但未解释原因

**是否有敏感性分析方案？**

- alidation_params.json 明确要求报告 ow_equal_vs_date_balanced_result_delta
- R8 第3.2节："半衰期12-18月的选择依据需要补充（文献支持？敏感性分析？）"
- 但截至 R9，**尚未看到实际的敏感性分析结果**
- 敏感性分析要求仅停留在"应报告"层面，没有具体实施方案

### 改进建议

1. **补充选择依据**：建议引用以下来源之一：
   - 学术文献（如 Lopez de Prado, Marcos 的 "Advances in Financial Machine Learning》中关于 sample weighting 的建议）
   - A股实证研究（如 12 个月是否覆盖 1 年财报周期、是否匹配 A股投资者行为周期等）
   - 本地数据驱动证据（如不同半衰期在训练窗口内的 ICIR 对比）
2. **敏感性分析方案具体化**：
   - 预注册 12 月 vs 18 月的敏感性实验（已在 llowed_half_life_sensitivity_months 中）
   - 明确敏感性分析的输出格式（ICIR 对比、组合收益对比）
   - **关键**：敏感性分析结果不得用于择优，只能作为"是否需要调整半衰期"的参考
3. **等权基线对照**：必须始终保留 5 年等权对照（equal_weight_control_required: true），作为 decay 方案的对比基准

---

## 综合评估

| 审查点 | 评分 | 核心问题 |
|--------|------|----------|
| S1-M Walk-Forward 设计 | 7/10 | 24步门槛合理，但未披露实际可运行步数；5年窗口缺乏敏感性 |
| S1-D 换手率控制 | 5/10 | **日换手率上限完全缺失**，R8 已预警但未解决 |
| 指数衰减半衰期 | 6/10 | 12个月选择依据缺失；敏感性分析仅有框架无落地结果 |

**最高优先级**：S1-D 日换手率上限缺失是当前最紧迫的问题，直接影响策略可交易性和成本评估。

**数据来源声明**：
- alidation_params.json（版本 2026-04-30-r8-daily-selection）
- quant_strategy_research_plan_detailed.md（2026-04-30 版）
- consensus_audit_r8.md（2026-04-30 版）
- 	rading_costs/equity_cost_history.csv（R8 引用的原始成本数据）
