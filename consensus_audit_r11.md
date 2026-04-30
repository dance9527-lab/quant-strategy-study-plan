# 量化策略研究计划审计报告（R11 终版）

**审计时间**：2026-05-01
**参与Agent**：Main、Review、DeepSeek（Coder超时3次未完成）
**讨论轮次**：2轮（达成共识）
**审计评分**：7.5/10

---

## 一、审计范围

基于仓库 D:\data\warehouse 实际数据，对两份策略文档进行全面审计：
- quant_strategy_plan.md（短总纲）
- quant_strategy_research_plan_detailed.md（执行规范）

## 二、三方共识（2轮讨论达成）

### 2.1 因子库完整性

**共识**：P1因子库基本完整，覆盖6大类。

| 因子类别 | 代表字段 | 数据来源 |
|---------|---------|---------|
| 动量 | ret_1d/5d/20d/60d/120d | market_daily_v1 |
| 波动率 | vol_20d/vol_60d/downside_vol_20d | market_daily_v1 |
| 换手率 | turnover_rate_pit/volume_ratio_pit | market_daily_v1 |
| 成交额 | adv_20d/adv_60d/adv_120d | market_daily_v1 |
| 估值 | total_mv_pit/circ_mv_pit | market_daily_v1 |
| 流通市值 | log_total_mv/log_circ_mv | market_daily_v1 |

**改进建议**：P2补充基本面质量类因子（ROE、毛利率、盈利稳定性），这类因子在A股市场IC稳定性不亚于动量类因子。

### 2.2 数据质量

**共识**：数据基础已具备，审计待完成。

| 维度 | 状态 | 说明 |
|------|------|------|
| 退市股票 | ✅ 已具备 | 319只退市股票（5.5%），security_master中is_delisted=True |
| PIT审计 | ⏳ 待完成 | 策略文档要求PIT审计，pit_feature_audit_market_daily_v1.json已生成但财务因子PIT待验证 |
| 幸存者偏差 | ⏳ 待验证 | 退市股票数据存在，但退市日期剔除和退市前收益率处理需验证 |

**改进建议**：S1启动前完成PIT审计和幸存者偏差验证。

### 2.3 GMSL（地缘宏观冲击层）

**共识**：框架设计完整，功能交付严重不足（4/6类数据源缺失），降级为S1报告项，不阻塞S1启动。

| GMSL数据源 | 状态 | 说明 |
|-----------|------|------|
| Cboe VIX/OVX/GVZ | ✅ 部分入仓 | 17,526行global_macro_daily |
| FRED（能源/利率/FX） | ❌ ReadTimeout | 配置了但抓取失败 |
| Brent/WTI/SC原油 | ❌ 未完成 | candidate_etl |
| USD/CNH/DXY | ❌ 未完成 | candidate_etl |
| UST利率 | ❌ 未完成 | candidate_etl |
| 地缘事件日历 | ❌ 空表 | 0行 |

**GMSL当前状态**：usage_allowed_stage: "stress_report_only"，禁止用于alpha_feature_selection、model_selection、threshold_tuning。

**改进建议**：S1期间增量补齐能源和汇率数据源（P1优先级），S2前完成全部6类数据源。

### 2.4 S1-D/S1-R定位

**共识**：S1-D/S1-R是日频风险/执行主线，非alpha keep主线。

- S1-D：Daily Risk/Execution，日度IC、alpha衰减和风险信号输出
- S1-R：Risk/Rebalancing，日度执行审计和持仓风险复核
- 两者共用同一套模型的不同频率输出，R使用更保守的模型版本

**注意**：Review Agent将S1-D误解为Development，实际文档定义为Daily Risk/Execution。

### 2.5 CSRP误报率估计

**共识方法**：用Walk-forward OOT窗口的信号命中率取倒数来估计。

具体做法：
1. 在滚动OOT窗口中逐期发出CSRP信号
2. 统计信号发出后固定窗口（如T+N）内实际发生的比例
3. 误报率 = 1 − 命中率
4. 用排列检验（随机shuffle信号时间戳）构建baseline误报率分布
5. 若p > 0.05则框架无统计效力，需重新审视信号逻辑

