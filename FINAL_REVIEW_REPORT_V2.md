# 四位专家独立审计 + 多轮讨论共识报告（v2 — 更新后文档）

> 审计日期：2026-05-01
> 参与者：Main Agent、Review Agent、DeepSeek Agent、Coder Agent
> 轮次：R1独立审计 → R2辩论（互相challenge） → R3回应（被说服/坚持）
> 文档版本：更新后的 quant_strategy_plan.md 和 quant_strategy_research_plan_detailed.md

---

## 一、讨论流程

| 轮次 | 形式 | 产出 |
|---|---|---|
| R1 | 四位独立审计 | 每位agent独立评估文档，输出审计报告 |
| R2 | 辩论轮（互相challenge） | 每位agent读取其他三位R1报告，对5个分歧点明确站队并反驳对方 |
| R3 | 回应轮（被说服/坚持） | 每位agent读取其他三位R2辩论报告，回应挑战，更新或维持立场 |

---

## 二、上一轮共识采纳审查

上一轮11项共识**全部正确采纳**（11/11）：

| # | 共识 | 采纳状态 |
|---|---|---|
| 1 | GMSL数据不完整，分GMSL-v1/v2 | ✅ |
| 2 | Phase A0 拆分A0.1+A0.2 | ✅ |
| 3 | Walk-forward Calendar系统基石 | ✅ |
| 4 | Concept shift 5/6门槛 | ✅ |
| 5 | 24步OOT只是smoke test | ✅ |
| 6 | SQLite WAL实验台账 | ✅ |
| 7 | 1日标签purge=20天 | ✅ |
| 8 | Block bootstrap敏感性{10,21,42} | ✅ |
| 9 | 因子方向Tier 1/2/3 | ✅ |
| 10 | 多重检验完整实验族 | ✅ |
| 11 | 标签misalignment P0 | ✅ |

---

## 三、5个分歧点的讨论过程与最终共识

### 分歧点1：MDE功效分析

**讨论过程**：
- R1：DeepSeek P0, Main P1, Coder P0, Review 未单独讨论
- R2：DeepSeek P0（给出功效表：24步对Sharpe=0.5功效仅17%）, Main P1, Coder P0, Review P1
- R3：**DeepSeek 改为 P1+**（接受"keep基于完整OOT"论点）, Main P1, Coder **改为 P1**, Review P1

**最终共识：P1（4:0）**

**具体内容**：
- 24步OOT对年化Sharpe=0.5的alpha功效仅17%，对Sharpe=0.8的功效约33%
- 完整OOT约180步对Sharpe=0.5的功效约58%，对Sharpe=1.0的功效约95%
- 在§5.5增加功效分析表和MDE说明，明确24步smoke test的检测能力边界
- 在validation_params.json中记录MDE分析的假设和结论

**DeepSeek R3 让步说明**：接受Main/Review的"keep决策基于完整OOT（~180步）"论点，将MDE从P0调整为P1+。但坚持在文档中补充功效分析表——这不是阻塞S1启动，而是量化框架的能力边界。

### 分歧点2：CSRP命中窗口

**讨论过程**：
- R1：Review P0, Main P1, DeepSeek P0, Coder P0
- R2：四位一致P0。Main被Review说服从P1改为P0
- R2辩论：DeepSeek提出窗口长度修正（3个OOT step vs 20日标签持有期）
- R3：Main接受DeepSeek修正

**最终共识：P0（4:0）**

**具体定义**：
| 参数 | 定义 |
|---|---|
| 命中窗口主口径 | 信号触发后**3个OOT step**（~3个月） |
| 命中标准（主口径） | 3步中至少2步的组合收益（扣除成本后）< benchmark收益 |
| 命中标准（辅助报告） | 3步中至少2步的成熟IC < 0 |
| 排列检验 | ≥1000次block permutation（block=21天） |
| 最小信号数 | n_signals ≥ 5才报告，≥ 20才作为tighten-only依据 |
| 敏感性 | 2-step / 3-step / 5-step 窗口 |

**关键被说服点**：
- Main R2：被Review说服从P1改为P0（命中窗口是FPR框架的前提参数）
- Main R3：被DeepSeek说服将窗口从"标签持有期（20日）"改为"3个OOT step"

### 分歧点3：裁剪与overlay执行顺序

**讨论过程**：四位在R1即一致为P0，无分歧。

**最终共识：P0（4:0）**

**执行顺序**：
```
Step 1: 模型生成目标权重（满仓，总和=1.0）
Step 2: 分层裁剪（总换手→行业→个股），每层等比例缩减
Step 3: 归一化到 1.0（裁剪后权重总和可能≠1.0）
Step 4: 乘 capital_multiplier（牛市0.8-1.0 / 震荡0.4-0.7 / 熊市0-0.3）
Step 5: 现金 = 1 - sum(w_final)
```

**为什么必须先裁剪再overlay**：
- 先overlay再裁剪会低估换手（DeepSeek R2给出反例）
- 裁剪后归一化确保overlay的语义清晰（multiplier直接表示满仓比例）
- 代码中用断言强制顺序

### 分歧点4：Sleeve FDR计入规则

