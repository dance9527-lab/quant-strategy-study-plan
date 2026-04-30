# A股量化策略研究与落地总纲（2026-04-30 版）

> 本文件是后续策略研究的短总纲。详细执行规则以 `quant_strategy_research_plan_detailed.md` 为准。  
> Canonical 数据源：`D:\data\warehouse`。旧 `processed`、旧 qant cache、旧随机验证结果只能作为历史对照或反例，不作为策略有效性证据。
> 2026-04-30/2026-05-01 已吸收 `三方审计报告_20260430.md`、`consensus_audit_report_20260430.md`、`consensus_audit_round2.md`、`consensus_audit_r3.md`、`consensus_audit_r4.md`、`consensus_audit_r5.md`、`consensus_audit_r6.md`、`a_share_quant_strategy_plan_audit_report.md`、`consensus_audit_r10.md`、`a_share_quant_strategy_plan_updated_audit_report_20260430.md` 和 `consensus_audit_r11.md`：采纳其对执行可成交性、因子 PIT、walk-forward 固化、过拟合审计、S1 执行分层、IC 显著性修正、股票池审计、数据缺口处理、manifest 治理、三层 universe、拥挤容量、concept shift resilience、GMSL 外生冲击层和日频风险/执行治理的核心批评；R11 后第一阶段采用“月频 alpha 主线 + 日频风险/执行主线”的双主线治理，但只有 `S1-M` 是近期正式 alpha keep 主线，`S1-D/S1-R` 不进入近期主动 alpha 调仓或 official keep；R5 后仍废弃双轨、动态 alpha 和在线 Track B 作为近期执行路径，保留单轨 5 年 rolling、预注册权重候选、结构性稳健性审计、GMSL stress audit 与数据驱动告警；不采纳未经本地验证的收益承诺。

---

## 1. 当前证据状态

### 1.1 已经可用的数据底座

`D:\data\warehouse` 已完成重构、六轮修正、P1 数据前置和 R7 feature-label/source-status 更新。数据事实以 Git 项目中的 `warehouse_build_manifest.json`、`DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md`、`external_data_sources.csv` 和最新审计报告 hash 为准；策略文档不再把手工复制行数当作单一权威。最近一次检查：

- `D:\data\warehouse\audit_reports\leakage_check_report.json`
- `checked_at=2026-04-30 09:48:02`
- 21 类目录全部 PASS，新增覆盖 `features`、`labels`、`corporate_actions`、`global_macro_daily`、`gmsl_shock_state` 和 `geopolitical_event_calendar`
- `validation_params.json` 版本：`2026-05-01-r13-consensus-r11-hardening`
- `warehouse_build_manifest.json` 记录当前表行数、最大数据日期、source status 和必须披露缺口
- R7 `feature_label_panel_v1_manifest.json`、`pit_feature_audit_market_daily_v1.json`、`label_audit_forward_returns_v1.json`、`source_status_audit_r7.json` 均已生成

当前可直接用于日频股票研究的核心数据层：

| 表/产物 | 规模和范围 | 主要用途 |
|---|---:|---|
| `prices_daily_unadjusted` | 17,599,789 行，1990-12-19 至 2026-04-27 | 未复权成交价、成交额、涨跌停和容量判断 |
| `prices_daily_returns` | 17,599,789 行 | `return_adjusted_pit` 用于收益、动量、标签和绩效 |
| `valuation_daily` | 16,642,794 行，2000-01-04 至 2026-04-27 | 市值、股本、换手率可先做市场慢变量；PE/PB/PS/TTM 等仍需公告日 PIT 审计 |
| `tradability_daily_enriched` | 18,177,689 行 | 停牌推断、涨跌停约束、上市年龄、风险警示 |
| `universe_daily` | 18,177,689 行，默认因子 universe 16,586,748 行 | 保守 close-based entry universe；不能替代完整 research observable universe |
| `benchmarks` | 31,229 行 | 全 A 代理、沪深300、中证500、中证1000 |
| `reference_rates` | 55,964 行 | 国债收益率、Shibor、固定 fallback |
| `industry_classification` | PIT 行业区间 53,925 行 | PIT 行业中性和行业轮动候选 |
| `risk_warning_daily` | 8,973,264 行 | 风险警示过滤，深市历史较完整 |
| `trading_costs` | 23 行 | 印花税、佣金、过户费、规费、滑点研究假设 |
| `features/market_daily_v1` | 15,420,654 行，2005-2026 | market-only 日频特征面板；月选股和日选股正式训练仍需 walk-forward calendar/holdout log |
| `labels/forward_returns_v1` | 15,420,654 行，2005-2026 | 1/5/10/20 日 forward adjusted return、超额、rank/top decile 标签；支持 S1-M 月选股正式主线和 S1-D/S1-R 日频风险/执行验证；可交易 PnL 仍需 execution-aligned audit |
| `global_macro_daily` / `gmsl_shock_state` / `geopolitical_event_calendar` | Cboe 候选源已部分入仓，candidate_etl | `global_macro_daily` 17,526 行、`gmsl_shock_state` 9,176 行、`geopolitical_event_calendar` 0 行；当前只作 stress report/source registry/时区审计框架，不是可用 alpha 输入 |

这些表足够启动第一批 market-only 日频股票研究：市值、流动性、动量、反转、波动率、beta、行业中性、因子 IC、分层收益、保守组合回测、容量压力测试和 PIT 行业研究。R7 已解除 `features/labels` 占位阻塞；R11 后近期正式 alpha keep 主线先推进 `S1-M` 月选股，主看 20 日标签，默认固定月末或月初首个交易日调仓，21 个交易日滚动只作敏感性。`S1-D/S1-R` 升级为正式日频风险/执行主线，使用 1 日和 5 日标签做短期 IC、alpha 衰减、风险预警、订单失败、流动性、GMSL shock state 和离线执行审计；它不是近期日频 alpha keep 主线，未通过独立 walk-forward、成本、容量、分钟/集合竞价、limit_events 和 holdout 审计前不得主动调仓、提高净敞口或放宽风险。官方 S1 训练仍必须先固化 `walk_forward_calendar_v1`、`holdout_access_log.tsv`、测试族台账和实验登记，未完成前不得训练官方 S1 模型或产出 keep 结论。估值/基本面类结论必须单独过 PIT 和 total-return 审计。

### 1.2 必须披露的数据缺口

以下缺口不阻塞第一批日频研究，但必须写入每份回测报告：

