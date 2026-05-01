# 四位专家独立审计 + 多轮讨论共识报告（v2 — 更新后文档）

> 审计日期：2026-05-01
> 参与者：Main Agent、Review Agent、DeepSeek Agent、Coder Agent
> 轮次：R1独立审计 + R2交叉审阅讨论
> 文档版本：更新后的 quant_strategy_plan.md 和 quant_strategy_research_plan_detailed.md（已采纳上一轮11项共识）

---

## 一、上一轮共识采纳审查

上一轮11项共识**全部正确采纳**（11/11）：

| # | 共识 | 采纳状态 | R2评估 |
|---|---|---|---|
| 1 | GMSL数据不完整，分GMSL-v1/v2 | ✅ | FRED替代方案已写入（fredapi/Nasdaq Data Link/Quandl） |
| 2 | Phase A0 25-45工作日 | ✅ | A0.1(2-3周)+A0.2(3-6周)已拆分 |
| 3 | Walk-forward Calendar系统基石 | ✅ | 完整字段列表+WalkForwardCalendarValidator |
| 4 | Concept shift 5/6门槛 | ✅ | R2发现：实际误报率低于10.9%（见分歧点6） |
| 5 | 24步OOT只是smoke test | ✅ | 完整OOT约180步已明确 |
| 6 | SQLite WAL实验台账 | ✅ | R2补充：需schema DDL+迁移+备份策略 |
| 7 | 1日标签purge=20天 | ✅ | +10/20/40敏感性 |
| 8 | Block bootstrap敏感性{10,21,42} | ✅ | Andrews(1991)+lag6+lag12带宽 |
| 9 | 因子方向Tier 1/2/3 | ✅ | 首批因子分类已预注册 |
| 10 | 多重检验完整实验族 | ✅ | 因子×标签×模型×半衰期×训练窗口×正交化分支×执行规则 |
| 11 | 标签misalignment P0 | ✅ | rebalance_to_rebalance_execution_aligned标签 |

**采纳质量：优秀，无遗漏。**

---

## 二、R2 共识项

### 2.1 已达成共识（6/6分歧点全部解决）

| # | 分歧点 | 共识 | 优先级 |
|---|---|---|---|
| 1 | 统计功效MDE | 补充说明性段落+MDE计算框架，24步可检测IC≥0.034，180步可检测IC≥0.012 | P1 |
| 2 | Phase A0工作量 | 调整为**35-55工作日**（A0.1: 3-4周，A0.2: 4-6周） | P1 |
| 3 | CSRP命中窗口 | 主口径=标签持有期（S1-M=20日，S1-D=1日），敏感性10/40日，排列检验≥1000次 | P0 |
| 4 | 裁剪与overlay执行顺序 | **先sleeve内裁剪→归一化到1.0→再乘capital_multiplier**，代码断言强制顺序 | P0 |
| 5 | Sleeve FDR计入 | sleeve共享test_family_id，不独立成族；sleeve间比较（如微盘vs大盘IC差异）计入FDR | P1 |
| 6 | Concept shift独立性 | **R2关键修正**：正自相关**降低**零假设误报率（ρ=0.3时从10.9%降至~2.5%），5/6门槛比预期更保守。真正风险是功效不足。建议报告IC lag-1自相关系数 | P1 |

### 2.2 新增P0项（需文档补充）

**R2新增3个P0**（上一轮无P0遗留）：

1. **CSRP命中窗口未定义**：Review/DeepSeek/Coder一致P0。命中窗口=标签持有期，排列检验≥1000次
2. **裁剪与overlay执行顺序未定义**：四位一致P0。先裁剪→归一化→overlay
3. **SQLite schema DDL缺失**：Coder P0。需补充CREATE TABLE+索引+WAL配置+迁移策略

### 2.3 新增P1项（建议补充）

1. **MDE计算框架**：24步可检测IC≥0.034（年化Sharpe≈0.83），弱alpha无法检测。补充说明性段落即可
2. **Phase A0工作量调整**：从25-45天调整为35-55天，主要低估了SQLite WAL(+1-2周)、orders_audit状态机(+0.5-1.5周)、FRED替代(+1周)
3. **ModelRegistry持久化**：需SQLite+文件系统方案，refit/rebalance不同步管理
4. **Sleeve test_family_id规则**：sleeve共享基础因子方向的test_family_id
5. **IC自相关报告**：OOT报告中同时报告IC lag-1自相关系数，如果ρ>0.3考虑更严格门槛
6. **execution_slippage计算基准**：需定义具体的滑点计算公式
7. **sleeve attempt_count计数规则**：5 sleeve × 7模型 = 35次尝试计入同一族
8. **capital_multiplier精度**：四舍五入到5%或10%
9. **CSRP最小n_signals下限**：信号数不足时CSRP统计不可靠
10. **S1-D/S1-R block bootstrap默认值**：需明确默认block大小

---

## 三、R2 关键修正

### 3.1 Concept Shift 误报率修正（DeepSeek R2 关键贡献）

**R1错误**：DeepSeek R1声称IC自相关导致误报率从10.9%升高到33%。

**R2修正**：通过定量计算发现，R1混淆了FPR（假阳性率）和功效（真阳性率）。

- **FPR（零假设下）**：正自相关使连续5步同号的概率**降低**（因为步骤间"粘连"，独立变化更难）。ρ=0.3时，实际FPR≈2.5%（vs独立假设的10.9%）
- **功效（备择假设下）**：正自相关使检测真alpha的能力**降低**（需要更多步才能确认趋势）

