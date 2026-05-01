# A股量化策略研究与落地总纲（执行版）

> 本文件是后续策略研究的短总纲。详细执行规则以 `quant_strategy_research_plan_detailed.md` 为准。本文只保留当前执行依据，不记录协议形成历史。
> Canonical 数据源：`D:\data\warehouse`。旧 `processed`、旧 qant cache、旧随机验证结果只能作为历史对照或反例，不作为策略有效性证据。

---

## 1. 当前证据状态

### 1.1 已经可用的数据底座

`D:\data\warehouse` 已形成 canonical 数据底座、P1 数据前置产物、feature-label 面板和 source-status 审计产物。数据事实以 Git 项目中的 `warehouse_build_manifest.json`、`DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md`、`external_data_sources.csv` 和关键 audit hash 为准；策略文档不再把静态摘录行数当作单一权威。最近一次检查：

- `D:\data\warehouse\audit_reports\leakage_check_report.json`
- `checked_at=2026-04-30 09:48:02`
- 21 类目录全部 PASS，新增覆盖 `features`、`labels`、`corporate_actions`、`global_macro_daily`、`gmsl_shock_state` 和 `geopolitical_event_calendar`
- `validation_params.json` 版本：`2026-05-01-capital-overlay-segmented-sleeves`
- `warehouse_build_manifest.json` 记录当前表行数、最大数据日期、source status 和必须披露缺口
- `feature_label_panel_v1_manifest.json`、`pit_feature_audit_market_daily_v1.json`、`label_audit_forward_returns_v1.json`、`source_status_audit_r7.json` 均已生成

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

这些表足够启动第一批 market-only 日频股票研究：市值、流动性、动量、反转、波动率、beta、行业中性、因子 IC、分层收益、保守组合回测、容量压力测试和 PIT 行业研究。`features/labels` 占位阻塞已解除；近期正式 alpha keep 主线先推进 `S1-M` 月选股，主看 20 日标签，默认固定月末或月初首个交易日调仓，21 个交易日滚动只作敏感性。`S1-D/S1-R` 是正式日频风险/执行主线，使用 1 日和 5 日标签做短期 IC、alpha 衰减、风险预警、订单失败、流动性、GMSL shock state 和离线执行审计；它不是近期日频 alpha keep 主线，未通过独立 walk-forward、成本、容量、分钟/集合竞价、limit_events 和 holdout 审计前不得主动调仓、提高净敞口或放宽风险。官方 S1 训练仍必须先固化 `walk_forward_calendar_v1`、`holdout_access_log.tsv`、测试族台账和实验登记，未完成前不得训练官方 S1 模型或产出 keep 结论。估值/基本面类结论必须单独过 PIT 和 total-return 审计。

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

### 1.4 当前执行规则

当前执行口径以本总纲、`quant_strategy_research_plan_detailed.md` 和 `validation_params.json` 为准。