- 完整交易所官方停复牌公告库仍缺失；`is_suspended_inferred=True` 是工程推断，不是官方公告。
- 沪/北历史 ST、摘帽、摘星带日期源仍缺；`risk_warning_daily` 主要来自深交所简称变更。
- `valuation_daily` 与收益表 key 不完全一致，2026-01-05 至 2026-02-05 存在估值覆盖缺口。
- `index_membership` 只是当前成分和最新月末权重快照，不能倒灌为历史 PIT 指数成分。
- `exchange_calendar` 是 SH/SZ/BJ 统一 A 股交易日历代理，不是三所官方历史差异日历。
- 成本模型中佣金、滑点、冲击成本和部分规费仍含研究假设。
- 公司行为、除权除息、分红送配尚未形成独立主表；`return_adjusted_pit` 当前只能声明为 adjusted-return proxy，不能宣称完整 total-return accounting 已闭环。
- `chip_daily`、`limit_events`、`prices_minute`、集合竞价/开盘成交明细、`option_minute`、`margin_trading`、`northbound`、`fund_flows`、`index_futures` 当前仍未形成可审计入仓主表；日频风险/执行主线可先用日频 L1 保守执行，精细开盘冲击、盘中成交优化或日频 alpha sleeve 必须等待分钟/集合竞价和 limit_events 数据入仓。
- GMSL 外生冲击数据当前只完成候选源局部入仓和审计框架；2026-04-30 对 FRED `fredgraph.csv` 配置源的实际抓取全部超时，Cboe VIX/OVX/GVZ 官方 CSV 抓取成功并形成 17,526 行 `global_macro_daily` 与 9,176 行 partial `gmsl_shock_state`。Brent/WTI、MOVE、DXY、USD/CNH、UST、全球股指/期货、商品和地缘事件窗口未完成 vendor/license/timezone/session cutoff/PIT/coverage 审计前，不得作为 alpha 特征、模型选择或阈值调参依据。

### 1.3 qant 实验结论的使用方式

此前 qant warehouse 实验只能作为边界证据：

- 2019-2026 chronological baseline：总收益 `-8.78%`，Sharpe `0.011`，最大回撤 `-60.65%`，相对中证1000总超额 `-51.54%`。
- random 8/2 曾显示总收益 `+531.43%`，Sharpe `0.988`，但已被 deep dive 判定为 label 泄漏和验证污染下的乐观结果。
- 证据：1,629,101 行训练窗口样本 `target_date_10d` 跨入 OOT 月，random 原始切分中 1,330,446 行进入 train。
- 2022-2024 修正实验中，所有 OOT purge 后版本绝对收益均为负。

因此，后续不得把 `outputs\warehouse_qant_2019_2026_random_val` 当作稳健基线，也不得用 naive random split 结果决定策略优先级。

### 1.4 三方审计后的独立裁决

`三方审计报告_20260430.md` 给早期计划的共识评分为 `6.0-6.5/10`。随后 `consensus_audit_report_20260430.md` 完成 Round 4 参数对齐，`consensus_audit_round2.md` 进一步细化执行层规则，`consensus_audit_r3.md` 补充因子正交化、股票池构造审计、A 股制度风险、Newey-West 显著性修正和 IC 衰减监控，`consensus_audit_r4.md` 聚焦仓库数据对接、估值缺口、真实 walk-forward 步数和 concept shift 替代训练框架，`consensus_audit_r5.md` 进一步复审双轨制可行性并将近期执行口径收敛为单轨指数衰减候选。`a_share_quant_strategy_plan_audit_report.md` 要求先修复数据 manifest、source registry、三层 universe、date-balanced 权重、拥挤容量、holdout 访问治理和测试族台账；`consensus_audit_r10.md` 进一步把 `S1-M` 固定为近期正式主线，把 `S1-D` 降级为探索/风控辅助通道，并补充成本、日换手、半衰期和训练窗口敏感性建议；`a_share_quant_strategy_plan_updated_audit_report_20260430.md` 将 `S1-D` 重构为正式日频风险/执行主线而非 alpha 主线，并新增 GMSL 外生冲击层、execution-aligned PnL 审计、日频 252/504 成熟日门槛和 computed purge 规则。`consensus_audit_r11.md` 进一步要求把 FDR、burned holdout、冻结模型版本、CSRP 误报率和 GMSL 降级写成可验收规则。当前执行口径以两份活跃策略文档和 `validation_params.json` 吸收后的表述为准。

