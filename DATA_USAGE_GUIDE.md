# D:\data\warehouse 数据说明和使用建议

## 数据分层

`warehouse` 采用不可变原始层和可审计特征层。原始压缩包和 CSV 仍保留在 `D:\data` 原位置，仓库内只保存派生表、清单、schema、质量报告和配置。

## 单一事实源

本文件只记录数据使用口径。表行数、最大日期、source status、构建脚本和关键审计结果应以 `warehouse_build_manifest.json`、`audit_reports/leakage_check_report.json`、`audit_reports/source_status_audit_r7.json`、`audit_reports/feature_label_panel_v1_manifest.json`、`audit_reports/gmsl_manifest.json` 和 `audit_reports/p1_data_preconditions_validation.json` 为准；策略报告和实验登记必须引用 manifest hash，不能手工抄写行数后再作为权威事实。

当前 Git 项目镜像的依据文档包括：

- `DATA_USAGE_GUIDE.md`
- `WAREHOUSE_README.md`
- `external_data_sources.csv`
- `warehouse_build_manifest.json`

## 当前构建结果

| 项目 | 当前结果 |
|---|---:|
| 构建模式 | full |
| 日 K 股票文件 | 5834 |
| 未复权日 K 行数 | 17,599,789 |
| 日收益行数 | 17,599,789 |
| 每日指标行数 | 16,642,794 |
| 当前行业快照行数 | 5,834 |
| PIT 行业变更事件 | 53,925 |
| Benchmark 行数 | 31,229 |
| Reference rate 行数 | 55,964 |
| 2023年以来 A 股停复牌提醒 | 1,447 |
| 时间跨度 | 1990-12-19 至 2026-04-27 |
| `security_master` 股票数 | 5834 |
| 当前股票列表外的历史证券 | 346 |
| `processed_inventory` 文件数 | 52 |
| 原始文件清单 | 74,490 |
| 复权因子重复日期去重 | 4,468 行 |
| `risk_warning_daily` 行数 | 8,973,264 |
| `tradability_daily_enriched` 行数 | 18,177,689 |
| `universe_daily` 行数 | 18,177,689 |
| `exchange_calendar` 行数 | 39,486 |
| `trading_costs.equity_cost_history` 行数 | 23 |
| `index_membership` 当前快照行数 | 3,600 |
| `features/market_daily_v1` 行数 | 15,420,654 |
| `labels/forward_returns_v1` 行数 | 15,420,654 |
| `corporate_actions` sanity reference 行数 | 9,534 |
| `global_macro_daily` 行数 | 17,526 |
| `gmsl_shock_state` 行数 | 9,176 |
| `geopolitical_event_calendar` 行数 | 0 |

重要解释：

- `factor_after_last_bar_assets=255` 表示部分证券复权因子最后日期晚于最后一根日 K bar。这通常是停牌、退市或无成交 bar 后仍有因子记录；不能把因子存在解释为可交易。
- `return_adjusted_pit` 和未复权日 K 行数一致，说明收益表没有因复权因子重复日期而放大。
- 交易日历包含 2026-04-28 之后的开市日，但本地日 K 和复权因子最新到 2026-04-27；`calendar.is_data_available` 已区分这一点。
- `reference_rates` 已在 P1 前置更新中追加 9 条 Shibor 序列。第五轮 AkShare 接入阶段的 “Shibor 后续修复” 说明已被 P1 更新取代。
- R7 已生成 `features/market_daily_v1` 与 `labels/forward_returns_v1`，各 15,420,654 行，覆盖 2005-2026，并登记 `feature_label_panel_v1_manifest.json`、`pit_feature_audit_market_daily_v1.json` 和 `label_audit_forward_returns_v1.json`。这只解除“面板未入仓”阻塞；官方 S1 训练仍必须先固化 walk-forward calendar、holdout log、测试族台账、execution label audit 和实验登记。
- R11 已初始化 `global_macro_daily`、`gmsl_shock_state` 和 `geopolitical_event_calendar` 三张 GMSL candidate 表，并生成 `gmsl_manifest.json`、`gmsl_timezone_available_at_audit.json`、`gmsl_source_fetch_status.csv` 和 `gmsl_coverage_report.csv`。2026-04-30 实际尝试抓取 FRED `fredgraph.csv` 配置源，所有 FRED series 均因 `ReadTimeout` 失败；同轮 Cboe 官方 VIX/OVX/GVZ CSV 抓取成功，`global_macro_daily` 形成 17,526 行，`gmsl_shock_state` 形成 9,176 行。GMSL 仍不能作为可用 alpha 输入，只能作为 source registry、stress report、时区审计和后续 PIT/coverage 审计框架。