| 领域 | 当前规则 | 执行边界 |
|---|---|---|
| 执行可成交性 | 任何组合回测必须报告涨停禁买、跌停禁卖、连续锁死、解锁后反转和订单失败。 | 纸面 alpha 若无法成交，不计为有效 alpha。 |
| 开盘冲击和容量 | 日频阶段先用 open、amount、participation 做保守冲击和容量惩罚。 | 集合竞价和分钟三段模型须等 `prices_minute` 或竞价表入仓后升级。 |
| 因子 PIT | 市值、估值、行业、风险警示和外部源均需通过实验层 PIT audit。 | warehouse leakage PASS 不能替代因子层审计。 |
| walk-forward | 官方 alpha keep 证据默认 5 年训练；S1-M 固定月末或月初首个交易日调仓，21 个交易日滚动只作敏感性；`computed_purge_days=max(label_horizon*3,40)`。 | 20 日标签默认 purge 60 个交易日；S1-D/S1-R 的 1 日风险/执行报告用 20 个交易日 purge 并报告 10/20/40 敏感性，但不得单独支持 alpha keep；24 个 OOT step 只是 smoke/minimum，完整 S1-M OOT 步数按 calendar 计算并披露。 |
| keep 统计门槛 | Newey-West HAC 调整后 `t>=1.65` 与 block bootstrap `p<0.10` 必须同时满足；只有一项通过时状态为 `inconclusive`。 | keep/晋级还必须通过 PIT/split/benchmark 审计、最后 12 个月 holdout、FDR、DSR/PBO、成本后超额和容量/成交约束。 |
| holdout | 最后 12 个月约 252 个交易日只作最终验收。 | 一旦用于策略选择即 burned；生产前需要新增不少于 252 个交易日 shadow/forward OOS。 |
| 数据 manifest 和 source registry | 策略实验必须引用 manifest/source registry hash。 | `DATA_USAGE_GUIDE.md`、`WAREHOUSE_README.md`、`external_data_sources.csv` 和 `warehouse_build_manifest.json` 是 Git 侧数据依据镜像。 |
| 三层 universe | 分离 `research_observable_universe`、`entry_eligible_universe` 和 `execution_accounting_universe`。 | IC 研究不得因涨跌停、停牌或成交失败静默删除风险样本。 |
| 估值和基本面 | 市值、流通市值、股本、换手率先作市场慢变量。 | PE/PB/PS/TTM、ROE、毛利率、盈利稳定性等需公告日和供应商计算时点 PIT 审计后才能 keep。 |
| 公司行为和 total return | 公司行为主表和 total-return audit 为 P1 并行项。 | 不阻塞 market-only S1，但阻塞完整 total-return accounting 和基本面增强结论。 |
| 训练权重 | 等权 5 年 rolling 是控制基线；12 月半衰期 row-equal/date-balanced 指数衰减为预注册候选；18 月为预注册敏感性；6/24/36 月只作诊断或研究网格。 | 不得用 OOT 或 holdout 在半衰期、row-equal/date-balanced 或训练窗口间择优。 |
| Concept shift 和 CSRP | 成熟 OOT IC、因子收益、分布漂移和拥挤度只作为数据驱动告警和生产前稳健性审计。 | 告警不得改变当前 step 模型、alpha、阈值、early stopping、特征选择或仓位。 |
| S1-D/S1-R | 日频风险/执行主线，使用 1/5 日标签输出短期 IC、alpha 衰减、风险预警、订单失败、流动性、GMSL shock state 和离线执行审计。 | 不是近期 alpha keep 主线；主动调仓或 alpha sleeve 必须另经 walk-forward、holdout、成本、容量、分钟/集合竞价和 limit_events 审计。 |
| 日换手控制 | 三层换手控制作为离线和未来升级规则；10% 单边日换手为验证前硬上限。 | 分层裁剪优先级为总换手上限 > 行业上限 > 个股上限；每层等比例缩减并重新归一化。动态 IC 原公式只能作为 `raw_report_only_formula`；验证前只有 `min(0.10, raw_report_only_formula)` 可进入执行口径。 |
| GMSL | 能源、汇率、全球波动率、全球股指/期货、利率、商品和地缘事件窗口只作 candidate source registry 与 stress audit。 | S1 只报告，S1.5 作生产前审计，S3 后才可作为 tighten-only 风控候选；未验证前不得增加风险、选模或调阈值。 |

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