| 审计意见 | 裁决 | 写入方式 |
|---|---|---|
| 涨跌停执行风险是 P0 | 采纳 | 任何组合回测必须报告涨停禁买、跌停禁卖、连续锁死和反转统计；纸面 alpha 若无法成交则不计为有效 alpha。 |
| 开盘冲击三段模型是 P0 | 部分采纳 | 日频阶段先用 open/amount/participation 做保守冲击和容量惩罚；集合竞价和分钟三段模型需等 `prices_minute`/竞价表入仓后升级。 |
| 因子 PIT 合规是 P0 | 采纳 | 市值/估值/行业/风险警示均需通过实验层 PIT audit；warehouse leakage PASS 不能替代因子层审计。 |
| walk-forward 参数固化 | 采纳并升级 | 官方证据默认 5 年训练；S1-M 默认固定月末/月初调仓，21 个交易日滚动为敏感性；`computed_purge_days=max(label_horizon*3,40)`，因此 20 日标签默认 purge 60 个交易日；embargo 10、至少 24 个 OOT step，并做分年度/市场状态分析。 |
| Deflated Sharpe 和 holdout 默认化 | 采纳 | 所有可 keep 的组合结果必须做过拟合审计和 holdout/稳定性复核。 |
| S1 完成标准量化 | 部分采纳并分层 | Newey-West HAC 调整后 `t>=1.65` 与 block bootstrap `p<0.10` 都必须报告；若只有一项通过，状态为 `inconclusive`，不能 keep。keep/晋级还必须通过 PIT/split/benchmark 审计、最后 12 个月 holdout、FDR、DSR/PBO、成本后超额和容量/成交约束。 |
| 分红送配从 P2 提到 P1.5 | 部分采纳 | 作为 Phase A 并行 ETL，不阻塞首轮价格/收益基线，但阻塞 total-return 和基本面增强结论。 |
| 风险开关 v1 | 采纳但去硬编码 | 放入 S1 通过后的强制风险模块；S3 前只使用 25/25/25/25 均匀权重占位，100/60/30/0 只能作为历史假设或挑战基线，不作为默认候选。 |
| 另类数据和筹码提前 | 部分采纳 | 北向、融资融券、限售解禁和筹码可提前做 source registration、ETL 和 candidate tracking；未通过 PIT/覆盖率/时点审计前不得进入官方 S1 keep。 |
| DeepSeek 收益路径和 alpha 区间 | 不作为承诺采纳 | 只能作为假设队列，所有收益区间必须由本地实验重新验证。 |
| 因子正交化流程 | 采纳但细化 | 单因子和等权基线保留原始因子；复合打分和线性模型前使用训练窗 ICIR 降序确定顺序，再做 Gram-Schmidt 正交化，并输出正交化前后相关矩阵。OOT 数据不得影响排序或处理参数。 |
| 季节性效应处理 | 采纳方案 B | 默认依靠 5 年训练窗口覆盖完整年度周期，不在 S1 默认加入月份哑变量；月份哑变量只能作为预注册 S3 或敏感性分析。 |
| Exploratory Tracking 冷却后处理 | 采纳 | 冷却期满后，如最近 6 个 OOT step 仍至少 4 步方向一致，可重新进入 S1 候选队列；不能直接进入 keep，且计入 `attempt_count`。 |
| `universe_daily` 构造审计 | 采纳 | 当前默认规则来自 `can_trade_close_based`、上市交易日龄和 PIT 风险警示，但 Step 1 必须补交股票池构造审计，确认未用当前股票列表或未来状态回填历史。 |
| A 股制度性风险对照 | 采纳为压力切片 | S1 报告增加涨跌停排除 IC 对比、注册制前后分段、流动性枯竭/拥挤压力日 IC 分析；这些切片用于诊断和风控，不得事后挑选窗口优化收益。 |
| IC 自相关和 bootstrap block | 采纳 | IC t-stat 默认使用 Newey-West HAC 调整；block bootstrap 默认 block=`max(label_horizon, rebalance_interval)`，并在 purge 敏感性中报告 10/21/40 日 block 对 p-value 的影响。 |
| IC 衰减半衰期 | 采纳为报告项 | S1 季度滚动 IC 报告增加半衰期，作为信号持久性风险提示，不作为 S1 hard gate。 |
| walk-forward 起始和总步数 | 采纳并精确化 | 24 步只是最低验收门槛，不是总步数；主窗口从 2005 开始，首个 OOT 约在 2010 年，实际步数按交易日和剔除最后 12 个月 holdout 后计算。 |
| 2026 估值缺口 forward-fill | 部分采纳 | 本地确认 2026-01-05 至 2026-02-05 缺 24 个交易日；只允许对慢变量估值特征做按股票有界 forward-fill，禁止用于标签、收益、成交价或绩效，并必须做有/无 forward-fill 敏感性。 |
| P1 因子可构建性 | 采纳但保留 PIT 缺口 | 9 类 P1 因子均可由现有表构建；沪/北 ST、全历史停复牌、估值缺口和 AkShare 行业源仍需在报告中披露。 |
| trailing ADV 和新股样本 | 采纳 | `tradability_daily_enriched.amount` 可用于 ADV；`listing_age_trading_days < 20` 标记为 ADV 不足，不得用新股异常成交额外推容量。 |
| 早期 benchmark 可靠性 | 采纳并校正事实 | benchmark 审计必须报告 `coverage_assets`；本地全 A 等权代理 1990 年仅 1-5 只，2005 年中位约 1315 只，2024 年中位约 5342 只。2005 前只做敏感性。 |
| R5/R11 Concept Shift 与日频风险执行 | 部分采纳并重构 | 采纳对双轨制、动态 alpha 和在线 Track B 的泄漏/过拟合风险批评，废弃这些近期执行路径；在 S1-M 正式主证据链内采纳单轨 5 年 rolling + 指数衰减 sample weight 作为预注册候选，并强制保留等权 5 年基线对照；`S1-D/S1-R` 是正式日频风险/执行主线，但不是 alpha keep 主线。不采纳“人工审查”，改为成熟 OOT IC/因子收益驱动的 yellow/red 状态机；任何告警不得改变当前 step 模型、alpha、阈值或特征选择。 |
| 数据 manifest 和 source registry | 采纳 | 新增 `warehouse_build_manifest.json`，并把 `DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md`、`external_data_sources.csv` 纳入 Git；策略实验必须引用 manifest/source registry hash。 |
| 三层 universe | 采纳 | 区分 `research_observable_universe`、`entry_eligible_universe` 和 `execution_accounting_universe`；不得在 IC 研究阶段因涨跌停直接删除风险样本。 |
| 估值字段分层 | 采纳 | 市值、流通市值、股本、换手率先作市场慢变量；PE/PB/PS/TTM 等财报派生字段需公告日和供应商计算时点 PIT 审计后才能 keep。 |
| 公司行为和 total return 审计提前 | 采纳但分层 | 提升为 P1 数据审计并行项，用于复权和绩效会计校验；不阻塞 market-only S1，但阻塞 total-return 与基本面增强结论。 |
| Date-balanced decay | 部分采纳 | 作为 5 年单轨内的必报对照，防止近期股票数扩张造成隐性双重加权；不得用 OOT/holdout 在 row-equal 与 date-balanced 间择优。 |
| CSRP 与拥挤容量 | 部分采纳 | 作为生产前结构性稳健性和容量审计层，不放宽 S1 hard gate，不恢复双轨/动态 alpha/在线 Track B。 |
| R11 双主线治理 | 采纳并纠偏 | 第一阶段采用 `S1-M` 月频 alpha 主线 + `S1-D/S1-R` 日频风险/执行主线；只有 `S1-M` 是近期正式 alpha keep 主线。`S1-D/S1-R` 可做短期 IC、alpha 衰减、风险预警、订单失败、流动性、GMSL shock state 和离线执行审计；主动调仓或 alpha sleeve 必须另经 walk-forward、holdout、成本、容量、分钟/集合竞价和 limit_events 审计。 |
| R10/R11 成本和日换手控制 | 部分采纳 | 往返 0.206% 写入机器参数，但披露佣金、规费、滑点、过户费为研究假设；S1-D/S1-R 三层换手控制作为离线/未来升级规则，10% 单边日换手为验证前硬上限；动态 IC 原公式只能作为 `raw_report_only_formula`，验证前只有 `min(0.10, raw_report_only_formula)` 可进入执行口径。 |
| R10 半衰期和训练窗口敏感性 | 部分采纳 | 12 月仍是默认半衰期，18 月为预注册敏感性，6/24 月为 R10 必报诊断，36 月为可选研究网格；5 年是唯一 keep 训练窗口，4/6 年只作诊断并计入 `attempt_count` 和试验族台账。好结果不得晋级 keep，坏结果不得改默认 5 年窗口，但可形成 robustness warning 并阻塞可部署叙事。 |
| R11 终版治理细化 | 采纳 | FDR 默认 Benjamini-Hochberg，因子相关性高时补 Storey-q；holdout access log 必须含 timestamp/operator/purpose/data_range/result_summary/pollution flag，burned holdout 后需 252 交易日 shadow/forward OOS；CSRP 误报率用 OOT 信号命中率和 shuffle baseline 估计。 |
| GMSL 外生宏观冲击层 | 采纳并分层 | 新增能源、汇率、全球波动率、全球股指/期货、利率、商品和地缘事件窗口的 candidate source registry 与 stress audit；S1 只报告，S1.5 作为生产前审计，S3 后才可作为 tighten-only 风控候选。未验证前不得增加风险、选模或调阈值。 |

---

## 2. 独立评估结论

当前最优先的工作不是追求新模型或高收益叙事，而是建立强基线、严格验证体系和可复现数据依据。Concept shift 不只是报告诊断；任何“可部署”叙事前必须通过结构性 regime 稳健性、date-balanced 权重对照和拥挤容量审计。

可立即推进的主线：

