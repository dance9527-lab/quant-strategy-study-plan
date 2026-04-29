# A股量化策略研究计划 — 第四轮审计综合报告（2026-04-30）

> **审计对象**：`quant_strategy_plan.md`（总纲）+ `quant_strategy_research_plan_detailed.md`（执行规范）
> **审计重点**：仓库数据对接 + Concept Shift 应对 + 训练方案重构

---

## 一、Walk-forward 步数和起始日期

**问题**：文档只说"最少24步OOT"，没有说明walk-forward的实际起始日期和总步数。

**实际情况**：
- 训练窗口：5年（约1,260个交易日）
- 步进：21个交易日（约1个月）
- 从2010年（2005+5年训练）到2026年，实际约179个OOT步
- 24步是S1的最低通过门槛，不是walk-forward的总步数
- 最后12个月为holdout，不参与OOT计数

**改进**：在文档中明确walk-forward的起始日期和总步数计算方式。

---

## 二、valuation_daily 2026年缺口应对

**问题**：2026-01-05至2026-02-05约25个交易日无估值数据，落在holdout期内。

**影响**：最近OOT步的估值因子（市值、EP、BP、换手率）缺失。

**改进**：对估值因子使用forward-fill（估值因子变化缓慢，25天偏差极小），并在报告中标注。同时在敏感性检查中验证forward-fill对IC的影响。

---

## 三、universe_daily 构造审计

**问题**：universe_daily.in_factor_research_universe的构造逻辑未文档化。如果构造引入了未来信息，会系统性污染所有因子。

**改进**：作为Step 0a在S1启动前完成，预计2-4小时。审计内容：
- 筛选条件不包含未来信息
- ST、停牌、涨跌停状态使用T日或T-1日数据
- 历史证券过滤不引入幸存者偏差
- 审计通过后在文档中补充构造规则

---

## 四、P1因子字段可构建性验证

**验证结果**：9类P1因子全部可从现有仓库表构建。

| 因子类别 | 来源表 | 关键字段 | 状态 |
|---------|--------|---------|------|
| 市值 | valuation_daily | total_mv, circ_mv | ✅ |
| 估值 | valuation_daily | pe_ttm, pb, ps_ttm | ✅ |
| 流动性 | valuation_daily + prices | turnover_rate, amount | ✅ |
| 动量 | prices_daily_returns | return_adjusted_pit | ✅ |
| 反转 | prices_daily_returns | return_adjusted_pit | ✅ |
| 波动率 | prices_daily_returns | return_adjusted_pit | ✅ |
| 风险 | prices_daily_returns + benchmarks | beta, residual_vol | ✅（沪/北ST有PIT缺口） |
| 交易约束 | tradability_daily_enriched | listing_age, is_limit_up | ✅ |
| 行业 | industry_classification | pit_industry_intervals | ✅（依赖AkShare） |

---

## 五、block bootstrap 单位标注

**问题**：文档中block=21未标注单位。

**改进**：在validation_params.json中补充 `"block_unit": "trading_days"`。

---

## 六、trailing ADV 数据可用性

**验证**：tradability_daily_enriched.amount 完整覆盖1990-2026，可计算任意窗口的日均成交额。

**补充**：标记listing_age_trading_days < 20的新股样本为"ADV数据不足"，避免新股成交额异常值影响容量测试。

---

## 七、早期benchmark可靠性

**问题**：EQW_PROXY在1990年仅覆盖3-5只股票，早期benchmark不可靠。

**改进**：在benchmark审计中标注各时期的覆盖股票数。S1主窗口从2005年开始（此时覆盖5000+只），早期数据仅用于敏感性检查。

---

## 八、Concept Shift 应对方案

### 8.1 风险识别

A股在2023-2024年发生了至少3个结构性变化，构成 **Covariate Shift + Concept Shift 复合类型**：

| 变化 | 影响 | 冲击程度 |
|------|------|---------|
| 量化基金拥挤（规模从~5000亿增长到~1.5万亿） | 因子收益被压缩，尾部风险放大 | 高 |
| 2024年2月微盘股踩踏 | 暴露因子拥挤的系统性风险 | 高（最强信号） |
| 融券/转融通政策变化 | 做空机制改变影响因子收益 | 中 |
| 注册制全面实施（2023年） | IPO供给增加，壳价值逻辑改变 | 中 |
| 印花税减半（2023-08-28） | 交易成本结构变化 | 低 |