| 优先级 | 方向 | 进入条件 | 主要目标 | 当前定位 |
|---|---|---|---|---|
| P0 | 数据 manifest/source registry | 任何正式实验登记前 | 统一行数、最大日期、source status 和 hash，避免文档版本漂移 | 立即固化 |
| P0 | walk-forward calendar 与 holdout access log | 任何正式 OOT/holdout 前 | 固化 S1-M 正式 alpha 主线和 S1-D/S1-R 日频风险/执行主线的 step、训练截止、label maturity、computed purge、holdout 访问和污染状态 | 立即固化 |
| P0 | 实验层 PIT/label/validation audit | 策略证据输出前必须通过 | 防止 warehouse PASS 后在实验层重新引入泄漏 | 立即固化 |
| P0 | 涨跌停和开盘执行门槛 | 任何组合回测前必须纳入 | 过滤纸面可得但真实不可成交的 alpha | 立即固化 |
| P0 | 三层 universe 审计 | S1 feature-label panel 前 | 分离研究观察、买入候选和执行会计，避免提前删除风险样本 | 立即固化 |
| P1 | S1-M 月选股正式强基线 | P0 audit 通过 | 验证 20 日持有期、固定月末/月初调仓、低换手多因子组合是否有成本后可交易超额；21 日滚动为敏感性 | 近期唯一正式 alpha keep 主线 |
| P1/P1.5 | S1-D/S1-R 日频风险/执行主线 | report-only 需 >=252 个成熟日度决策日；tighten-only 生产规则需 >=504 个成熟日、>=24 月桶、>=8 季度桶、换手控制、涨跌停/停牌影响评估、成本 1x/2x/3x 和 execution PnL 审计 | 验证 1/5 日短 horizon 信号能否用于短期因子研究、风险预警、alpha 衰减、GMSL shock state、订单失败、流动性和执行审计 | 不阻塞 S1-M；不得作为近期 alpha keep；主动调仓/alpha sleeve 后置 |
| P1 | 基础容量压力测试 | P0 成交规则可运行 | 用 trailing ADV、参与率、成交失败和市值分档量化真实成交边界 | 随 S1 同步输出 |
| P1 | 小资金可行性档 | P0 成交规则可运行 | 增加 10 万、20 万、50 万、100 万初始资金档，检查 100 股整数手、最低佣金/最小成交额、现金闲置和小账户成本拖累 | 只解释小资金实操，不替代 1000 万、5000 万、1 亿容量 |
| P1 | Concept Shift + GMSL 诊断 | S1 walk-forward 同步运行 | 检测 2023-2025 内部结构变化、因子拥挤、分布漂移以及能源、汇率、全球波动率、利率、商品和地缘事件冲击是否破坏基线稳定性 | 不直接作为收益结论，不得用 OOT/holdout 调阈值 |
| P1 | 公司行为和 total-return 审计 | source/available_at 先行 | 复核 adjusted return、除权除息、分红送配和绩效会计 | 不阻塞 market-only S1，阻塞 total-return 声明 |
| P1 | 候选另类数据 ETL | source/available_at 先行 | 北向、融资融券、限售解禁只进入 candidate tracking | 不阻塞传统因子 S1 |
| P1.5 | CSRP + GMSL 结构性稳健性 | S1-M 正式主线可复现并通过主审计后；S1-D/S1-R 作为风险/执行主线参加验证 | 内部 regime map、GMSL shock-state、row-equal vs date-balanced、拥挤容量、forced deleveraging 和生产前风险审计 | 阻塞可部署叙事，不放宽 S1 hard gate |
| P1.5 | 衰减权重稳健性 | S1-M 正式主线可复现并通过主审计后 | 对比等权 5 年、12 月半衰期 row-equal/date-balanced 指数衰减、18 月敏感性和 6/24 月诊断 | 数据驱动候选，不使用 OOT/holdout 择优 |
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
3. 固定经济逻辑顺序的 Gram-Schmidt 正交化复合打分。
4. Ridge、ElasticNet、线性横截面回归。
5. LightGBM、XGBoost。
6. LightGBM Ranker 或 LambdaRank，用于 Top-N 排序。

第一阶段目标是形成强基线，而不是调参追高收益。

组合构建新增两类预注册对照，但不改变 S1-M 默认主线：

1. 分数分段 sleeve：保留最高分/Top-N 基线，同时测试 `P80-P95` 次高分段、`P60-P80` 中高分段和 `P40-P60` 中段诊断，检验收益是否只来自极端最高排名。低于 `P40` 默认不进入多头持仓，只作风险和反向信号诊断。
2. 市值分段 sleeve：按当日 PIT 市值分位切成 `P0-P20`、`P20-P40`、`P40-P60`、`P60-P80`、`P80-P100`；默认可交易候选优先测试 `P20-P80` 中小到中大型区间，`P0-P20` 微盘段只作诊断或单独高风险 sleeve，不得放宽流动性、ST、停牌和涨跌停约束。

这些 sleeve 必须使用同一训练窗、同一成本、同一交易规则和同一 walk-forward calendar；阈值必须在训练前写入实验登记，不能根据 OOT/holdout 结果挑选最优分段。

Concept shift 处理采用“单轨强基线 + 预注册训练权重 + 数据驱动告警”：