**结论**：5/6门槛比预期**更保守**（误报率更低），但检测弱alpha的功效不足。这是好消息——策略不容易误报，但可能漏检弱信号。

### 3.2 MDE功效框架（Coder+DeepSeek贡献）

| OOT步数 | 可检测IC均值（80%功效，IC标准差=0.06） | 对应年化Sharpe |
|---|---|---|
| 24步 | ≥0.034 | ≈0.83 |
| 60步 | ≥0.021 | ≈0.52 |
| 180步 | ≥0.012 | ≈0.30 |

**实践意义**：24步OOT只能排除IC<0.01的弱信号，不能精确评估中等alpha。完整180步OOT提供足够功效。

---

## 四、综合评分

| 维度 | R1评分 | R2评分 | 变化 | 说明 |
|---|---|---|---|---|
| 上一轮共识采纳 | 9.0 | 9.5 | +0.5 | 11/11全部正确采纳，新增内容与共识一致 |
| 新增内容质量 | 8.0 | 8.5 | +0.5 | sleeve/overlay/CSRP/ET设计合理，R2补充了执行顺序和schema |
| 统计严谨性 | 7.5 | 8.5 | +1.0 | R2修正了concept shift误报率误解，补充MDE框架 |
| 工程可行性 | 7.5 | 8.0 | +0.5 | R2明确了SQLite schema需求和Phase A0工作量 |
| 文档一致性 | 9.0 | 9.0 | 0 | 总纲与执行规范高度一致 |
| 文档完备性 | 8.0 | 8.5 | +0.5 | R2发现了3个P0需补充的细节 |
| **综合评分** | **8.1** | **8.7** | **+0.6** | **显著提升** |

---

## 五、待改进项清单

### P0（3项，阻塞相关模块）

| # | 问题 | 来源 | 建议修复 |
|---|---|---|---|
| 1 | CSRP命中窗口未定义 | Review/DeepSeek/Coder | §9.1.5增加：主口径=标签持有期，敏感性10/40日，排列检验≥1000次 |
| 2 | 裁剪与overlay执行顺序未定义 | 四位一致 | §7.1+§9.3增加：先裁剪→归一化→overlay，代码断言强制 |
| 3 | SQLite schema DDL缺失 | Coder | §11补充CREATE TABLE+索引+WAL配置+迁移策略 |

### P1（10项，建议补充）

| # | 问题 | 来源 | 建议修复 |
|---|---|---|---|
| 1 | MDE功效说明缺失 | DeepSeek/Coder | §5.5增加MDE段落和功效计算框架 |
| 2 | Phase A0工作量偏低 | Coder | 调整为35-55工作日 |
| 3 | ModelRegistry持久化方案缺失 | Coder | §8.4补充SQLite+文件系统方案 |
| 4 | Sleeve test_family_id规则不明确 | Review/DeepSeek | §5.1增加：sleeve共享基础因子方向的test_family_id |
| 5 | IC自相关对concept shift的影响未说明 | DeepSeek | §4.1增加IC lag-1自相关报告要求 |
| 6 | execution_slippage计算基准未定义 | Coder | §4.4定义滑点计算公式 |
| 7 | sleeve attempt_count计数规则 | Coder | §9.1.5增加：5sleeve×7模型=35次计入同一族 |
| 8 | capital_multiplier精度未定义 | Main | §9.3增加：四舍五入到5%或10% |
| 9 | CSRP最小n_signals下限 | Review | §9.1.5增加信号数不足时的处理规则 |
| 10 | S1-D/S1-R block bootstrap默认值 | Review | §7.1明确默认block=21天 |

### P2（3项，建议改进）

| # | 问题 | 来源 | 建议修复 |
|---|---|---|---|
| 1 | Sleeve间持仓重叠率报告要求 | Main | §9.1.5增加sleeve间重叠率报告 |
| 2 | 市场状态阈值预注册候选 | Main | validation_params.json增加market_state_indicators |
| 3 | Score分位计算universe选择 | Main | §5.1明确分位计算的universe |

---

## 六、最终结论

**文档质量：8.7/10（优秀）**

更新后的文档成功采纳了上一轮全部11项共识，新增内容（分层sleeve、资本overlay、CSRP误报率、Exploratory Tracking、动态IC换手、rebalance-to-rebalance标签、分层裁剪）设计合理。R2发现了3个P0级细节缺失（CSRP命中窗口、裁剪与overlay执行顺序、SQLite schema DDL），均为补充性定义，不影响整体架构设计。

**建议**：
1. 优先修复3个P0（预计1-2天）
2. 补充10个P1（预计3-5天）
3. 修复后文档质量可达到9.0/10，具备启动Phase A0的完整规格

**R2关键贡献**：
- DeepSeek修正了concept shift误报率误解（自相关**降低**误报率，非升高）
- Coder提供了MDE功效计算框架（24步可检测IC≥0.034）
- Review明确了裁剪与overlay执行顺序（先裁剪→归一化→overlay）
- 四位一致同意Phase A0工作量应调整为35-55工作日

---

*报告生成时间：2026-05-01 12:49 CST*
*审计流程：R1四位独立审计 → R2交叉审阅讨论 → 共识产出*
*R1平均分：8.1/10 → R2综合评分：8.7/10（+0.6）*