## 数据可用状态分层

`external_data_sources.csv` 使用 `availability_bucket` 显式区分数据状态：

| 状态 | 含义 | 当前示例 | 使用限制 |
|---|---|---|---|
| `available_now` | 已在 warehouse 或 manifest 镜像中可用，但仍受用途限制 | 日 K、PIT adjusted return、tradability/universe、benchmark、reference rates、PIT 行业、估值里的市值/换手等市场慢变量、R7 market-only features/forward labels、核心 source status 字段 | 可用于 S1 market-only 研究准备；正式训练仍需 walk-forward calendar、holdout log、PIT/label/benchmark audit hash、execution label audit 和实验登记。 |
| `candidate_etl` | 只完成 source registration、局部抓取、空表初始化或计划接入 | 融资融券、北向、限售解禁、ETF flow、市场宽度、股指期货 basis/OI、财报、分钟/集合竞价、AkShare 公司行为 sanity reference、GMSL 外生冲击源 | 只可做 ETL、覆盖率、PIT、timezone/session cutoff 和质量审计；未完整入仓前不得进入官方 S1 keep。 |
| `missing` | 应有但当前没有可审计主表或字段 | walk-forward calendar、holdout access log、测试族台账、execution label audit、完整公司行为主表 | 阻塞相关训练、字段结论或正式 evidence。 |
| `blocked_by_source_gap` | 需要官方、授权或可靠历史源，不是简单 ETL 能解决 | 沪/北历史 ST、全历史官方停复牌、历史 PIT 指数成分权重、完整独立公司行为主表 | 必须披露 source gap；不得用当前快照、近期局部源或推断表冒充完整 PIT。 |

Git 项目中的依据文档和 `warehouse_build_manifest.json` 是当前策略文档事实源。`D:\data\warehouse` 根目录下同名说明文件若滞后于 Git 镜像，不得覆盖 manifest 和本地 audit JSON 的结论。

## 目录结构

| 目录/文件 | 内容 | 当前用途 |
|---|---|---|
| `raw_manifest/` | `raw_files.csv/parquet`、摘要 JSON | 原始资产清单、文件大小、mtime、后续增量比对 |
| `security_master/` | `equity_master`、`option_contracts` | 股票/期权主数据，含历史证券补全 |
| `industry_classification/` | 当前行业快照 + PIT 行业变更 | 当前快照、AkShare/巨潮行业归属变动事件、PIT 行业区间 |
| `calendar/` | `trading_calendar`、`trading_rules.csv`、`cost_model.csv` | 日期对齐、交易规则、最低成本模型 |
| `prices_daily_unadjusted/` | 年度分区未复权日 K | 成交价、成交量、成交额、涨跌停/停牌判断 |
| `prices_daily_returns/` | 年度分区收益 | `return_raw`、`return_adjusted_pit` |
| `tradability_daily/` | 年度分区逐日可交易性 | 观测 bar、推断停牌/无成交、bar 质量不可交易标记 |
| `suspension_events/` | 推断停牌/无成交事件 + AkShare 停复牌提醒 | 缺失 bar 推断事件、2023 年以来 A 股停复牌提醒 |
| `valuation_daily/` | 年度分区每日指标 | PE/PB/市值/股本/换手率等日频指标，T 日盘后可见 |
| `features/market_daily_v1` | R7 market-only 日频特征面板 | 市值/流动性/动量/反转/波动率/ADV/tradability/universe/PIT 行业等 S1 准备特征 |
| `labels/forward_returns_v1` | R7 forward return 标签面板 | 1/5/10/20 日 forward adjusted return、全 A 等权代理超额、rank/top decile 标签 |
| `global_macro_daily` | GMSL 外生宏观候选表 | Cboe VIX/OVX/GVZ 已形成 17,526 行 candidate 数据；FRED Brent/WTI、DXY、UST、全球股指等仍抓取失败或待接入，只作 candidate/stress report 框架 |
| `gmsl_shock_state` | GMSL shock-state 候选表 | 基于当前 Cboe 候选源形成 9,176 行 partial shock-state；非 keep gate，不得用于 alpha 选模或调阈值 |
| `geopolitical_event_calendar` | 地缘事件窗口候选空表 | 俄乌、中东、美伊、红海、制裁等预注册事件窗口；当前 0 行，只作 stress reporting |
| `corporate_actions/` | R7 公司行为 sanity reference | AkShare/Sina 历史分红摘要和 Eastmoney 2023 年报分红送配样本，只作复权 sanity，不是完整主表 |
| `benchmarks/` | 内部代理 + 官方指数 benchmark | 全 A 等权、总市值加权代理、沪深300/中证500/中证1000 |
| `reference_rates/` | 无风险利率 | 固定 fallback + 中国国债收益率 + Shibor 实际序列 |
| `processed_inventory/` | 旧 processed 产物盘点 | 判断旧清洗结果能否复用 |
| `schemas/` | `schema_registry.csv` | 字段登记、时间字段和质量规则 |
| `audit_reports/` | 构建报告、泄漏检查、覆盖清单 | 验收与追溯 |
| `configs/` | `retention_policy.yaml` | 派生产物/缓存/临时解压/告警归档策略 |
| `external_data_sources.csv` | 外部数据源登记 | P1/P1.5/P2/P3 source registration，不等于已入仓 |