**讨论过程**：
- R1：DeepSeek P0, Main P1, Review P1, Coder P1
- R2：DeepSeek P0（BH阈值收紧5倍）, Review **改为P0**（被DeepSeek说服）, Main P1, Coder P1
- R3：Main **改为P0**（被DeepSeek说服）, Coder **改为P0**（被DeepSeek说服）

**最终共识：P0（4:0）**

**关键被说服点**：
- Main R3：DeepSeek的BH阈值计算（收紧5倍）证明"影响可控"是错误的
- Review R3：用药物临床试验亚组类比——即使共享数据，5个亚组的假设检验仍需多重比较校正
- Coder R3：自己的"共享test_family_id"方案实际上接受了阈值收紧，并未解决核心关切

**具体规则**：
- 所有sleeve的尝试计入attempt_count，共享test_family_id
- BH校正在整个实验族上执行
- 实验报告必须披露："本次实验族包含N个sleeve，BH校正后的p值阈值为X"
- 如果5×收紧过于严格，可减少sleeve数量或使用Storey-q

### 分歧点5：Concept shift独立性假设

**讨论过程**：
- R1：DeepSeek P0, Review P0, Main P1, Coder P1
- R2：DeepSeek **修正R1错误**（正自相关降低误报率，非升高）, 仍P0。Review P0（采纳修正）。Main P1, Coder P1
- R3：Main承认计算错误但维持P1, Coder维持P1, DeepSeek和Review维持P0

**最终结果：2:2分裂，Main裁决为P1（附严格条件）**

**R2关键修正**：DeepSeek发现R1混淆了FPR和功效。正自相关在零假设下**降低**误报率（ρ=0.3时从10.9%降至~2-5%），5/6门槛比预期更保守。真正风险是功效不足（检测真实concept shift的能力降低）。

**裁决理由**：
- Main和Coder认为：功效不足不阻塞S1启动，可在OOT阶段通过block bootstrap动态调整
- DeepSeek和Review认为：功效不足（80-85%漏报率）是系统性设计缺陷
- 裁决：P1，但增加严格条件——必须在OOT报告中报告IC自相关和功效，如果功效<50%标注inconclusive

**具体要求**：
1. §4.1修正理论解释："5/6门槛的10.9%误报率基于步间独立假设。实际walk-forward中IC存在正自相关（因训练窗口重叠），正自相关**降低**零假设误报率（实际约2-5%），但同时降低检测真实concept shift的功效。"
2. OOT报告必须同时报告IC lag-1自相关系数ρ
3. 如果ρ > 0.3，用block bootstrap（block=21天，≥5000次重采样）估计实际误报率和功效
4. 如果功效 < 50%，标注"inconclusive - insufficient power"，建议增加OOT步数或放宽门槛（如4/6）
5. 在validation_params.json中记录`concept_shift_ic_autocorrelation_threshold: 0.3`

---

## 四、立场变化追踪

### R2辩论轮立场变化（vs R1）

| Agent | 分歧点 | R1→R2变化 | 原因 |
|---|---|---|---|
| Main | CSRP命中窗口 | P1→P0 | 被Review说服：命中窗口是FPR框架前提参数 |
| Review | Sleeve FDR | P1→P0 | 被DeepSeek说服：BH阈值收紧5倍 |
| DeepSeek | Concept shift | 修正方向 | 发现R1错误：自相关降低误报率，非升高 |

### R3回应轮立场变化（vs R2）

| Agent | 分歧点 | R2→R3变化 | 原因 |
|---|---|---|---|
| Main | Sleeve FDR | P1→P0 | 被DeepSeek说服：BH阈值收紧5倍不是"可控"影响 |
| Coder | MDE | P0→P1 | 被Main/Review说服：keep基于完整180步OOT |
| Coder | Sleeve FDR | P1→P0 | 被DeepSeek说服：共享test_family_id未解决核心关切 |
| DeepSeek | MDE | P0→P1+ | 接受"keep基于完整OOT"论点，但坚持补充功效表 |

### 被说服次数统计

| Agent | 被说服改变立场次数 | 被说服的具体点 |
|---|---|---|
| Main | 2次 | CSRP P1→P0, Sleeve FDR P1→P0 |
| Review | 1次 | Sleeve FDR P1→P0 |
| DeepSeek | 1次 | MDE P0→P1+ |
| Coder | 2次 | MDE P0→P1, Sleeve FDR P1→P0 |

---

## 五、综合评分

| 维度 | 评分 | 说明 |
|---|---|---|
| 上一轮共识采纳 | 9.5/10 | 11/11全部正确采纳 |
| 新增内容质量 | 8.5/10 | sleeve/overlay/CSRP/ET设计合理，R2+R3补充了关键细节 |
| 统计严谨性 | 8.5/10 | R2修正了concept shift误报率误解，R3明确了MDE功效边界 |
| 文档一致性 | 9.0/10 | 总纲与执行规范高度一致 |
| 文档完备性 | 8.5/10 | R2+R3发现了5个需补充的P0细节 |
| 讨论质量 | 9.0/10 | 真正的多轮辩论，4次被说服改变立场，3个关键纠正 |
| **综合评分** | **8.8/10** | **从上一轮8.1/10提升至8.8/10** |

