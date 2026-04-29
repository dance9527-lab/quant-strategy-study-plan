# A股量化策略研究计划 — 第四轮审计改进报告（2026-04-30）

> **审计对象**：`quant_strategy_plan.md`（总纲）+ `quant_strategy_research_plan_detailed.md`（执行规范）
> **审计重点**：仓库数据与策略文档的具体对接验证

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

## 八、S1 启动前置条件

| 项目 | 内容 | 耗时 | 阻塞级别 |
|------|------|------|---------|
| universe_daily构造审计 | 确认无未来信息 | 2-4h | P0（阻塞S1执行） |
| walk-forward起始日明确 | 文档补充 | 0.5h | P1（阻塞S1设计） |
| valuation缺口forward-fill方案 | 确认并标注 | 1h | P1 |
| benchmarks目录清理 | 移除STATUS.md | 0.1h | P2 |
| block bootstrap单位标注 | validation_params补充 | 0.1h | P2 |

**总计**：约4-6小时，不显著延迟S1启动。

---

*日期：2026-04-30*