## 表级口径

### prices_daily_unadjusted

未复权日 K，代表真实可成交价格。适用于成交模拟、涨跌停判断、停牌判断、成交额容量、滑点和冲击成本估计。不要用它直接计算长期动量标签，因为除权除息会造成价格跳变。

核心字段：

- `asset_id`：统一证券 ID，如 `000001.SZ`、`600000.SH`、`832317.BJ`。
- `trade_date`：行情日期。
- `open/high/low/close/pre_close`：未复权价格。
- `pct_change_vendor`：供应商原始涨跌幅字段，单位是百分比数值。
- `volume/amount`：成交量和成交额。
- `tradable_flag`：第一版可交易标记，仅表示 bar 存在且成交量/成交额/收盘价有效；涨跌停、一字板、T+1 仍需上层模型处理。
- `available_at/decision_time`：日频默认 T 日 16:00 后可见和决策。

### prices_daily_returns

- `return_raw`：`close_t / close_{t-1} - 1`，只用于原始价格一致性检查。
- `return_adjusted_pit`：`close_t * factor_t / (close_{t-1} * factor_{t-1}) - 1`，用于收益标签、动量、波动率和绩效统计。
- 缺少当前或上一根 bar 的复权因子时不填 1，返回空值并写入 `quality_flags`。

使用原则：

- 训练标签、动量、波动率、组合绩效优先使用 `return_adjusted_pit`。
- 原始价格异常、除权跳变、停复牌诊断使用 `return_raw`。
- 不要把全样本最新前复权价作为模型输入。

### tradability_daily

逐日可交易性伴生表。它不合成 OHLCV，而是把证券生命周期内的开放交易日展开为 `(asset_id, trade_date)`，并与价格主表对齐。

当前结果：

- 年度分区：37 个，1990-2026。
- 总行数：18,177,689。
- `bar_present=True`：17,599,789 行，与未复权价格主表一致。
- `is_suspended_inferred=True`：577,900 行，表示证券首末 bar 之间的开市日缺少价格 bar。
- `is_tradable=True`：17,599,557 行，底层 bar 存在且价格主表 `tradable_flag=True`。
- `calendar_date_status=observed_price_bar_not_in_calendar`：3 行历史边界数据，表示价格 bar 存在但当前交易日历未覆盖。

使用原则：

- 回测股票池和成交过滤应优先 join `tradability_daily`，用 `is_suspended_inferred=True` 禁止当日买卖或将持仓标记为不可交易。
- `is_suspended_inferred` 是工程推断，不是官方停牌公告。它也可能覆盖长期无 bar、暂停上市、代码变更前后缺口或源数据缺口。
- 价格、成交额、收益仍从 `prices_daily_unadjusted` 和 `prices_daily_returns` 读取；不要为缺失 bar 合成价格。