### 2.6 验证框架

**Review评分**：7.0/10

**改进建议**：
1. FDR方法：默认使用Benjamini-Hochberg (BH)校正，因子相关性高时报告Storey-q
2. Holdout访问日志：补充最小字段规范（timestamp、operator、purpose、data_range、result_summary、污染标记）
3. Burned holdout：shadow period长度=原holdout长度（252交易日）
4. HAC vs Bootstrap冲突：当HAC t-stat>=1.65但bootstrap p>=0.10时，结论为inconclusive

### 2.7 指数衰减加权

**Review评分**：6.5/10

**改进建议**：
1. 补充date-balanced权重假设的理论声明
2. 补充冻结模型版本管理规范（版本号命名、存储路径、回滚条件）
3. 补充21交易日/月转换因子的敏感性报告
4. 补充row-equal vs date-balanced择优判断标准

### 2.8 S1-M Walk-Forward

**Review评分**：7.5/10

**改进建议**：
1. 补充4/6年窗口的明确处置规则（"计入attempt_count"后的结论效力）
2. 补充OOT步数统计功效说明（24步对应约2010-2024年的14年窗口）
3. 补充purge边际效益递减分析

## 三、Main独立评估

### 3.1 S1-M/S1-D/S1-R分离设计
- 设计清晰，S1-M为正式alpha主线，S1-D/S1-R为风险/执行主线
- 三层换手率控制（重叠>=85% + 单票2% + 全局10%）设计完整

### 3.2 训练权重
- 指数衰减 + 等权对照 + row-equal/date-balanced双口径，设计完整
- 半衰期12个月（默认）、18个月（敏感性）、6/24月（诊断），档位合理

### 3.3 验证框架
- Walk-forward + purge + embargo + holdout + FDR校正，体系完备
- 24步OOT最低门槛、12个月holdout、purge>=max(label_horizon*3,40)

### 3.4 潜在问题
- 动态IC换手率公式上限15%（R10共识为10%），文档中pre_validation_effective_turnover_cap=min(0.10, formula)有矛盾
- GMSL阈值需从训练数据计算，当前为占位符

## 四、综合评分

| 审查点 | 评分 | 主要缺陷 |
|--------|------|---------|
| S1-M Walk-Forward | 7.5/10 | 4/6年窗口处置规则模糊；purge边际效益未披露 |
| 指数衰减加权 | 6.5/10 | date-balanced理论假设未声明；冻结模型版本管理缺失 |
| GMSL冲击层 | 4.5/10 | 4/6类数据源缺失；阈值未完成；降级为报告项 |
| S1-D/S1-R定位 | 5.5/10 | D/R分工需明确；日频OOT step间距未定义 |
| 验证框架 | 7.0/10 | FDR方法未指定；burned holdout规范缺失 |
| 因子库 | 8.0/10 | P1完整，P2补充盈利质量 |
| 数据质量 | 7.0/10 | 退市数据✓，PIT审计待完成 |
| CSRP | 7.5/10 | 框架完整，误报率需量化 |

**总体评分**：7.5/10

## 五、最优先改进项

| 优先级 | 事项 | 阻塞级别 |
|--------|------|---------|
| P0 | GMSL数据源增量补齐（能源、汇率优先） | 不阻塞S1，S1期间并行完成 |
| P1 | PIT审计和幸存者偏差验证 | 阻塞估值类因子keep |
| P1 | FDR方法明确（BH校正） | 阻塞候选因子>20时的keep |
| P1 | 冻结模型版本管理规范 | 阻塞正式实验登记 |
| P2 | 盈利质量因子（ROE/毛利率）入库 | 不阻塞S1-M |
| P2 | CSRP误报率量化 | 不阻塞S1启动 |
| P2 | date-balanced理论假设声明 | 不阻塞S1启动 |

## 六、结论

策略计划整体合理（7.5/10），S1-M主线可推进。经2轮讨论，三方在因子库完整性、数据质量状态、GMSL处理方案上达成共识。GMSL降级为S1报告项，不阻塞S1启动。S1启动前需完成PIT审计和FDR方法明确化。