### 8.2 检测机制

**Chow断点检验**：
- 把因子IC序列切成两段（如2024年前 vs 2024年后）
- 用F统计量检验两段的均值/方差是否显著不同
- p<0.05 → 确认concept shift存在

**因子拥挤度监控**：
- 因子收益与换手率的相关性（拥挤时相关性突然升高）
- 因子收益左尾偏度（拥挤时左尾肥大）
- 因子收益自相关性（拥挤时收益序列更不稳定）
- 三个指标中任意两个同时异常 → 触发拥挤度告警

**OOT分3段评估**：
- 踩踏恢复期（2024-05 ~ 2024-08）
- 政策调整期（2024-09 ~ 2025-02）
- 新均衡期（2025-03 ~ 2025-04）
- 每段单独报告IC、Sharpe、MaxDD

---

## 九、训练方案重构：双轨制 + 动态 α 权重

### 9.1 问题诊断

当前walk-forward设计存在根本缺陷：**训练数据永远滞后于评估数据**。

- 每个OOT步使用该步之前5年数据训练
- 2024年量化踩踏、注册制改革、2025年政策调整、2026年美伊冲突——这些变化模型完全没有学到
- 指数衰减加权无法解决——因为所有训练数据都在变化发生之前
- 这是信息论层面的不可能：衰减权重无法引入窗口外的新信息

### 9.2 方案：双轨制

**Track A：长期趋势模型**
- 训练数据：全历史（2005-当前OOT步的前21天）
- 用途：捕捉长期稳定的因子关系（如价值效应、动量效应）
- 更新频率：每季度重新训练
- 权重：在无concept shift时为主（α=0.7）

**Track B：近期适应模型**
- 训练数据：最近6个月（约120个交易日）
- 用途：捕捉最新市场结构变化（如拥挤度变化、政策影响、地缘冲突）
- 更新频率：每个OOT步后在线微调（用该步的真实标签更新）
- 权重：在检测到concept shift时为主（1-α=0.7）

**组合方式**：
```
最终预测 = α × Track A 预测 + (1-α) × Track B 预测
```

**α动态调整**：
- 无concept shift：α=0.7（偏重长期趋势）
- 检测到concept shift：α=0.3（偏重近期适应）
- α的具体值在S1实验中通过Chow断点检验结果确定

### 9.3 Walk-forward框架调整

**原框架**：
```
Step N: 训练 [T-5years, T-21d] → 预测 [T, T+21d]
```

**新框架**：
```
Step N:
  Track A: 训练 [T-5years, T-21d] → 预测 A
  Track B: 训练 [T-6months, T-21d] → 预测 B
  α = f(concept_shift_detection)
  最终预测 = α × A + (1-α) × B
  → 评估 [T, T+21d]
  → 用真实标签更新 Track B
```

### 9.4 工程实现路线图

| Phase | 内容 | 耗时 |
|-------|------|------|
| Phase 1 | 基础双轨制（Track A + Track B，固定α=0.5） | 2-3天 |
| Phase 2 | 动态α权重（Chow检验 + regime检测 + 拥挤度监控） | 1-2天 |
| Phase 3 | 在线微调（Track B每步更新） | 1-2天 |
| Phase 4 | 验证与调参（对比双轨制 vs 单轨制） | 1-2天 |
| **总计** | | **5-7天** |

### 9.5 对S1实验的影响

| 影响项 | 说明 |
|--------|------|
| 计算成本 | 增加约2倍（两个模型） |
| 代码复杂度 | 中等增加（需要双训练+组合+检测） |
| 预期收益 | 在结构变化期（如2024年踩踏）回撤显著减小 |
| 风险 | Track B近期窗口样本量小（~120天），IC估计可能不稳定 |

---

## 十、S1 启动前置条件

| 项目 | 内容 | 耗时 | 阻塞级别 |
|------|------|------|---------|
| universe_daily构造审计 | 确认无未来信息 | 2-4h | P0（阻塞S1执行） |
| walk-forward起始日明确 | 文档补充 | 0.5h | P1（阻塞S1设计） |
| valuation缺口forward-fill方案 | 确认并标注 | 1h | P1 |
| 双轨制实现 | Track A + Track B | 5-7天 | P1（阻塞S1执行） |
| benchmarks目录清理 | 移除STATUS.md | 0.1h | P2 |
| block bootstrap单位标注 | validation_params补充 | 0.1h | P2 |

---

*日期：2026-04-30*