### suspension_events

`suspension_events/inferred_suspension_events` 将连续 `is_suspended_inferred=True` 的交易日聚合为事件：

- 事件数：75,630。
- 覆盖证券：3,455 只。
- 覆盖推断缺失交易日：577,900。

第四轮优化后，该表补充了事件级诊断字段：

- `event_length_bucket`：按 1 日、2-5 日、6-20 日、21-60 日、61-250 日、250 日以上分桶。
- `event_type_inferred`：按长度粗分单日缺失、短区间、中区间、长期暂停/源缺口候选。
- `tradability_constraint_confidence`：作为不可交易约束的置信说明；当前为 `high_no_observed_price_bar`。
- `official_suspension_validation_status`：官方停牌源验证状态；当前为 `not_validated_no_official_source`。

该表适合快速排查长期停牌/无 bar 区间，正式回测日级过滤仍建议读取 `tradability_daily`。

`suspension_events/official_suspension_events_akshare` 为 AkShare/百度股市通 2023 年以来 A 股停复牌提醒：

- 事件数：1,447。
- 覆盖证券：980 只。
- 数据范围：2023-01-03 至 2026-04-27。
- 仅保留 `SH/SZ/BJ`，已过滤港股和非当前 A 股 warehouse 标的。
- 它适合校验近期 `is_suspended_inferred`，但历史深度有限，不能替代完整交易所官方公告库。

### security_master

股票主表不只依赖当前股票列表，还从日 K ZIP 文件名补入历史出现过的证券。当前列表缺失但历史有行情的证券会标记 `in_current_stock_list=false`，用于控制幸存者偏差。

示例：`832317.BJ` 当前股票列表缺失，但已由日 K 补入，`first_bar_date=2020-07-27`、`last_bar_date=2021-10-20`、`in_current_stock_list=false`。

`is_delisted`、`listing_status_inferred` 和 `last_bar_staleness_days` 是基于当前股票列表和最后 bar 日期的工程推断字段，不是交易所官方退市公告字段。用于构建 PIT universe 前的风险提示和状态初筛。

### industry_classification

`industry_classification/current_industry_snapshot` 来自当前股票列表/equity_master 的行业字段：

- 总行数：5,834。
- 行业非空：5,488 行。
- 行业缺失：346 行，主要是当前列表外历史证券。
- 唯一行业：110 个。

使用原则：

- 该表是当前快照，不是 PIT 历史行业分类，不能用于历史任一天的股票池筛选、行业中性化或行业轮动回测。
- 可用于当前截面诊断、数据覆盖检查，或作为后续接入 PIT 行业源前的显式占位。
- 若要做历史行业中性化，应先接入带 `effective_from/effective_to/available_at` 的 PIT 行业分类源。

第五轮后新增 AkShare/巨潮 PIT 行业事件：

- `industry_change_events_akshare`：53,925 行，逐证券行业归属变动事件。
- `pit_industry_intervals_akshare`：53,925 行，按 `classification_standard_code` 生成的行业有效区间。
- 尝试证券 5,834 只，成功 5,510 只，空返回/错误 324 只；详情见 `audit_reports/akshare_industry_fetch_status.csv`。
- 覆盖 12 个分类标准，使用时必须指定标准，例如证监会、申万、巨潮或中证口径，不要混用。
- `effective_to` 是由下一次变更日期离线推导的区间终点；做 PIT 特征时以 `effective_from/available_at` 控制可见性，避免把未来变更信息用于当日决策。

### valuation_daily

每日指标来自 `D:\data\每日指标`，2000-2025 年按股票年度 CSV、2026 年按日 CSV 统一入仓为年度 Parquet。

当前结果：

- 年度分区：27 个，2000-2026。
- 总行数：16,642,794。
- 源 CSV：72,418 个。
- 构建错误：0。
- `(asset_id, trade_date)` 重复键：0。

使用原则：