- S1-M 使用单轨 5 年 rolling walk-forward 作为正式主证据框架；S1-D/S1-R 用同样隔离原则做正式风险/执行验证，不是同级 alpha keep 主线，也不是已废弃的 Track A/B、动态 alpha 或在线 Track B。
- 等权 5 年 rolling 是正式主线必须保留的对照基线，指数衰减加权是单轨训练权重候选；S1-D/S1-R 侧输出日频风险/执行报告，未来 tighten-only 规则需独立验证。
- 指数衰减默认半衰期为 12 个月，主口径 `row_equal_decay_weight = 2 ** (-age_trading_days / (half_life_months * 21))`；同时必须报告 `date_balanced_decay_weight = date_weight_t / n_assets_t` 对照，防止近年股票数扩张造成隐性双重加权。两种口径均在每个训练 step 内归一化到均值 1。
- 18 个月半衰期只作预注册敏感性；6/24 个月作为必报诊断，36 个月只能作为可选研究网格，全部计入 `attempt_count`，不能用 OOT 或 holdout 择优。`date-balanced` 的理论角色是把每个交易日作为近似等权经济观察，防止上市股票数扩张让近年样本隐性超配；若 row-equal 有效但 date-balanced 失败且无法预注册解释，只能 `inconclusive` 或 discard。
- 模型默认每 63 个交易日重训一次；S1-M 默认固定月末/月初调仓/预测，21 日滚动为敏感性；S1-D/S1-R 默认每日重算分数、候选、风险告警和执行审计。两次重训之间使用最近一次符合 computed purge 规则的冻结模型版本。冻结模型必须登记 `model_version`、`train_end`、panel/label hash、参数 hash、代码提交、artifact hash、随机种子和回滚原因；命名建议为 `{track_id}_{model_family}_{train_end}_{validation_params_hash8}_{commit8}`。
- 对评审报告中“GMSL red 或 IC 连续 3 步为负触发重训”的建议，当前 S1 不采纳为自动重训规则：GMSL 仍是 candidate/report-only，不能触发模型切换或重训；IC 连续 3 步为负只能提前触发预注册 revalidation 报告。冻结模型替换必须来自预注册重训日或独立 revalidation 失败后的新版本登记，且不得使用当前 step、holdout 或未成熟标签反馈。
- Concept shift 告警只使用已成熟 OOT IC、因子收益或预测前已可得的分布/拥挤度指标；连续 6 步成熟 IC < 0 触发 red quarantine，最近 6 步中至少 5 步为负触发 yellow。告警只触发 report/quarantine/pre-registered revalidation，不改变当前 step 模型、alpha、阈值、early stopping、特征选择或仓位。
- 动态 IC 换手公式只能作为 Phase 2 report-only 或 tighten-only 诊断；输入必须是至少滞后一 step 的成熟 trailing IC。验证前有效上限必须写成 `min(0.10, raw_report_only_formula)`，trailing IC 变好也不得 loosen 到 15%，只能报告或收紧。
- 结构性 regime map、GMSL shock-state、拥挤容量和风险响应只能作为预注册 CSRP/GMSL 生产前风险审计；风险开关必须在完整 walk-forward 中独立验证，不得由人工主观覆盖。
- 3 年窗口、anchored post-2023 或多候选模型库不进入 S1/S1.5 近期路径；未来若单独研究，只能作为后置协议，并且每个 step 的选择必须只由训练窗内部 nested validation 决定。

### 4.2 第二阶段模型

在第一阶段通过后再评估：

- CatBoost：用于类别特征和稳健树模型对照。
- GARCH/HAR-RV：用于波动率和风险状态。
- 轻量 LSTM 或 1D-CNN：仅作为 P4 对照，不早于强基线和审计框架稳定后进入。
- TFT、N-HiTS、PatchTST、iTransformer、AutoGluon-TimeSeries、Darts、NeuralForecast：本地路线降级为研究储备或云端实验，不作为近期执行计划。

当前本机已可用：`lightgbm`、`xgboost`、`qlib`、`cvxpy`、`torch`。  
当前尚未安装或未验证：`arch`、`vectorbt`、`riskfolio-lib`、`PyPortfolioOpt`、`catboost`、`darts`、`neuralforecast`。这些依赖应在对应阶段进入前再安装和验证。

---

## 5. 外部数据接入边界

近期默认不做大规模外部数据接入。理由：

1. 当前 warehouse 已足够支撑第一批核心日频研究。
2. 外部数据必须先定义 schema、`available_at`、质量检查和回滚策略。
3. 贸然把半审计外部表混入 warehouse，会降低刚完成的数据底座可信度。

已确认 AkShare 1.18.57 可提供以下候选数据：

| 排名 | 数据源 | 价值 | 接入边界 |
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


## 5.5 当前验证和准入参数