1. S1-M 月选股正式 alpha 主线：使用 20 日 forward excess/rank 标签，默认固定月末或月初首个交易日调仓，21 个交易日滚动只作敏感性，目标是低换手、多因子选股和月度持仓组合。
2. S1-D/S1-R 日频风险/执行主线：使用 1 日和 5 日 forward excess/rank 标签，T 日盘后输出短期 IC、风险预警、alpha 衰减监控、GMSL shock state、订单失败、流动性和离线执行审计；初期 report-only，未来 tighten-only 至少需要 504 个成熟日度决策日、24 个自然月桶和 8 个季度桶；默认不生成正式主动调仓目标仓位。
3. Market-only 因子库：市值、流动性、动量、反转、波动率、beta、PIT 行业中性，优先服务 S1-M 正式强基线。
4. 保守可交易回测：T+1、涨跌停、停牌、ST、上市年龄、交易成本、容量；日选股必须额外报告每日换手、订单失败和短持有期滚动持仓会计。
5. 市场状态、GMSL 和风险开关：指数趋势、市场宽度、波动率、涨跌停压力、能源/汇率/全球波动率/商品/地缘冲击。
6. PIT 行业中性和行业轮动：只使用 `pit_industry_intervals_akshare`，固定分类标准。
7. qant 小盘模型重审：只用 corrected baseline、OOT purge、blocked validation 和 embargo。
8. 数据审计并行项：公司行为/复权、三层 universe、walk-forward calendar、holdout access log、orders audit 和 source registry。
9. 外部数据候选 ETL：北向、融资融券、限售解禁、ETF flow、股指期货 basis/OI 以及 GMSL 外生冲击源只做可审计入仓准备和 stress/exploratory tracking，不直接作为官方 alpha 结论。

暂不作为第一批核心 alpha 的方向：

- 筹码增强：原始数据有价值，但尚未形成可审计 warehouse 主表，先做 P1/P1.5 并行 ETL、source registration 和 PIT 可用性审计，alpha 结论后置。
- 涨停事件：需先将事件表入仓，并严格区分盘后策略和盘中打板。
- 分钟策略：优先服务执行和滑点建模，不承诺普通 A 股 T+0 alpha。
- 期权策略：数据期短且缺 bid/ask、保证金、盘口深度和真实成交概率，先做研究储备。
- 深度时序、NLP、RL：必须在强基线和 walk-forward 体系稳定后作为增强模型进入。

---

## 3. 策略优先级

| 优先级 | 方向 | 进入条件 | 主要目标 | 当前裁决 |
|---|---|---|---|---|
| P0 | 数据 manifest/source registry | 任何正式实验登记前 | 统一行数、最大日期、source status 和 hash，避免文档版本漂移 | 立即固化 |
| P0 | walk-forward calendar 与 holdout access log | 任何正式 OOT/holdout 前 | 固化 S1-M 正式 alpha 主线和 S1-D/S1-R 日频风险/执行主线的 step、训练截止、label maturity、computed purge、holdout 访问和污染状态 | 立即固化 |
| P0 | 实验层 PIT/label/validation audit | 策略证据输出前必须通过 | 防止 warehouse PASS 后在实验层重新引入泄漏 | 立即固化 |
| P0 | 涨跌停和开盘执行门槛 | 任何组合回测前必须纳入 | 过滤纸面可得但真实不可成交的 alpha | 立即固化 |
| P0 | 三层 universe 审计 | S1 feature-label panel 前 | 分离研究观察、买入候选和执行会计，避免提前删除风险样本 | 立即固化 |
| P1 | S1-M 月选股正式强基线 | P0 audit 通过 | 验证 20 日持有期、固定月末/月初调仓、低换手多因子组合是否有成本后可交易超额；21 日滚动为敏感性 | 近期唯一正式 alpha keep 主线 |
| P1/P1.5 | S1-D/S1-R 日频风险/执行主线 | report-only 需 >=252 个成熟日度决策日；tighten-only 生产规则需 >=504 个成熟日、>=24 月桶、>=8 季度桶、换手控制、涨跌停/停牌影响评估、成本 1x/2x/3x 和 execution PnL 审计 | 验证 1/5 日短 horizon 信号能否用于短期因子研究、风险预警、alpha 衰减、GMSL shock state、订单失败、流动性和执行审计 | 不阻塞 S1-M；不得作为近期 alpha keep；主动调仓/alpha sleeve 后置 |
| P1 | 基础容量压力测试 | P0 成交规则可运行 | 用 trailing ADV、参与率、成交失败和市值分档量化真实成交边界 | 随 S1 同步输出 |
| P1 | Concept Shift + GMSL 诊断 | S1 walk-forward 同步运行 | 检测 2023-2025 内部结构变化、因子拥挤、分布漂移以及能源、汇率、全球波动率、利率、商品和地缘事件冲击是否破坏基线稳定性 | 不直接作为收益结论，不得用 OOT/holdout 调阈值 |
| P1 | 公司行为和 total-return 审计 | source/available_at 先行 | 复核 adjusted return、除权除息、分红送配和绩效会计 | 不阻塞 market-only S1，阻塞 total-return 声明 |
| P1 | 候选另类数据 ETL | source/available_at 先行 | 北向、融资融券、限售解禁只进入 candidate tracking | 不阻塞传统因子 S1 |
| P1.5 | CSRP + GMSL 结构性稳健性 | S1-M 正式主线可复现并通过主审计后；S1-D/S1-R 作为风险/执行主线参加验证 | 内部 regime map、GMSL shock-state、row-equal vs date-balanced、拥挤容量、forced deleveraging 和生产前风险审计 | 阻塞可部署叙事，不放宽 S1 hard gate |
| P1.5 | R5/R10 衰减权重稳健性 | S1-M 正式主线可复现并通过主审计后 | 对比等权 5 年、12 月半衰期 row-equal/date-balanced 指数衰减、18 月敏感性和 6/24 月 R10 诊断 | 数据驱动候选，不使用 OOT/holdout 择优 |
| P1.5 | 风险状态和仓位开关 v1 | S1 有正向证据后 | 降低回撤和波动 | S1 通过后强制验证 |
| P1.5 | 筹码 ETL 和 PIT 审计 | source/算法/available_at 先行 | 判断旧筹码数据能否进入 canonical warehouse | 不先作为 alpha 结论 |
| P2 | PIT 行业中性和行业轮动 | 固定分类标准并验证覆盖 | 约束暴露、研究行业动量和拥挤 | 基线后启动 |
| P2 | qant 小盘模型重审 | 必须 purge/embargo | 判断旧 132 特征是否有可救增量 | 作为反例驱动重审 |
| P2 | AkShare 低频外部数据 | schema、available_at、质量检查先行 | 财报、业绩预告、股东结构、质押、龙虎榜和大宗交易等增强 | 单独 ETL 阶段 |
| P3 | 筹码 alpha | `chip_daily` 入仓并验证时点 | A 股特色增量 alpha | ETL/PIT 审计通过后研究 |
| P3 | 涨停事件卫星 | `limit_events` 入仓并验证成交 | 小仓位事件策略 | ETL 后研究 |
| P3 | 分钟执行优化 | 5min/1min 分区表可用 | VWAP、滑点、冲击成本 | 服务执行，不先做 alpha |
| P4 | 期权波动率和保护性对冲 | 期权链、IV、Greeks、流动性模型完成 | 风险对冲和研究储备 | 后置 |
| P4 | 深度时序、NLP、RL | 线性/GBDT/Ranker 基线通过 | 增强预测或执行 | 严格准入 |

---

## 4. 模型路线

采用“模型输出分数，组合和风控决定仓位”的路线。