- 市值、流通市值、股本、换手率等市场可得慢变量默认 T 日 16:00 可见，不能用于 T 日开盘前决策。
- PE、PB、PS、TTM 等估值/财报派生字段虽然已入 `valuation_daily`，但仍必须通过公告日、报告期、重述和供应商计算时点的 PIT 审计后，才可作为基本面因子 keep 的证据。
- S1 应先输出 `market-only baseline`，再单独输出 `valuation/fundamental baseline`，避免把行情衍生 alpha 与潜在财报时点风险混在一起。
- `source_file` 和 `source_mtime` 可用于追踪具体源 CSV。
- 与收益表做特征拼接时推荐以 `prices_daily_returns` 或可交易 universe 为主表左连接 `valuation_daily`；估值供应商覆盖与行情供应商不完全一致。

### benchmarks

当前 benchmark 同时包含内部代理和 AkShare 中证指数：

- `CN_A_ALL_EQW_PROXY`：所有当日有 `return_adjusted_pit` 的证券等权平均。
- `CN_A_ALL_MV_WEIGHTED_PROXY`：使用上一交易日可得 `valuation_daily.total_mv` 加权，覆盖从 2000 年每日指标可用后开始。
- `CSI_000300_OFFICIAL_AKSHARE`：沪深300指数日频收盘收益。
- `CSI_000905_OFFICIAL_AKSHARE`：中证500指数日频收盘收益。
- `CSI_000852_OFFICIAL_AKSHARE`：中证1000指数日频收盘收益。

旧 `CN_A_ALL_AMOUNT_WEIGHTED_PROXY` 已移除：同日成交额加权会把上涨当天放量股票后验放大，属于成交流向统计，不是可投资指数。官方中证指数可用于产品比较和基准归因；内部代理仍可用于全市场横截面研究。

### reference_rates

当前 `reference_rates` 已包含两类序列：

- `CNY_FIXED_1P5PCT_RESEARCH_ASSUMPTION`：固定年化 1.5% 研究假设，保留为 2002 年前缺口或测试 fallback。
- `CNY_GOVT_BOND_2Y_AKSHARE`、`CNY_GOVT_BOND_5Y_AKSHARE`、`CNY_GOVT_BOND_10Y_AKSHARE`、`CNY_GOVT_BOND_30Y_AKSHARE`：AkShare 中国国债收益率实际序列，覆盖 2002-01-04 至 2026-04-27。
- `CNY_SHIBOR_*_AKSHARE`：9 条 Shibor 序列，合计新增 23,043 行；隔夜 Eastmoney/AkShare 序列覆盖 2006-10-08 至 2026-04-27，金十/AkShare 多期限序列覆盖 2015-05-08 至 2026-04-27。

Sharpe/超额收益建议优先使用实际国债收益率；资金利率和短端流动性研究可使用 Shibor。固定 1.5% 序列只作为早期缺口或测试 fallback，正式绩效报告必须说明所用 `rate_id`。

### calendar

交易日历来自本地 SSE 日历。日历开市不等于行情已更新，使用时必须结合数据最大日期。

`is_data_available` 的含义是该交易日开市且已被当前日 K 数据覆盖。2026-04-28、2026-04-29、2026-04-30 虽然开市，但当前行情未覆盖，因此为 `False`。

`trading_rules.csv` 已结构化区分 `scenario`：

- `ipo_first_5_trading_days`：科创板、创业板注册制后、北交所上市前 5 个交易日不设涨跌幅限制，`limit_pct` 为空。
- `regular_after_ipo_day_5`：上市第 6 个交易日起进入常规涨跌幅。
- `settlement`：普通 A 股默认 T+1。

### processed_inventory

该表不是研究输入，而是旧清洗产物盘点。它记录文件大小、mtime、行数、字段摘要、日期范围和证券/合约数量。用途是：

- 判断旧 `processed` 数据是否能复用；
- 防止重复造表；
- 标记历史清洗产物中的已知问题，例如旧期权清洗曾经做过整月流动性过滤。

## 回测使用建议

1. 信号日：使用 T 日盘后可见数据。
2. 决策日：`decision_time` 默认 T 日 16:00。
3. 执行日：普通股票默认 T+1，不做 T+0。
4. 成交过滤：bar 存在、成交量和成交额大于 0；涨停买入、跌停卖出、一字板需保守处理。
   - S1-D/S1-R 现阶段优先使用 `tradability_daily_enriched` / `universe_daily` 的 close-based 买卖阻断、涨跌停和停牌推断字段做保守订单会计；独立 `limit_events` 仍是 candidate ETL，未入仓和审计前不得写成可用事件表。
   - close-to-close adjusted forward label 不能直接等同账户可交易收益；正式 keep 或日频风险规则升级前必须做 execution-aligned PnL audit。
