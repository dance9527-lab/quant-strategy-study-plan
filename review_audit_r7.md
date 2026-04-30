# A股量化策略研究计划 — 第七轮审计报告（2026-04-30）

> **审计重点**：日调仓+模型更新训练方案 + 整体方案一致性
> **评分变化**：8.8 → 9.0/10

---

## 一、审计背景与分工

本轮审计为第 7 轮独立审查，由 4 位 Agent 并行完成：

- **Agent 1（量化代码 Review）**：本报告，聚焦日调仓和模型更新机制
- **Agent 2（数据工程）**：日频数据底座验证
- **Agent 3（成本和流动性）**：日调仓交易成本影响
- **Agent 4（文档一致性）**：与前六轮共识的冲突检查

本报告为 Agent 1 的独立审计产出。

---

## 二、审计发现：日调仓方案

### 2.1 文档中是否新增了日调仓方案？

**结论：已完整建立，且两条主线已清晰分离。**

从 quant_strategy_research_plan_detailed.md（第 9.1 节）确认：

| 特征 | S1-M 月选股 | S1-D 日选股 |
|---|---|---|
| 主标签 | 20 日 forward excess/rank | 1 日和 5 日 forward excess/rank |
| 调仓 cadence | 约 21 个交易日调仓 | 每日盘后候选，T+1 执行；默认每日滚动调仓或分批更新 |
| 模型重训 | 默认每 63 个交易日重训 | 默认每 63 个交易日重训；每日重训只作后置敏感性 |
| 预测频率 | 约每月一次 | 每日盘后重算分数 |

**关键约束已明确写入：**
- S1-D "每日预测不等于每日重训"（Section 7.1 walk-forward 参数表注释）
- S1-D "可按日度滚动调仓或预注册分批更新"（Section 9.1 双主线定义）
- "S1-D 日选股执行审计" 已列为 P1 阻塞项（Section 9.1 S1 启动前置条件表）

### 2.2 日调仓与月调仓的关系

**关系：平行两条主线，不是替代。**

- S1-M（月选股）和 S1-D（日选股）是"同等重视、平行启动"的同级研究 cadence（Section 1.2.1 表头注释、Section 9.1 表头注释）
- "两条主线同等重视、平行启动，但必须各自有独立 track_id、calendar、label、orders audit、capacity report 和实验台账"（Section 9.1）
- "不得把一条主线的 OOT/holdout 结果作为另一条主线的选择依据"（Section 9.1）
- S1-M 通过 1 亿容量不代表 S1-D 也通过；月选股和日选股容量独立（Section 9.1 S1 启动前置条件注释）

### 2.3 日调仓交易成本处理

**结论：已有系统性处理方案，但 A 股日频成本敏感性需在 S1-D 中明确报告。**

trading_costs.equity_cost_history 已入仓（23 行，1990-12-19 至 2023-08-28）。文档要求的成本处理包括：

| 成本项 | 处理方式 | 文档出处 |
|---|---|---|
| 佣金、印花税、过户费、规费 | 来自 equity_cost_history | Section 3.3 |
| 滑点 | L1 日频保守模型使用 open/amount/participation | Section 3.2 开盘冲击分层 |
| 冲击成本 | S2 深化分档；S1 至少保守版本 | Section 3.3 |
| 成本 1x/2x/3x 敏感性 | S1-D 必须报告 | Section 9.1 S1 启动前置条件（"成本 1x/2x/3x 敏感性"）|
| 日换手和成本拖累 | S1-D 必须报告 | Section 9.1 S1 启动前置条件 |
| 容量后成本 | S1-D 必须报告 | Section 9.1 S1 启动前置条件 |

**审计关注点**：日选股的高换手特性（Section 7.1 备注："高换手、成本拖累"是 S1-D 主风险）意味着成本后超额比月选股更难保持。文档已将"成本 1x/2x/3x 敏感性"列为 P1 阻塞项，日选股 keep 结论必须通过此敏感性。

---

## 三、审计发现：模型更新训练

### 3.1 是否新增了每日/定期模型更新的机制？

**结论：是，但已严格限制为"每日预测，每日**不**重训"。**

文档明确（Section 4.1 模型路线 + Section 7.1 walk-forward 参数）：