### 4.1 第一阶段模型

第一阶段采用“月频 alpha 主线 + 日频风险/执行主线”的双主线治理，但不是两条 alpha 主线：

| 主线 | 标签和预测 | 调仓和执行 | 默认重训 | 首批模型 |
|---|---|---|---|---|
| S1-M 月选股正式 alpha 主线 | 20 日 forward excess/rank 为主，10 日作稳健性 | 固定月末或月初首个交易日调仓，T 日盘后信号、T+1 执行；21 日滚动为敏感性 | 每 63 个交易日重训；非重训 step 使用冻结模型 | 单因子、等权打分、ICIR 加权、线性模型，非线性模型后置对照 |
| S1-D/S1-R 日频风险/执行主线 | 1 日和 5 日 forward excess/rank 为主，10/20 日只作稳健性或交叉验证 | 每日盘后输出 candidate_score、risk_signal、alert_state、GMSL shock_state 和执行审计；默认不主动调仓，离线模拟不进入 official keep | 每 63 个交易日重训；每日重训只作后置敏感性，不作为 S1-D/S1-R 默认 | 短期 IC、alpha 衰减、S1-M 持仓风险预警、订单失败、流动性、GMSL 和离线 orders/capacity/execution PnL 审计 |

模型顺序：

1. 单因子和等权打分。
2. ICIR 加权打分。
3. 训练窗 ICIR 排序后的 Gram-Schmidt 正交化复合打分。
4. Ridge、ElasticNet、线性横截面回归。
5. LightGBM、XGBoost。
6. LightGBM Ranker 或 LambdaRank，用于 Top-N 排序。

第一阶段目标是形成强基线，而不是调参追高收益。

Concept shift 处理采用“单轨强基线 + 预注册训练权重 + 数据驱动告警”：

- S1-M 使用单轨 5 年 rolling walk-forward 作为正式主证据框架；S1-D/S1-R 用同样隔离原则做正式风险/执行验证，不是同级 alpha keep 主线，也不是已废弃的 Track A/B、动态 alpha 或在线 Track B。
- 等权 5 年 rolling 是正式主线必须保留的对照基线，R5 指数衰减加权是单轨训练权重候选；S1-D/S1-R 侧输出日频风险/执行报告，未来 tighten-only 规则需独立验证。
- 指数衰减默认半衰期为 12 个月，主口径 `row_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))`；同时必须报告 `date_balanced_decay_weight = date_weight_t / n_assets_t` 对照，防止近年股票数扩张造成隐性双重加权。两种口径均在每个训练 step 内归一化到均值 1。
- 18 个月半衰期只作预注册敏感性；R10 的 6/24 个月作为必报诊断，36 个月只能作为可选研究网格，全部计入 `attempt_count`，不能用 OOT 或 holdout 择优。`date-balanced` 的理论角色是把每个交易日作为近似等权经济观察，防止上市股票数扩张让近年样本隐性超配；若 row-equal 有效但 date-balanced 失败且无法预注册解释，只能 `inconclusive` 或 discard。
- 模型默认每 63 个交易日重训一次；S1-M 默认固定月末/月初调仓/预测，21 日滚动为敏感性；S1-D/S1-R 默认每日重算分数、候选、风险告警和执行审计。两次重训之间使用最近一次符合 computed purge 规则的冻结模型版本。冻结模型必须登记 `model_version`、`train_end`、panel/label hash、参数 hash、代码提交、artifact hash、随机种子和回滚原因；命名建议为 `{track_id}_{model_family}_{train_end}_{validation_params_hash8}_{commit8}`。
- Concept shift 告警只使用已成熟 OOT IC、因子收益或预测前已可得的分布/拥挤度指标；连续 6 步成熟 IC < 0 触发 red quarantine，最近 6 步中至少 4 步为负触发 yellow。告警不改变当前 step 模型、alpha、阈值、early stopping、特征选择或仓位。
- R10 动态 IC 换手原公式只能作为 Phase 2 report-only 或 tighten-only 诊断；输入必须是至少滞后一 step 的成熟 trailing IC。验证前有效上限必须写成 `min(0.10, raw_report_only_formula)`，trailing IC 变好也不得 loosen 到 15%，只能报告或收紧。
- 结构性 regime map、GMSL shock-state、拥挤容量和风险响应只能作为预注册 CSRP/GMSL 生产前风险审计；风险开关必须在完整 walk-forward 中独立验证，不得由人工主观覆盖。
- 审计报告中的 3 年窗口、anchored post-2023 或多候选模型库不进入 S1/S1.5 近期路径；未来若单独研究，只能作为后置协议，并且每个 step 的选择必须只由训练窗内部 nested validation 决定。

### 4.2 第二阶段模型

在第一阶段通过后再评估：

- CatBoost：用于类别特征和稳健树模型对照。
- GARCH/HAR-RV：用于波动率和风险状态。
- 轻量 LSTM 或 1D-CNN：仅作为 P4 对照，不早于强基线和审计框架稳定后进入。
- TFT、N-HiTS、PatchTST、iTransformer、AutoGluon-TimeSeries、Darts、NeuralForecast：本地路线降级为研究储备或云端实验，不作为近期执行计划。

当前本机已可用：`lightgbm`、`xgboost`、`qlib`、`cvxpy`、`torch`。  
当前尚未安装或未验证：`arch`、`vectorbt`、`riskfolio-lib`、`PyPortfolioOpt`、`catboost`、`darts`、`neuralforecast`。这些依赖应在对应阶段进入前再安装和验证。

---

## 5. AkShare 外部数据裁决

本轮不做大规模外部数据接入。理由：

1. 当前 warehouse 已足够支撑第一批核心日频研究。
2. 外部数据必须先定义 schema、`available_at`、质量检查和回滚策略。
3. 贸然把半审计外部表混入 warehouse，会降低刚完成的数据底座可信度。

已确认 AkShare 1.18.57 可提供以下候选数据：

| 排名 | 数据源 | 价值 | 裁决 |
|---:|---|---|---|
| 1 | 公司行为、分红、送配 | total return、分红因子、复权校验 | P1 数据审计并行项，先用于 adjusted return sanity check |
| 2 | 融资融券明细 | 杠杆资金、拥挤度、融券可得性 | P1 candidate ETL，PIT 审计前不进 keep |
| 3 | 北向资金 | 资金流状态、风格切换 | P1 candidate ETL，PIT 审计前不进 keep |
| 4 | 限售解禁 | 注册制后供给压力 | P1 candidate ETL，公告日和实施日双时点 |
| 5 | ETF flows、市场宽度、涨跌停压力 | 被动/政策资金、风险开关、拥挤踩踏 | P1.5 CSRP 数据源 |
| 6 | 股指期货 basis/OI | 对冲成本、风格去杠杆、小盘拥挤 | P1.5 风险和容量数据源 |
| 7 | 财报、业绩预告、业绩快报 | 质量、成长、盈利修正 | P2，公告日 PIT 审计后再进基本面增强 |
| 8 | 股东户数、质押、龙虎榜、大宗交易 | 事件风险、供给压力和情绪 | P2/P3 接入 |
| 9 | 公告、新闻、NLP | 潜在高价值但稳定性低 | P4 研究 |