---

## 六、待改进项清单

### P0（3项，已达成共识，需文档补充）

| # | 问题 | 共识来源 | 建议修复 |
|---|---|---|---|
| 1 | CSRP命中窗口定义 | R2+R3 4:0共识 | §9.1.5增加：主口径=3个OOT step，组合收益<基准，排列检验≥1000次 |
| 2 | 裁剪与overlay执行顺序 | R1 4:0共识 | §7.1+§9.3增加：裁剪→归一化→overlay，代码断言强制 |
| 3 | Sleeve FDR计入规则 | R2+R3 4:0共识 | §5.1增加：sleeve共享test_family_id，BH校正在整个实验族执行 |

### P1（6项，建议补充）

| # | 问题 | 共识来源 | 建议修复 |
|---|---|---|---|
| 1 | MDE功效分析 | R3 4:0共识 | §5.5增加功效表（24步/180步对不同Sharpe的检测功效） |
| 2 | Concept shift理论修正 | R2+R3裁决 | §4.1修正：正自相关降低误报率（2-5%），但降低功效 |
| 3 | IC自相关报告 | R2+R3裁决 | OOT报告必须报告IC lag-1自相关，ρ>0.3时估计功效 |
| 4 | SQLite schema DDL | Coder R1 | §11补充CREATE TABLE+索引+WAL配置 |
| 5 | ModelRegistry持久化 | Coder R1 | §8.4补充SQLite+文件系统方案 |
| 6 | Sleevecross比较计入FDR | DeepSeek R2 | §5.1增加：sleeve间IC差异比较计入FDR |

---

## 七、讨论中的关键纠正

### 纠正1：Concept shift 误报率方向错误（DeepSeek R2）

**R1错误**：DeepSeek声称正自相关导致误报率从10.9%升高到33%
**R2修正**：正自相关**降低**零假设误报率（ρ=0.3时从10.9%降至~2-5%），R1混淆了FPR和功效
**影响**：5/6门槛比预期更保守（好消息），但检测真实concept shift的功效降低（坏消息）

### 纠正2：CSRP窗口长度不匹配（DeepSeek R2→R3）

**R1-R2错误**：Main建议命中窗口=标签持有期（20日）
**R2修正**：DeepSeek指出CSRP信号基于6个OOT step（~6个月），用20日窗口验证6个月的恶化趋势不匹配。应改为3个OOT step（~3个月）

### 纠正3：Sleeve FDR影响被低估（DeepSeek R2→R3）

**R1-R2错误**：Main认为"sleeve不独立训练模型，对FDR影响可控"
**R2修正**：DeepSeek计算BH阈值收紧5倍（从0.02到0.004），证明不是"可控"影响。Review用药物临床试验亚组类比进一步说明

### 纠正4：MDE功效边界被忽视（DeepSeek R1→R2）

**R1发现**：24步OOT对Sharpe=0.5的alpha功效仅17%
**R3共识**：四位一致接受P1——MDE不阻塞S1启动，但必须在文档中补充功效分析表

### 纠正5：功效不足时应放宽门槛而非收紧（Review R3）

**Main R2错误**：建议"如果ρ>0.3，考虑更严格门槛（如6/6）"
**Review R3修正**：功效不足时应**放宽**门槛（如4/6）来提高检测能力，而非收紧

---

## 八、最终结论

**文档质量：8.8/10（优秀）**

更新后的文档成功采纳了上一轮全部11项共识。通过R1独立审计→R2辩论→R3回应的真正多轮讨论，5个分歧点中4个达成共识（MDE、CSRP命中窗口、裁剪与overlay顺序、Sleeve FDR），1个（Concept shift）以2:2裁决解决。

**R2+R3的关键贡献**：
1. DeepSeek修正了concept shift误报率方向错误（自相关降低误报率，非升高）
2. DeepSeek提供了完整的MDE功效计算框架（24步/180步对不同Sharpe的检测功效）
3. Review纠正了"功效不足时应收紧门槛"的方向错误（应放宽）
4. 四位一致同意Sleeve FDR计入规则（BH阈值收紧5倍不是"可控"影响）

**建议**：
1. 优先修复3个P0（CSRP命中窗口、裁剪与overlay顺序、Sleeve FDR计入规则）
2. 补充6个P1（MDE功效表、Concept shift理论修正、IC自相关报告、SQLite schema、ModelRegistry、sleeve间比较FDR）
3. 修复后文档质量可达到9.0/10

---

*报告生成时间：2026-05-01 13:06 CST*
*审计流程：R1四位独立审计 → R2辩论（互相challenge） → R3回应（被说服/坚持） → 共识产出*
*R1平均分：8.1 → R2辩论后：8.5 → R3回应后：8.8/10*
*被说服改变立场：共6次（Main 2次、Review 1次、DeepSeek 1次、Coder 2次）*
*关键纠正：5个（concept shift方向、CSRP窗口长度、Sleeve FDR影响、MDE功效边界、门槛方向）*