- 默认重训频率：每 63 个交易日（约 3 个月）
- S1-M：每 21 个交易日调仓/预测，非重训 step 使用冻结模型
- S1-D：每日盘后重算分数，非重训 step 使用冻结模型；"每日重训只作后置敏感性"
- "两次重训之间使用最近一次符合 purge 规则的冻结模型版本"（Section 4.1）

### 3.2 更新频率与调仓频率的配合

**结论：已正确分离预测频率和重训频率。**

| 组合 | 预测/调仓 | 模型重训 | 文档依据 |
|---|---|---|---|
| S1-M | 每 ~21 交易日 | 每 63 交易日 | Section 7.1 参数表 + Section 4.1 |
| S1-D | 每日盘后 | 每 63 交易日（敏感性可月度/每日） | Section 7.1 参数表 + Section 9.1 |

关键约束：
- "两次重训之间使用最近一次符合 purge 规则的冻结模型版本"（Section 4.1）
- "日度决策窗口...必须同时满足 label maturity"（Section 7.1 OOT 规则）

### 3.3 在线学习/增量学习的具体实现方式

**结论：当前采用"冻结模型 + 定期重训"，未实现正式在线学习/增量训练。**

文档明确（Section 4.1）：
- "模型默认每 63 个交易日重训一次"
- 在线微调（online fine-tuning）：R5 后已废弃，不作为近期执行路径（Section 4.1 Concept shift 处理 + Section 6 禁止事项 #11）
- R5 废弃方案包括：双轨制、动态 alpha、在线 Track B

当前实现是"预注册单轨 5 年 rolling + 指数衰减 sample weight + 数据驱动告警"，而不是在线更新模型权重。

### 3.4 与 walk-forward 框架的兼容性

**结论：完全兼容，purge/embargo 约束已明确。**

关键规则：
- "所有模型训练截止日都必须满足 train_end <= oot_start - purge_days，并同时满足 label maturity 和 embargo"（Section 7.1 硬规则）
- "Step k 的预测必须先落盘并记录 model_version、train_rows_hash..."（Section 7.1 Concept shift 硬规则）
- S1-D 的训练和验证必须按 decision_date 横截面分组；Ranker 的 group 必须是日期截面，不能做 random row split（Section 7.1 S1-D 补充规则）

---

## 四、整体方案一致性

### 4.1 新增内容与前六轮共识是否矛盾？

**结论：完全一致，无矛盾。**

R5 共识关键点（已固化于 R5/R6）：
- 废弃双轨制、动态 alpha、在线 Track B
- 采用单轨 5 年 rolling + 指数衰减 sample weight
- 预注册候选 + 数据驱动告警

本轮新增内容（S1-D 日选股主线）：
- 同样是单轨 5 年 rolling（Section 7.1：5 年训练窗口对两条主线均适用）
- 同样使用指数衰减加权（Section 6.1.5：R5 训练权重适用于 S1-M 和 S1-D）
- 同样采用冻结模型 + 定期重训（不在线更新）
- 同样使用成熟 IC 驱动的 yellow/red 状态机（不人工干预）

**无任何矛盾**。

### 4.2 指数衰减加权是否仍然适用？

**结论：适用，且已覆盖 S1-D 场景。**

Section 6.1.5（R5 训练权重）定义：
  row_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))

- age_trading_days = 样本 decision_time 到当前 step train_end 的交易日年龄
- S1-D 的每个交易日决策截面均对应一个 train_end（对应那个 step 的训练截止日）
- 因此 S1-D 同样适用该公式，权重由样本距离各自 step 训练截止日的交易日年龄决定

S1-D 的额外要求（Section 6.1.5 + Section 7.1）：
- 必须同时报告 date_balanced_decay_weight 对照
- 两种口径均在每个训练 step 内归一化到均值 1

### 4.3 S1 通过条件是否需要调整？

**结论：S1-D 的特殊风险已纳入 S1 Hard Gate，无需调整通用框架。**

S1 Hard Gate 对 S1-D 的关键附加项（Section 9.1 S1 启动前置条件）：