安全抓取原则：

- 全局 1 worker 起步。
- 慢接口串行，间隔 5-10 秒。
- 日频交易所接口整体不超过约 0.3 req/s。
- 失败指数退避重试 2-3 次。
- 所有中文参数用 UTF-8 脚本或 Unicode escape，避免 PowerShell 管道乱码。
- 所有披露类特征至少 T+1 生效，不得使用当前快照字段回填历史。

---


## 5.5 三方审计共识改进（2026-04-30）

三方独立审计（Main/Review/DeepSeek）达成以下共识，已写入执行规范：

### 验证框架参数调整（Round 5 + round2/r3/r4/r5/r6/R10/R11 执行细化）
- **embargo**：5日 → **10日**（基于A股因子自相关实证数据）
- **purge**：max(horizon,20) → **computed_purge_days=max(horizon*3,40)**；1/5/10 日标签为 40 个交易日，20 日标签为 60 个交易日。20 日标签的 40/60/80 日敏感性只能报告样本损失、label overlap proxy、HAC、bootstrap、holdout 和成本后 PnL delta；40 日对 20 日标签是 under-purge 诊断，不能支持 keep。
- **训练窗口**：**5年**（唯一 keep 通道）；R10/R11 的 4/6 年窗口只作诊断敏感性，计入 `attempt_count` 和试验族台账，不得用于改默认窗口、模型、阈值或半衰期。好结果不得晋级 keep，坏结果不得改默认 5 年窗口，但可形成 robustness warning 并阻塞可部署叙事。
- **训练权重**：R5 后新增单轨指数衰减候选；默认半衰期 12 个月，等权 5 年 rolling 必须作为对照，18 个月作为预注册敏感性；R10 的 6/24 个月为必报诊断，36 个月为可选研究网格，不得用 OOT/holdout 择优。
- **主线 cadence**：S1-M 月选股默认 20 日标签、固定月末/月初调仓，是近期唯一正式 alpha keep 主线；21 日滚动为敏感性。S1-D/S1-R 默认 1/5 日标签、每日盘后输出候选分数、风险预警、GMSL shock state 和执行审计，是正式日频风险/执行主线，但不进入近期主动 alpha 调仓或 official keep。
- **模型重训频率**：默认 63 个交易日重训；S1-M 默认固定月末/月初调仓/预测，21 日滚动为敏感性；S1-D/S1-R 每日重算分数、告警和执行审计但不默认每日重训；非重训 step 使用最近一次冻结模型。
- **OOT steps**：S1-M 最少**24步 + 分年度分析**。S1-D/S1-R 不能把 24 步写成充分日频证据；report-only 风险监控至少 252 个成熟日度决策日，tighten-only 生产规则至少 504 个成熟日、24 个自然月桶和 8 个季度桶，并同时报告日/周/月/季聚合。
- **walk-forward 起始和总步数**：主窗口从 2005-01-01 开始，首个 OOT 起点约为 2010 年；24 步只是最低验收门槛，实际总步数按交易日历和最后 12 个月 holdout 剔除后计算并披露。
- **S1门槛分层**：Hard Gate 包括审计通过、Newey-West HAC 调整后的 IC t-stat **≥1.65**、bootstrap p **<0.10**、最后 12 个月 holdout 至少满足方向一致、成本后超额 > 0、Sharpe > 0、MaxDD/CVaR 不显著差于 benchmark 或等权控制、单月利润贡献不超过 50%，且订单失败/成本/容量在预注册边界内；若 HAC 与 bootstrap 只有一项通过，状态为 `inconclusive` 而不是 keep。Soft Floor 包括换手、年度/市场状态稳定性和复杂模型相对简单基线增量；尾部风险必须报告并执行预注册 fatal check，未触发 fatal 才能进入 keep/晋级。
- **IC显著性**：IC t-stat 默认使用 **Newey-West HAC** 调整；未调整 t-stat 只能作为诊断值。
- **bootstrap方法**：**Block Bootstrap, block=max(label_horizon, rebalance_interval)**，月选股 20 日标签默认 block=21 日；S1-D/S1-R 默认 block=21 日，敏感性 5/10/21/40 日，晋级或生产 tighten-only 使用 10/21/40 中最保守结论，≥5000次重抽样。
- **多重检验**：候选因子>20个时，FDR 默认使用 Benjamini-Hochberg；若因子相关性高或有效假设数不清晰，必须补充 Storey-q 诊断，并记录相关性触发指标、有效假设数和 Storey-q。进入 keep/晋级时 FDR 为硬约束。
- **尾部风险**：S1报告模板必须记录MaxDD/VaR/CVaR/Sortino/Calmar，并对 max drawdown、CVaR、limit-lock CVaR、无法卖出的持仓暴露执行预注册 fatal check；S2 再深化尾部风险优化。
- **Exploratory Tracking机制**：方向一致性≥65%（OOT 24步中IC与对应样本内IC同号的步数/24，辅助：最近6步中4步一致） + 冷却期≥6个月（从首次进入Exploratory Tracking日起算） + 不入组合 + 完整记录；冷却期满后若最近6步仍至少4步方向一致，只能重新进入 S1 候选队列，不能直接 keep。
- **holdout定义**：最后12个月（约252个交易日）作为最终验收窗口，不参与调参、特征选择、early stopping、阈值选择、GMSL 阈值、shock window、行业规则、风控规则、日频 tighten-only 规则或仓位开关选择；12 vs 18个月只在S2预实验中验证。`holdout_access_log.tsv` 最小字段为 timestamp、operator、purpose、track_id、data_range、result_summary、decision_or_read_only、pollution_flag、followup_action；holdout 被用于策略选择后即 burned，只能作只读 benchmark，生产前需新增不少于 252 个交易日的 shadow/forward OOS。
- **Concept Shift + GMSL 分层**：S1-M 保留 5 年 rolling 单轨正式强基线；S1-D/S1-R 是日频风险/执行主线但不是 alpha keep；R5 后废弃双轨自适应、在线 Track B 和动态 alpha 近期路径；concept shift 与 GMSL 诊断随 S1 报告输出，并通过成熟 IC 驱动的 yellow/red 状态机和 shock-state report 进入 quarantine/revalidation，不放宽 hard gate。
- 若机器可读参数镜像与本节冲突，以本文档、`consensus_audit_report_20260430.md`、`consensus_audit_round2.md`、`consensus_audit_r3.md`、`consensus_audit_r4.md`、`consensus_audit_r5.md`、`consensus_audit_r10.md`、`a_share_quant_strategy_plan_updated_audit_report_20260430.md` 和 `consensus_audit_r11.md` 为准；执行前必须校验一致的参数 hash。

### 因子库扩展
- P1阶段同步做3-5个另类数据源的 source registration 和 candidate ETL（北向资金、融资融券、限售解禁优先）
- 筹码数据ETL从P3提前到P1/P1.5并行准备；PIT、覆盖率、算法解释和异常值审计通过前不进入官方 S1 keep