### 验证框架参数
- **embargo**：10 日。
- **purge**：官方 alpha keep 使用 `computed_purge_days=max(horizon*3,40)`；5/10 日标签为 40 个交易日，20 日标签为 60 个交易日。S1-D/S1-R 的 1 日风险/执行报告默认 20 个交易日 purge，并报告 10/20/40 敏感性；该口径只用于风险/执行、misalignment 和 execution-audit 报告，不得单独支持主动调仓 keep。20 日标签的 40/60/80 日敏感性只能报告样本损失、label overlap proxy、HAC、bootstrap、holdout 和成本后 PnL delta；40 日对 20 日标签是 under-purge 诊断，不能支持 keep。
- **训练窗口**：**5年**（唯一 keep 通道）；4/6 年窗口只作诊断敏感性，计入 `attempt_count` 和试验族台账，不得用于改默认窗口、模型、阈值或半衰期。好结果不得晋级 keep，坏结果不得改默认 5 年窗口，但可形成 robustness warning 并阻塞可部署叙事。
- **训练权重**：指数衰减是单轨训练权重候选；默认半衰期 12 个月，等权 5 年 rolling 必须作为对照，18 个月作为预注册敏感性；6/24 个月为必报诊断，36 个月为可选研究网格，不得用 OOT/holdout 择优。
- **主线 cadence**：S1-M 月选股默认 20 日标签、固定月末/月初调仓，是近期唯一正式 alpha keep 主线；21 日滚动为敏感性。S1-D/S1-R 默认 1/5 日标签、每日盘后输出候选分数、风险预警、GMSL shock state 和执行审计，是正式日频风险/执行主线，但不进入近期主动 alpha 调仓或 official keep。
- **模型重训频率**：默认 63 个交易日重训；S1-M 默认固定月末/月初调仓/预测，21 日滚动为敏感性；S1-D/S1-R 每日重算分数、告警和执行审计但不默认每日重训；非重训 step 使用最近一次冻结模型。
- **OOT steps**：S1-M 预备 smoke/minimum 为**24步 + 分年度分析**；完整验证必须按 2005-2026 月末/月初 calendar、扣除 holdout 后计算全量 OOT/rebalance 步数，并以 `walk_forward_calendar_v1` 生成值为准。S1-D/S1-R 不能把 24 步写成充分日频证据；report-only 风险监控至少 252 个成熟日度决策日，tighten-only 生产规则至少 504 个成熟日、24 个自然月桶和 8 个季度桶，并同时报告日/周/月/季聚合。
- **walk-forward 起始和总步数**：主窗口从 2005-01-01 开始，首个 OOT 起点约为 2010 年；24 步只是最低验收门槛，实际总步数按交易日历和最后 12 个月 holdout 剔除后计算并披露。
- **S1门槛分层**：Hard Gate 包括审计通过、Newey-West HAC 调整后的 IC t-stat **≥1.65**、bootstrap p **<0.10**、最后 12 个月 holdout 至少满足方向一致、成本后超额 > 0、Sharpe > 0、MaxDD/CVaR 不显著差于 benchmark 或等权控制、单月利润贡献不超过 50%，且订单失败/成本/容量在预注册边界内；若 HAC 与 bootstrap 只有一项通过，状态为 `inconclusive` 而不是 keep。Soft Floor 包括换手、年度/市场状态稳定性和高容量模型相对简单基线的增量；尾部风险必须报告并执行预注册 fatal check，未触发 fatal 才能进入 keep/晋级。
- **IC显著性**：IC t-stat 默认使用 **Newey-West HAC** 调整；必须报告默认公式、Andrews (1991)、lag 6 和 lag 12 四种带宽敏感性，keep/晋级取最保守结论；未调整 t-stat 只能作为诊断值。
- **bootstrap方法**：**Block Bootstrap, block=max(label_horizon, rebalance_interval)**，月选股 20 日标签默认 block=21 日；必须报告 10/21/42 日敏感性，晋级或生产 tighten-only 使用最保守结论，≥5000次重抽样。
- **多重检验**：FDR 覆盖完整实验族，而不是只按因子列数触发；当因子 × 标签 × 模型 × 半衰期 × 训练窗口 × 正交化分支 × 执行规则的累计尝试数超过 20 时，默认使用 Benjamini-Hochberg。若因子相关性高或有效假设数不清晰，必须补充 Storey-q 诊断，并记录相关性触发指标、有效假设数、Storey-q、`test_family_id` 和跨 family 累计 `attempt_count`。进入 keep/晋级时 FDR 为硬约束。
- **尾部风险**：S1报告模板必须记录MaxDD/VaR/CVaR/Sortino/Calmar，并对 max drawdown、CVaR、limit-lock CVaR、无法卖出的持仓暴露执行预注册 fatal check；S2 再深化尾部风险优化。
- **Exploratory Tracking机制**：方向一致性≥65%（OOT 24步中IC与对应样本内IC同号的步数/24，辅助：最近6步中4步一致） + 冷却期≥6个月（从首次进入Exploratory Tracking日起算） + 不入组合 + 完整记录；冷却期满后若最近6步仍至少4步方向一致，只能重新进入 S1 候选队列，不能直接 keep。
- **holdout定义**：最后12个月（约252个交易日）作为最终验收窗口，不参与调参、特征选择、early stopping、阈值选择、GMSL 阈值、shock window、行业规则、风控规则、日频 tighten-only 规则或仓位开关选择；12 vs 18个月只在S2预实验中验证。`holdout_access_log.tsv` 最小字段为 timestamp、operator、purpose、track_id、data_range、result_summary、decision_or_read_only、pollution_flag、followup_action；holdout 被用于策略选择后即 burned，只能作只读 benchmark，生产前需新增不少于 252 个交易日的 shadow/forward OOS。
- **Concept Shift + GMSL 分层**：S1-M 保留 5 年 rolling 单轨正式强基线；S1-D/S1-R 是日频风险/执行主线但不是 alpha keep；双轨自适应、在线 Track B 和动态 alpha 不进入近期路径；concept shift 与 GMSL 诊断随 S1 报告输出，并通过成熟 IC 驱动的 yellow/red 状态机和 shock-state report 进入 quarantine/revalidation，不放宽 hard gate。
- 若机器可读参数镜像与本节冲突，以本文档和 `quant_strategy_research_plan_detailed.md` 为准；执行前必须校验一致的参数 hash。