| 附加项 | 状态 |
|---|---|
| S1-D 日选股执行审计（daily_selection_rebalance_v1、daily_orders_audit、daily_turnover_capacity_report） | P1 阻塞项 |
| 成本 1x/2x/3x 敏感性 | P1 阻塞项 |
| 日换手、订单失败、短持有期滚动持仓会计 | S1-D 必须报告 |
| S1-D 与 S1-M 持仓重叠度和冲突交易统计 | S1-D 必须报告 |
| 日度成熟 IC 状态机 | 随 S1 输出 |
| 10/21/40 日 block bootstrap 敏感性 | S1-D 保留（不能用 1 日 block） |

这些附加项已充分覆盖 S1-D 的高换手、短持有期、高噪声风险，**无需修改通用 S1 Hard Gate 框架**。

---

## 五、数据验证

### 5.1 日调仓需要的数据是否可从仓库获取？

**结论：核心日频数据已就绪，S1-D 专项数据已有安排。**

| 数据需求 | 仓库状态 | 确认 |
|---|---|---|
| 日频价格/收益 | prices_daily_returns（17,599,789 行） | [PASS] |
| 日频因子（market-only） | features/market_daily_v1（15,420,654 行） | [PASS] R7 已解除阻塞 |
| 日频 forward 标签（1/5/10/20 日） | labels/forward_returns_v1（15,420,654 行） | [PASS] R7 已解除阻塞 |
| 日频交易成本 | trading_costs.equity_cost_history（23 行） | [PASS] 已入仓（部分为研究假设） |
| 日频成交额/量 | tradability_daily_enriched（18,177,689 行） | [PASS] 可用于 ADV |
| 日频涨跌停/停牌 | tradability_daily_enriched | [PASS] |
| 日度 orders audit | 需要新建 daily_orders_audit | [WARN] 尚未入仓（P1 阻塞） |
| 日度 capacity/turnover report | 需要新建 daily_turnover_capacity_report | [WARN] 尚未入仓（P1 阻塞） |

**审计结论**：R7 已解除 features/labels 占位阻塞，核心日频研究数据已就绪。但 S1-D 正式 keep 仍需等待 daily_orders_audit 和 daily_turnover_capacity_report 的预注册和产出（P1 阻塞项）。

### 5.2 日频因子的计算频率与仓库数据更新频率是否匹配？

**结论：数据基础设施支持日频研究，交付物已通过审计。**

R7 审计产出确认：
- feature_label_panel_v1_manifest.json 已生成
- pit_feature_audit_market_daily_v1.json 已生成（PASS）
- label_audit_forward_returns_v1.json 已生成（PASS）
- source_status_audit_r7.json 已生成

日频因子（日度 IC、每日盘后分数）理论上可每日更新，实际更新频率取决于：
1. 数据管道的 T+1 延迟（prices_daily_returns 等表是否在 T+1 开盘前就绪）
2. 因子计算管道的运行时间
3. 预测落盘和记录机制

当前文档对"日度因子计算频率"无硬性 SLA 要求，但明确要求（Section 13 Step 1 输出）：
- "S1-D 面板绑定：1/5 日标签、日度 decision calendar、daily candidate schema、日度订单审计规则"

---

## 六、R7 新增发现

### 6.1 S1-D 验证复杂度被低估

**风险等级：中**

S1-D 与 S1-M 相比，额外需要：
1. 每日盘后 daily_selection_rebalance_v1 候选清单
2. 每日 daily_orders_audit
3. 每日 daily_turnover_capacity_report
4. 日度 IC 序列 + 周/月汇总 + concept shift 状态机
5. 成本 1x/2x/3x 敏感性
6. 与 S1-M 持仓重叠度

24 个 OOT step 对 S1-M 约等于 24 个月（约 2 年），但对 S1-D 意味着 24 个日度决策窗口。文档（Section 5.5）已认识到这一点："S1-D 可用 1 日决策/调仓但报告时按交易日和月度汇总同时披露，不能把 24 步写成全量日选股验证"。

**建议**：在 Step 0 审计阶段，应明确 S1-D 的验证汇报结构，避免将 24 个 OOT step 误解为"只需 24 个日度回测"。

### 6.2 S1-D 模型重训频率存在敏感性歧义

**风险等级：低**