### 新增验证项
- 因子正交化流程：单因子、等权和原始 ICIR 先保留为基线；随后在 ICIR 复合和 Ridge/ElasticNet 前，用训练窗 ICIR 降序确定 Gram-Schmidt 顺序，并输出正交化前后相关矩阵。
- 多重检验校正（FDR，因子>20个时）
- 尾部风险指标（VaR 95%、CVaR 99%）
- regime断裂检测和保护：S1-M 使用月度/20 日成熟 IC 告警，S1-D 使用日度成熟 IC 序列并同时按周/月汇总，先只作为报告/yellow 标记/暂停跟踪候选；减仓或停用必须经 walk-forward 验证。
- `universe_daily` 构造逻辑审计：确认默认股票池不使用未来股票列表、未来 ST、未来停牌或未来涨跌停状态筛历史。
- 季节性效应处理：默认依靠 5 年训练窗口覆盖完整年度周期；月份哑变量仅作预注册敏感性或 S3 研究。
- A 股制度性风险对照：涨跌停排除 IC、注册制阶段、流动性枯竭/拥挤压力日。
- 因子 IC 衰减半衰期：写入 S1 季度滚动 IC 报告，报告风险等级但不作为 hard gate。
- 估值缺口处理：2026-01-05 至 2026-02-05 估值缺口只允许慢变量特征有界 forward-fill，并做缺口 mask 和敏感性报告。
- concept shift 诊断：预注册 2023-2025 结构变化切片、滚动成熟 IC/因子收益、分布漂移和拥挤度监控；Chow/ADWIN/Page-Hinkley/BOCPD 只可作为成熟序列上的报告项，不作为 keep gate 或自动切换依据；诊断不放宽 S1 hard gate。
- GMSL 外生冲击诊断：预注册能源、汇率、全球波动率、利率、商品和地缘事件 shock state；所有海外数据必须先过 vendor/license/timezone/session cutoff/PIT/coverage 审计。S1 只报告，S1.5 生产前审计，S3 后才允许作为 tighten-only 风控候选；未验证前不得提高净敞口、杠杆、单票权重、行业集中或日换手。

### 深度模型降级
- 放弃PatchTST/TFT，改用轻量LSTM或1D-CNN
- 或定位为云端实验，本地只做推理

### 容量测试前移
- S1阶段增加最简容量过滤（日均成交额>1000万）
- S1同步报告 trailing ADV、参与率、成交失败率、涨跌停压力和市值分档 IC；S2做精细容量分析（分档滑点/冲击/参与率）

### S1 启动前补充验证
- purge 敏感性：在相同因子和窗口下对比 40/60/80 个交易日 purge；该实验不阻塞面板构建，但阻塞正式 keep/晋级结论。
- R5 S1 前置条件：
  - P0：`universe_daily` 构造审计、S1-M/S1-D walk-forward 日历固化、每步训练截止日满足 purge/embargo。
  - P1：valuation 缺口三口径敏感性、benchmark 覆盖审计、ADV 新股不足标记、validation 参数 hash。
  - P1：concept shift 诊断和成熟 IC yellow/red 状态机预注册，随 S1 输出但不放宽 hard gate。
  - 非阻塞 S1：ADWIN/BOCPD 等额外变点诊断、6/24/36 月半衰期研究网格；均不得进入 keep 决策。
- 24 步仅是最低验证规模和快速 smoke；完整 R5 主证据按交易日历生成全量 OOT step，需单独估算耗时。

详细共识报告见：consensus_audit_report_20260430.md
执行层补充审计见：consensus_audit_round2.md
第三轮执行深化见：consensus_audit_r3.md
第四轮数据和 concept shift 审计见：consensus_audit_r4.md
第五轮 concept shift 训练方案复审见：consensus_audit_r5.md

## 6. 禁止事项

后续所有实验禁止：

1. 使用全样本最新前复权价格作为历史训练特征或决策输入。
2. 使用未来股票列表、未来行业、未来 ST、未来停牌状态筛选历史样本。
3. 使用 naive random 8/2 作为最终验证证据。
4. 用 OOT 月内 future label 参与训练、验证或 early stopping。
5. 用当前指数成分或权重快照构造历史指数增强股票池。
6. 把缺 bar 推断停牌当作交易所官方停牌公告。
7. 把当前行业快照当作 PIT 历史行业。
8. 只报告毛收益，不报告成本、换手、成交失败和容量。
9. 在没有基线对照的情况下引入深度学习、NLP 或 RL。
10. 在文档中承诺未经实证的高收益、Sharpe 或胜率。
11. 把双轨 Track A/B、动态 alpha 或在线 Track B 作为 S1/S1.5 近期执行路径。
12. 让人工主观判断决定模型切换、参数选择、候选 keep 或告警处置；所有处置必须来自预注册数据规则。
13. 把 stress slice、2024-02、post-2023 或全面注册制后样本作为选模窗口；这些只能作为预注册诊断和风险审计。
14. 用行级样本数扩张造成的近期股票数偏差冒充 concept shift 适配。
15. 只用自有参与率判断拥挤容量，不报告因子重叠、左尾、跌停未成交和市场成交额占比。
16. 未建立 holdout access log 就反复查看 holdout 后继续声称其仍是未污染最终验收。
17. 绕过 R7 可审计 `features/labels` 面板、manifest/hash、PIT audit、label audit、walk-forward calendar 或 holdout log，直接训练官方 S1 模型。
18. 用临时实验缓存绕过 feature-label 入仓审计、PIT audit、label audit 或 manifest/hash 登记。
19. 把 anchored post-2023 keep、same-step label feedback 或当前 OOT/holdout/stress slice 反馈作为模型选择、阈值选择或参数选择依据。

---

## 7. 近期行动路线

### Phase A0：S1-M alpha 主线与 S1-D/S1-R 风险执行主线共享审计和日历固化

目标：为 S1-M 月选股正式 alpha 主线建立可复现、可审计的启动底座，并为 S1-D/S1-R 日频风险/执行主线固化独立登记、日历、GMSL shock-state、execution label 和离线审计接口。

产出：

- Round 5 固化的 walk-forward 参数、指数衰减权重参数和本地参数 hash。
- `warehouse_build_manifest.json`、`external_data_sources.csv`、`validation_params.json`、`track_registry_v1` 和 `walk_forward_calendar_v1` 的 hash。
- 实验层 PIT audit、split label audit、benchmark audit。
- 三层 universe 构造审计报告。
- `holdout_access_log.tsv`、测试族台账字段、`track_id`、`label_id`、`rebalance_interval`、`holding_period`、`execution_rule_id` 和 `panel_hash`。
- 2026 估值缺口 mask、forward-fill 敏感性和受影响样本报告。
- benchmark 覆盖股票数审计，2005 前 benchmark 仅作敏感性说明。
- 涨跌停禁买/跌停禁卖、连续锁死、开盘冲击和成交失败报告。
- 因子覆盖率和质量报告。
- S1-M 与 S1-D/S1-R 的日历、标签、执行口径和容量报告分离；S1-D/S1-R 结果不得用于选择 S1-M 模型、阈值、半衰期或窗口，也不得在未验证前触发主动调仓、提高净敞口、放宽日换手或增加行业集中。
- GMSL candidate source registry、timezone/session cutoff audit、source fetch status、候选表初始化和局部源抓取；在外部源通过 PIT/coverage 审计前只能写成 `candidate_etl`。