### 因子库扩展
- P1阶段同步做3-5个另类数据源的 source registration 和 candidate ETL（北向资金、融资融券、限售解禁优先）
- 筹码数据ETL从P3提前到P1/P1.5并行准备；PIT、覆盖率、算法解释和异常值审计通过前不进入官方 S1 keep

### 当前验证项
- 因子正交化流程：单因子、等权和原始 ICIR 先保留为基线；V1 在 ICIR 复合和 Ridge/ElasticNet 前使用固定经济逻辑顺序做 Gram-Schmidt：市场因子、行业因子、风格因子、alpha 候选因子。每个 step 报告正交化顺序一致性和 Spearman 稳定性；PCA 只作为 V2 候选，不进入 S1 主线。
- 多重检验校正（FDR 覆盖完整实验族：因子、标签、模型、半衰期、训练窗口、正交化分支和执行规则）
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
- 资金档分两层：小资金实操档 `10 万、20 万、50 万、100 万`；容量压力档 `1000 万、5000 万、1 亿`，表面容量足够时追加 `5 亿`。小资金档必须报告 100 股整数手、现金闲置、最低佣金/最小成交额假设和成本拖累；不能用小资金表现外推大资金容量。

### S1 启动前补充验证
- purge 敏感性：在相同因子和窗口下对比 40/60/80 个交易日 purge；该实验不阻塞面板构建，但阻塞正式 keep/晋级结论。
- S1 前置条件：
  - P0：`universe_daily` 构造审计、S1-M/S1-D walk-forward 日历固化、每步训练截止日满足 purge/embargo。
  - P1：valuation 缺口三口径敏感性、benchmark 覆盖审计、ADV 新股不足标记、validation 参数 hash。
  - P1：concept shift 诊断和成熟 IC yellow/red 状态机预注册，随 S1 输出但不放宽 hard gate。
  - 非阻塞 S1：ADWIN/BOCPD 等额外变点诊断、6/24/36 月半衰期研究网格；均不得进入 keep 决策。
- 24 步仅是最低验证规模和快速 smoke；完整主证据按交易日历生成全量 OOT step，并记录实际 step 数、样本覆盖和产物 hash。

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
12. 让临场主观判断决定模型切换、参数选择、候选 keep 或告警处置；所有处置必须来自预注册数据规则。
13. 把 stress slice、2024-02、post-2023 或全面注册制后样本作为选模窗口；这些只能作为预注册诊断和风险审计。
14. 用行级样本数扩张造成的近期股票数偏差冒充 concept shift 适配。
15. 只用自有参与率判断拥挤容量，不报告因子重叠、左尾、跌停未成交和市场成交额占比。
16. 未建立 holdout access log 就反复查看 holdout 后继续声称其仍是未污染最终验收。
17. 绕过可审计 `features/labels` 面板、manifest/hash、PIT audit、label audit、walk-forward calendar 或 holdout log，直接训练官方 S1 模型。
18. 用临时实验缓存绕过 feature-label 入仓审计、PIT audit、label audit 或 manifest/hash 登记。
19. 把 anchored post-2023 keep、same-step label feedback 或当前 OOT/holdout/stress slice 反馈作为模型选择、阈值选择或参数选择依据。

---

## 7. 执行路线