5. 股票池至少拆成三层：
   - `research_observable_universe`：用于因子 IC、特征分布和 concept shift 诊断；从已上市、bar 存在、基础生命周期和数据质量派生，不因 T 日涨跌停直接删除风险样本。
   - `entry_eligible_universe`：用于买入候选；加入 T+1 可买、ST、上市年龄、ADV、容量和涨跌停压力约束。
   - `execution_accounting_universe`：用于订单会计；记录涨停买不到、跌停卖不出、停牌延迟和解锁后收益。
6. 当前 `universe_daily.in_factor_research_universe` 是保守 close-based 因子 universe，更接近 `entry_eligible_universe`，不能替代完整研究观察 universe。
7. 成本：优先读取 `trading_costs/equity_cost_history.parquet`，并区分 `official_or_high_confidence_history` 与 `research_assumption`。
8. 无风险利率：`reference_rates` 已含国债收益率和 Shibor；2006 年前或 Shibor 缺口仍可用固定 1.5% fallback，但应在绩效报告中说明。
9. GMSL：所有海外或夜盘外生冲击数据必须先转 UTC，再按 Asia/Shanghai 决策时点判断可见性。若源市场收盘或供应商发布时间晚于 A 股 T 日 16:00，该记录只能用于下一 A 股决策日。当前 GMSL 仅有 Cboe VIX/OVX/GVZ 候选源局部入仓，不能用于 alpha feature selection、model selection、threshold tuning、exposure increase 或 turnover cap loosening。

## 常用读取示例

```python
from pathlib import Path
import pandas as pd

root = Path(r"D:\data\warehouse")

# 读取 2024 年 PIT 收益
ret_2024 = pd.read_parquet(root / "prices_daily_returns" / "year=2024")

# 读取股票主表，包含历史退市证券
equity = pd.read_parquet(root / "security_master" / "equity_master.parquet")

# 只取可用于动量/标签的收益
usable_ret = ret_2024.dropna(subset=["return_adjusted_pit"])

# 读取 2024 年可交易性，过滤推断停牌日
tradability_2024 = pd.read_parquet(root / "tradability_daily" / "year=2024")
tradeable_keys = tradability_2024.loc[
    tradability_2024["is_tradable"] & ~tradability_2024["is_suspended_inferred"],
    ["asset_id", "trade_date"],
]

# 读取 P1 默认 universe：已包含停牌、涨跌停买卖阻断、上市年龄和深市 ST 状态
universe_2024 = pd.read_parquet(root / "universe_daily" / "year=2024")
factor_universe = universe_2024.loc[
    universe_2024["in_factor_research_universe"],
    ["asset_id", "trade_date"],
]

# 读取增强可交易性：close-based 约束适合日频保守回测
tradability_enriched_2024 = pd.read_parquet(root / "tradability_daily_enriched" / "year=2024")

# 构造研究观察 universe 示例：保留涨跌停风险样本，不直接使用 close-based 可买卖作为 IC 过滤
research_observable = tradability_enriched_2024.loc[
    tradability_enriched_2024["bar_present"]
    & tradability_enriched_2024["is_tradable"]
    & (tradability_enriched_2024["listing_age_trading_days"] >= 60),
    ["asset_id", "trade_date"],
]

can_enter = tradability_enriched_2024.loc[
    tradability_enriched_2024["can_buy_close_based"],
    ["asset_id", "trade_date"],
]
```

## 质量检查建议

每次增量或全量重建后至少运行：

```powershell
python D:\data\scripts\warehouse\leakage_check.py --warehouse D:\data\warehouse
```

并检查：