### Phase A-M：S1-M 月选股强基线

目标：验证 20 日标签、约月度调仓和低换手多因子组合是否在成本、容量和成交约束后仍有超额。

产出：

- 20 日 forward excess/rank 标签的单因子 IC、RankIC、ICIR。
- 固定月末/月初调仓的等权、ICIR、正交化复合因子、线性、LightGBM/Ranker 对照；21 个交易日滚动作为敏感性。
- Newey-West HAC IC t-stat、block bootstrap 和 10/21/40 日 block 敏感性。
- 固定月度调仓的成交失败、T+1 单日执行、1/3/5 日分批执行必报、月度换手和容量上限。
- 分层收益、制度性风险切片、IC 衰减半衰期和 concept shift 报告。

### Phase A-R：S1-D/S1-R 日频风险/执行主线

目标：验证 1/5 日标签和短 horizon 信号是否能作为短期因子研究、S1-M 持仓风险预警、alpha 衰减监控、GMSL shock-state、订单失败、流动性和离线执行审计输入；近期不作为主动 alpha 调仓或 official keep 主线。

产出：

- 1 日和 5 日 forward excess/rank 标签的单因子 IC、RankIC、ICIR；10/20 日只作稳健性或与月选股交叉对照。
- 每日盘后 `S1-D_daily_risk_execution_offline` 候选清单：`as_of_date`、`trade_date`、`asset_id`、`score`、`rank`、`horizon`、`risk_signal`、`alert_state`、`gmsl_shock_state`、`model_version`、`feature_cutoff`、`label_cutoff`、`no_trade_reason`；离线权重字段只能命名为 `offline_sim_target_weight`，不得接入生产订单接口。
- 离线滚动组合模拟的等权、ICIR、正交化复合因子和线性模型基线；非线性模型只作后续对照，模拟结果不得进入 official keep 或收益承诺。
- `daily_orders_audit`：涨停买入失败、跌停卖出失败、停牌延迟、100 股整数手、T+1、未成交继续暴露、解锁后 1/3/5 日收益；独立 `limit_events` 未入仓前使用 `tradability_daily_enriched` / `universe_daily` close-based 代理字段。
- `daily_turnover_capacity_report`：日换手、成本拖累、ADV 参与率、成交失败率、容量上限、limit-lock CVaR，以及成本 1x/2x/3x 敏感性；三层换手控制默认重叠率 >=85%、单票日变动 <=2%、单边日换手 <=10%。
- 日度成熟 IC 状态机、按日/周/月/季汇总的 concept shift + GMSL 报告、与 S1-M 持仓重叠度和冲突交易统计；report-only 至少 252 个成熟日，tighten-only 至少 504 个成熟日、24 月桶和 8 季度桶。

### Phase B：风险状态和组合约束

目标：减少回撤，约束风格和行业暴露。

产出：

- 市场状态变量库。
- 仓位开关对照实验。
- R5/CSRP/GMSL 稳健性：等权 5 年、12 月半衰期 row-equal/date-balanced 指数衰减、18 月半衰期敏感性、结构性 regime map、GMSL shock-state、拥挤容量、forced deleveraging 和成熟 IC 状态机对照；必须同口径击败等权控制且通过全部审计才可晋级。
- 风险开关 v1：S3 前使用 25/25/25/25 均匀权重占位；S3 验证后替换为数据驱动仓位比例。100/60/30/0 只保留为可选历史假设或挑战基线，不作为默认事实。
- 熔断规则：组合回撤、市场宽度崩塌、跌停压力和流动性枯竭触发降仓。
- 行业、市值、beta、换手、容量约束组合。

### Phase C：外部低频数据 ETL

目标：补齐基本面、公司行为、执行增强、风险事件和 GMSL 完整外生冲击覆盖。Phase C 是后续数据收集、整理、清洗规划；R12 复核只更新文档和 registry，不执行新增抓取或入仓。

优先顺序：

1. P0 governance：`track_registry_v1`、`walk_forward_calendar_v1`、`holdout_access_log.tsv`、`test_family_registry`、冻结模型 registry 和 `experiment_ledger`，用于锁定 S1-M / S1-D/S1-R 的验证边界、computed purge、holdout 污染状态、model_version、attempt count、FDR 方法和统计冲突状态。
2. P0/P1 execution audit：`execution_label_audit`、`execution_audit/orders_audit` 和 `daily_turnover_capacity_report`，先用日频未复权 OHLCV、`tradability_daily_enriched` 和成本表形成 T+1 open/proxy、3/5 日分批、未成交 carryover 和解锁反转审计。
3. 公司行为和分红送配，用于 adjusted return / total-return sanity check；完整官方或授权主表未闭环前，不声明完整 total-return accounting。
4. `limit_events`、分钟/集合竞价/开盘成交明细，用于精细执行、开盘三段模型和未来日频 alpha sleeve。
5. 融资融券、北向、限售解禁、ETF flows、市场宽度/涨跌停压力、股指期货 basis/OI。
6. GMSL 外生冲击候选：Brent/WTI/SC、黄金/铜/工业金属、USD/CNH/DXY、VIX/MOVE、UST、全球股指/期货和地缘事件日历；未完成时区/session cutoff/PIT/coverage 审计前只作 stress report。
7. 财报、业绩预告、业绩快报，优先登记 ROE、毛利率、盈利稳定性和盈利修正类质量因子；公告日/可得日 PIT 未审计前只做 P2 解释力候选。
8. 股东户数、质押、龙虎榜、大宗交易。

### Phase D：特色 alpha 和高级模型

目标：在强基线基础上验证增量。

候选：

- 筹码增强。
- 涨停事件卫星。
- 分钟执行优化。
- 期权波动率和保护性对冲。
- 深度时序、NLP、RL。

---

## 8. 活跃文档

后续只维护 Git 项目中的两份活跃策略文档：

1. `D:\quantum_a0\quant-strategy-study-plan\quant_strategy_plan.md`：短总纲，记录方向、证据、优先级和禁用结论。
2. `D:\quantum_a0\quant-strategy-study-plan\quant_strategy_research_plan_detailed.md`：详细执行规范，记录数据口径、标签、验证、回测、台账、验收和 review 清单。

数据依据文档也必须随 Git 同步维护：

1. `DATA_USAGE_GUIDE.md`：数据表使用口径。
2. `WAREHOUSE_README.md`：warehouse 状态说明。
3. `external_data_sources.csv`：外部源登记和 source gap。
4. `warehouse_build_manifest.json`：当前数据事实、source status 和审计报告 hash。
5. `validation_params.json`：机器可读验证参数镜像。

`D:\data\strategy\` 下的旧副本只作为迁移前来源；后续若需要保留副本，必须从 Git 项目同步回写，不得双向分叉维护。

`量化时间序列模型调研和选择.md` 与 `量化策略设计调研与建议.md` 作为参考材料，不作为直接执行规范。