### Phase A0：S1-M alpha 主线与 S1-D/S1-R 风险执行主线共享审计和日历固化

Phase A0 按阻塞关系拆成 A0.1 和 A0.2：

- **A0.1，阻塞 S1 启动**：`track_registry_v1`、`walk_forward_calendar_S1M_v1`、`WalkForwardCalendarValidator`、`validation_params.json` 参数 hash、`universe_daily_construction_audit`、valuation coverage audit、停牌推断 precision/recall 和估值 `available_at` 抽样审计。
- **A0.2，阻塞 S1 keep**：`holdout_access_log.tsv`、`test_family_registry`、冻结模型 registry、SQLite WAL `experiment_ledger`、factor direction registry、ModelRegistry、`execution_label_audit`、`execution_audit/orders_audit`、`daily_turnover_capacity_report` 和数据版本 hash 机制。

目标：为 S1-M 月选股正式 alpha 主线建立可复现、可审计的启动底座，并为 S1-D/S1-R 日频风险/执行主线固化独立登记、日历、GMSL shock-state、execution label 和离线审计接口。

产出：

- 预注册 walk-forward 参数、指数衰减权重参数和本地参数 hash。
- `warehouse_build_manifest.json`、`external_data_sources.csv`、`validation_params.json`、`track_registry_v1` 和 `walk_forward_calendar_v1` 的 hash。
- 实验层 PIT audit、split label audit、benchmark audit。
- 三层 universe 构造审计报告。
- `holdout_access_log.tsv`、SQLite WAL 实验台账字段、`track_id`、`label_id`、`rebalance_interval`、`holding_period`、`execution_rule_id` 和 `panel_hash`。
- 2026 估值缺口 mask、forward-fill 敏感性和受影响样本报告。
- benchmark 覆盖股票数审计，2005 前 benchmark 仅作敏感性说明。
- 涨跌停禁买/跌停禁卖、连续锁死、开盘冲击和成交失败报告。
- 因子覆盖率和质量报告。
- S1-M 与 S1-D/S1-R 的日历、标签、执行口径和容量报告分离；S1-D/S1-R 结果不得用于选择 S1-M 模型、阈值、半衰期或窗口，也不得在未验证前触发主动调仓、提高净敞口、放宽日换手或增加行业集中。
- GMSL-v1 candidate source registry、timezone/session cutoff audit、source fetch status、候选表初始化和局部源抓取；v1 只能基于 Cboe VIX/OVX/GVZ、国债收益率和 Shibor 做 partial stress report，v2 才是完整外生冲击层。在外部源通过 vendor/license、PIT、coverage 和 session cutoff 审计前只能写成 `candidate_etl`。

### Phase A-M：S1-M 月选股强基线

目标：验证 20 日标签、约月度调仓和低换手多因子组合是否在成本、容量和成交约束后仍有超额。

产出：

- 20 日 forward excess/rank 标签的单因子 IC、RankIC、ICIR。
- 固定月末/月初调仓的等权、ICIR、正交化复合因子、线性、LightGBM/Ranker 对照；21 个交易日滚动作为敏感性。
- Newey-West HAC IC t-stat、Andrews/lag 6/lag 12 带宽敏感性、block bootstrap 和 10/21/42 日 block 敏感性。
- 固定月度调仓的成交失败、T+1 单日执行、1/3/5 日分批执行必报、月度换手和容量上限。
- 分层收益、制度性风险切片、IC 衰减半衰期和 concept shift 报告。
- 分数分段与市值分段持仓对照：最高分/Top-N、次高分段、中高分段、P20-P80 中小盘/中盘组合和微盘诊断；所有分段阈值预注册并计入 `attempt_count`。

### Phase A-R：S1-D/S1-R 日频风险/执行主线

目标：验证 1/5 日标签和短 horizon 信号是否能作为短期因子研究、S1-M 持仓风险预警、alpha 衰减监控、GMSL shock-state、订单失败、流动性和离线执行审计输入；近期不作为主动 alpha 调仓或 official keep 主线。

产出：