文档中关于 S1-D 重训的描述有三层：
1. "默认每 63 个交易日重训一次"（Section 4.1 + Section 7.1）
2. "S1-D 每日盘后重算分数...每日重训只作后置敏感性"（Section 4.1 模型路线表）
3. "月度重训或每日重训只能作为预注册敏感性"（Section 9.1.5 S1.5 候选方案）

三层描述均一致，但"月度重训"在 S1-D 语境下可能引发歧义（因为 S1-M 已定义了约 21 交易日=月度调仓 cadence）。若 S1-D 采用"月度重训"，则重训周期与 S1-M 相同（~63 交易日）。

**无实质问题**：文档已将"63 交易日"明确为默认重训周期，其他频率均标注为敏感性。

### 6.3 日选股容量独立验证的卡点

**风险等级：中**

Section 9.1 明确："月选股通过 1 亿容量不代表日选股也通过"。S1-D 的容量验证必须独立完成，且需要：
- 日度参与率（vs 月度参与率对 S1-M 的影响）
- 每日成交失败（vs 月度调仓的低频成交失败）
- 日换手和成本拖累（日频交易的累积成本效应）

当前 daily_orders_audit 和 daily_turnover_capacity_report 尚未建立（P1 阻塞），这意味着 S1-D 的容量 keep 结论无法正式产出。

**建议**：Step 0 应优先固化 S1-D 的 orders audit schema 和 turnover/capacity report schema，避免 S1-D 完成后因缺乏预注册台账而无法 keep。

---

## 七、评分汇总

| 维度 | 评分 | 核心发现 |
|---|---|---|
| 日调仓方案完整性 | 9.2 | 两条主线平行，关系清晰，日调仓不等于日重训约束到位 |
| 模型更新机制合理性 | 9.0 | 冻结模型+定期重训符合 walk-forward 框架，在线学习歧路已封堵 |
| 与前六轮共识一致性 | 9.5 | 完全一致，无矛盾；指数衰减加权覆盖 S1-D |
| S1-D 特殊风险覆盖 | 8.5 | Hard Gate 附加项到位，但 orders audit 台账未就绪 |
| 日频数据底座 | 8.8 | features/labels R7 已解除阻塞，orders audit 仍 P1 阻塞 |
| **综合** | **9.0/10** | 日选股主线设计合理，与月选股主线平行独立；主要风险在执行台账未就绪 |

---

## 八、R7 累积评分总览

| 轮次 | 评分 | 核心改进 |
|------|------|---------|
| 第一轮 | 6.5->7.0 | S1门槛/embargo/OOT/purge参数共识 |
| 第二轮 | 7.0->7.5 | S1条件分层/Exploratory Tracking/regime告警 |
| 第三轮 | 7.5->8.0 | 因子正交化/Newey-West/A股制度性风险 |
| 第四轮 | 8.0->8.5 | Walk-forward澄清/valuation缺口/P1因子验证 |
| 第五轮 | 8.5->8.5 | 放弃双轨制，采用指数衰减+人工审查 |
| 第六轮 | 8.5->8.8 | R5集成验证/文档一致性/S1卡点确认 |
| 第七轮 | 8.8->9.0 | 日调仓+模型更新方案审查/数据验证/执行台账确认 |

---

## 九、建议行动项

| 优先级 | 行动项 | 责任阶段 |
|--------|--------|---------|
| P0 | S1-D orders audit schema 预定义（daily_orders_audit 字段） | Step 0 |
| P0 | S1-D turnover/capacity report schema 预定义 | Step 0 |
| P0 | holdout_access_log.tsv 对 S1-D 的独立 track_id 绑定 | Step 0 |
| P1 | S1-D 日度 walk-forward calendar 生成（含日度 step vs 月度 step 区分） | Step 0 |
| P1 | 明确 S1-D 24 OOT step 的汇报结构（避免误解为 24 个日度回测） | Step 0 文档补充 |
| P2 | S1-D 与 S1-M 持仓重叠度统计方法预定义 | Step 3 |
| P2 | 日度 IC 状态机与月度 IC 状态机的报告分离 | Step 3 |

---

*审计人：Agent 1（量化代码 Review）*
*日期：2026-04-30*
*本报告为独立审计发现，未与其他 Agent 讨论。*