- `prices_daily_unadjusted` 与 `prices_daily_returns` 行数一致；
- `warehouse_build_manifest.json`、`leakage_check_report.json` 和 P1 validation 报告中的行数、最大日期、source status 一致；
- `leakage_check_report.json` 已覆盖 `features`、`labels`、`corporate_actions`、`global_macro_daily`、`gmsl_shock_state` 和 `geopolitical_event_calendar`，当前 21 类目录 PASS；
- `features/market_daily_v1` 与 `labels/forward_returns_v1` 行数一致，`feature_label_panel_v1_manifest.json` 中 parquet hash 与本地文件一致；
- `pit_feature_audit_market_daily_v1.json` 和 `label_audit_forward_returns_v1.json` 均 PASS；
- `source_status_audit_r7.json` 显示核心表必需 source/PIT/time 字段已存在；
- `valuation_daily` 通过时点约束和重复键检查；
- `benchmarks` 和 `reference_rates` 通过时点约束和重复键检查；
- `tradability_daily` 通过时点约束和 `(asset_id, trade_date)` 重复键检查；
- `suspension_events` 通过事件时点约束和 `(asset_id, event_start_date, event_end_date)` 重复键检查；
- `industry_classification` 通过快照、行业变更事件和 PIT 区间的时点/重复键检查；
- `risk_warning_events` 和 `risk_warning_daily` 通过时点约束和重复键检查；
- `tradability_daily_enriched` 与 `universe_daily` 行数应与 `tradability_daily` 一致；
- `index_membership` 当前权重快照按指数合计应接近 1；
- `trading_costs` 必须明确区分官方/高置信历史和研究假设；
- `bar_present_rows` 与 `prices_daily_unadjusted` 行数一致；
- `(asset_id, trade_date)` 无重复；
- `calendar.is_data_available` 不晚于行情最大日期；
- `quality_flags` 中缺因子、首根 bar、无成交等比例是否异常；
- `processed_inventory` 文件数和日期范围是否符合预期。
- `benchmark_sanity_report` 中市值加权代理不存在异常指数点位；同日成交额加权代理不应重新作为默认基准。
- 公司行为/除权除息/分红送配未入仓前，S1 只能声明使用 `adjusted-return proxy`，不能宣称完整 total-return accounting 已闭环。
- 若训练使用指数衰减权重，必须同时报告 `row_equal_decay` 和 `date_balanced_decay` 对照，避免近期股票数扩张造成隐性双重加权。
- 若报告 GMSL，必须同时引用 `gmsl_manifest.json`、`gmsl_timezone_available_at_audit.json`、`gmsl_source_fetch_status.csv`、`gmsl_coverage_report.csv` 和 source registry hash；当前只完成 Cboe VIX/OVX/GVZ 候选源抓取，FRED 配置源仍全部超时，不能宣称已完成外生冲击数据入仓或 PIT/coverage 审计闭环。

## 禁止用法

- 用全样本最新前复权价格作为训练特征或历史决策输入。
- 用未来股票列表、未来行业、未来 ST 状态筛选历史样本。
- 把交易日历未来开市日期当作已有行情日期。
- 在清洗阶段用整月成交量过滤期权合约。
- 用 `tradable_flag=True` 直接代表一定能成交。它只是底层 bar 可用性标记，不包含涨跌停、一字板、撮合失败、滑点和冲击成本。
- 把 `is_suspended_inferred=True` 当作官方停牌公告。它是缺失 bar 推断，需后续官方事件源校验。
- 把 `industry_classification/current_industry_snapshot` 当作历史 PIT 行业分类使用。
- 混用不同 `classification_standard_code` 的 PIT 行业区间做行业中性化。
- 把 AkShare/百度停复牌提醒当作全历史完整交易所公告库。
- 把 `index_membership` 当前快照倒灌为历史 PIT 成分权重。
- 把 `risk_warning_current_snapshot` 或当前股票名倒灌为历史 ST 状态。
- 把 `exchange_calendar` 当前 SH/SZ/BJ 代理表当作三所官方历史差异日历。
- 把 `universe_daily.in_factor_research_universe` 当作所有 IC 研究的唯一 universe，并因此删除涨跌停/停牌风险样本。
- 把行级样本数扩张带来的近期权重上升解释成 concept shift 适配效果。
- 把 stress slice、holdout 或当前 OOT 结果用于同一步模型选择、半衰期选择、阈值选择、特征选择或 early stopping。
- 把 GMSL shock state 或地缘事件窗口用于提高净敞口、杠杆、单票权重、行业集中或日换手；未通过 S3 独立验证前，GMSL 只能 report-only 或 tighten-only。