- 1 日和 5 日 forward excess/rank 标签的单因子 IC、RankIC、ICIR；10/20 日只作稳健性或与月选股交叉对照。
- 每日盘后 `S1-D_daily_risk_execution_offline` 候选清单：`as_of_date`、`trade_date`、`asset_id`、`score`、`rank`、`horizon`、`risk_signal`、`alert_state`、`gmsl_shock_state`、`model_version`、`feature_cutoff`、`label_cutoff`、`no_trade_reason`；离线权重字段只能命名为 `offline_sim_target_weight`，不得接入生产订单接口。
- 离线滚动组合模拟的等权、ICIR、正交化复合因子和线性模型基线；非线性模型只作后续对照，模拟结果不得进入 official keep 或收益承诺。
- `daily_orders_audit`：涨停买入失败、跌停卖出失败、停牌延迟、100 股整数手、T+1、未成交继续暴露、解锁后 1/3/5 日收益；独立 `limit_events` 未入仓前使用 `tradability_daily_enriched` / `universe_daily` close-based 代理字段。
- `daily_turnover_capacity_report`：日换手、成本拖累、ADV 参与率、成交失败率、容量上限、limit-lock CVaR，以及成本 1x/2x/3x 敏感性；三层换手控制默认重叠率 >=85%、单票日变动 <=2%、单边日换手 <=10%，执行裁剪顺序为总换手上限、行业上限、个股上限。
- 日度成熟 IC 状态机、按日/周/月/季汇总的 concept shift + GMSL 报告、与 S1-M 持仓重叠度和冲突交易统计；report-only 至少 252 个成熟日，tighten-only 至少 504 个成熟日、24 月桶和 8 季度桶。

### Phase B：风险状态和组合约束

目标：减少回撤，约束风格、行业暴露和入市资本比例。

产出：

- 市场状态变量库。
- 资金仓位控制模块：选股模型先生成目标股票篮子，资金模块再按市场状态给组合目标市值乘以 capital multiplier；现金部分不追买、不加杠杆、不参与收益承诺。
- 仓位开关对照实验：至少包含 full-investment 对照、保守映射 `牛市 80%-100% / 震荡 40%-70% / 熊市 0%-30% / 极端风险 0%`、挑战映射 `100/60/30/0` 和固定低仓位对照。
- CSRP/GMSL 稳健性：等权 5 年、12 月半衰期 row-equal/date-balanced 指数衰减、18 月半衰期敏感性、结构性 regime map、GMSL shock-state、拥挤容量、forced deleveraging 和成熟 IC 状态机对照；必须同口径击败等权控制且通过全部审计才可晋级。
- 风险开关 v1：S3 前使用 25/25/25/25 均匀权重占位；S3 验证后替换为数据驱动仓位比例。100/60/30/0 只保留为可选历史假设或挑战基线，不作为默认事实。
- 熔断规则：组合回撤、市场宽度崩塌、跌停压力和流动性枯竭触发降仓。
- 行业、市值、beta、换手、容量约束组合。

资金仓位控制模块只在 S1.5/S2 之后作为后续验证项，不参与 S1-M 默认选股模型训练、特征选择、阈值选择或 holdout 策略选择。若该模块只降低收益而不能降低最大回撤、CVaR、跌停卖不出暴露或成交失败，不得 keep。

### Phase C：外部低频数据 ETL

目标：补齐基本面、公司行为、执行增强、风险事件和 GMSL 完整外生冲击覆盖。Phase C 是后续数据收集、整理、清洗规划；未获明确执行指令前不新增抓取或入仓。

优先顺序：

1. P0 governance：A0.1 先生成 `track_registry_v1`、`walk_forward_calendar_S1M_v1`、`WalkForwardCalendarValidator`、`universe_daily_construction_audit` 和必要参数 hash；A0.2 再补 `holdout_access_log.tsv`、`test_family_registry`、冻结模型 registry 和 SQLite WAL `experiment_ledger`，用于锁定 S1-M / S1-D/S1-R 的验证边界、computed purge、holdout 污染状态、model_version、attempt count、FDR 方法和统计冲突状态。
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
2. `D:\quantum_a0\quant-strategy-study-plan\quant_strategy_research_plan_detailed.md`：详细执行规范，记录数据口径、标签、验证、回测、台账、验收和复核清单。

数据依据文档也必须随 Git 同步维护：

1. `DATA_USAGE_GUIDE.md`：数据表使用口径。
2. `WAREHOUSE_README.md`：warehouse 状态说明。
3. `external_data_sources.csv`：外部源登记和 source gap。
4. `warehouse_build_manifest.json`：当前数据事实、source status 和关键 audit hash。
5. `validation_params.json`：机器可读验证参数镜像。

`D:\data\strategy\` 下的旧副本只作为迁移前来源；后续若需要保留副本，必须从 Git 项目同步回写，不得双向分叉维护。

`量化时间序列模型调研和选择.md` 与 `量化策略设计调研与建议.md` 作为参考材料，不作为直接执行规范。






