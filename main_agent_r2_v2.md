# Main Agent R2 独立判断（v2）

> 日期：2026-05-01
> 角色：Main Agent（金融工程/量化策略/ML/DL/架构设计专家）
> 分歧点：6个

---

## 分歧点 1：统计功效MDE

**立场：同意 DeepSeek — P1（非P0）**

DeepSeek 的论点正确但优先级判断过高。24步OOT在10%单侧alpha下，检测CAGR>5%的alpha功效不足30%（粗略估计：24步×12月=288个月样本，标准误约1.5-2%，5%alpha的z-stat约2.5-3.3）。这是已知的OOT样本量限制，不是文档缺陷。

**建议**：在§5.5增加一段MDE说明："24步OOT对年化alpha<5%的策略功效不足30%，alpha>8%的功效约70-80%。OOT的主要作用是smoke test（排除IC<0.01的弱信号），不是精确功效分析。完整OOT约180步（2005-2025）提供足够功效。" 这是P1说明性补充，不是阻塞性P0。

---

## 分歧点 2：Phase A0工作量

**立场：部分同意 Coder — 30-50工作日（介于两者之间）**

文档25-45天偏乐观但不离谱。Coder的35-60天包含了SQLite schema DDL和ModelRegistry持久化，这些确实是额外工作，但Coder可能高估了复杂度——SQLite schema可以用ORM自动生成，ModelRegistry可以用简单的JSON+文件系统实现。

**建议**：调整为30-50工作日。A0.1从2-3周调整为2.5-3.5周（增加WalkForwardCalendarValidator的边界case测试），A0.2从3-6周调整为3-5周（SQLite schema可用模板生成，不需要从零设计）。

---

## 分歧点 3：CSRP命中窗口

**立场：同意 Review — P1，需预注册**

CSRP命中窗口应与标签持有期一致：S1-M使用20日标签→命中窗口=20日，S1-D使用1日标签→命中窗口=1日。这在逻辑上是一致的——信号预测的是N日forward return，命中窗口也应是N日。

**建议**：在§9.1.5增加："CSRP命中窗口主口径=标签持有期（S1-M=20日，S1-D=1日），敏感性报告10/40日。排列检验shuffle次数≥1000次。" 这是P1补充。

---

## 分歧点 4：分层裁剪与capital overlay执行顺序

**立场：同意 Review — P0，需明确定义**

正确顺序是：**先sleeve内裁剪 → 再capital overlay → 最后sleeve间归一化**。

理由：
1. 裁剪是alpha信号层面的操作（基于score确定性），应在capital overlay之前完成
2. Capital overlay是总仓位管理（基于市场状态），应用于裁剪后的sleeve权重
3. 最后sleeve间归一化确保总权重=capital_multiplier

如果顺序反过来（先overlay再裁剪），则capital_multiplier会放大裁剪前的极端权重。

**建议**：在§7.1和§9.3明确执行顺序："Step 1: 每个sleeve内按score确定性裁剪至turnover上限 → Step 2: 将裁剪后的sleeve权重 × capital_multiplier → Step 3: sleeve间归一化至目标总敞口。"

---

## 分歧点 5：sleeve FDR计入规则

**立场：部分同意 DeepSeek — P1（非P0）**

DeepSeek的论点正确：分层sleeve确实产生新假设，扩大实验族。但影响程度取决于实现方式：
- 如果sleeve只是在已有的alpha信号上做分层持仓（不独立训练模型），则实验族增加有限（约5-10个sleeve×原有实验数）
- 如果sleeve独立训练模型，则实验族显著扩大

当前文档的sleeve设计是前者（分层持仓，不独立训练），因此对FDR的影响是可控的。

**建议**：在§5.1增加："分层sleeve的test_family_id继承自其基础因子方向+标签+模型组合，sleeve本身不产生独立实验。但sleeve间的交叉比较（如微盘vs大盘sleeve的IC差异）应作为独立假设计入FDR。" 这是P1澄清。

---

## 分歧点 6：concept shift独立性假设

**立场：同意 DeepSeek — P1，需定量说明**

DeepSeek的论点正确：walk-forward IC存在自相关（典型lag-1自相关0.2-0.4），5/6步中5步为负的误报率在独立假设下是10.9%，但在自相关下会显著升高。

定量估计：如果IC lag-1自相关ρ=0.3，则6步中连续5步同号的概率远高于独立假设。粗略估计：有效独立样本数≈6/(1+2×0.3)≈3.75，5/6步同号的概率≈25-30%（vs独立假设的10.9%）。

**建议**：在§4.1增加说明："5/6步门槛基于步间独立假设。Walk-forward IC可能存在自相关（典型lag-1 ρ=0.2-0.4），实际误报率可能高于10.9%。建议在OOT报告中同时报告IC的lag-1自相关系数，如果ρ>0.3，考虑使用更严格的门槛（如6/6步全部为负）或对IC序列做block bootstrap后再计算概念漂移概率。" 这是P1方法论说明。

---

## R2 共识总结

| 分歧点 | 共识 | 优先级 |
|---|---|---|
| 1. MDE | 补充说明性段落，非阻塞性 | P1 |
| 2. Phase A0 | 调整为30-50工作日 | P1 |
| 3. CSRP命中窗口 | 主口径=标签持有期，敏感性10/40日 | P1 |
| 4. 裁剪与overlay顺序 | 先裁剪→再overlay→再归一化 | P0 |
| 5. sleeve FDR | sleeve不产生独立实验，但sleeve间比较计入FDR | P1 |
| 6. concept shift独立性 | 补充IC自相关说明和定量估计 | P1 |

---

*Main Agent R2 完成。6个分歧点中1个P0（裁剪与overlay执行顺序），5个P1。*
