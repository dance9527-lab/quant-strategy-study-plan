# D:\data\warehouse 使用说明

> 构建时间：2026-04-29 02:14:44

本目录是 `D:\data` 的 point-in-time 数据仓库。原始数据不被修改，所有派生产物都保留来源文件、可见时间和质量标记。

当前策略 Git 项目将本 README、`DATA_USAGE_GUIDE.md`、`external_data_sources.csv` 和 `warehouse_build_manifest.json` 作为数据依据文档镜像。表行数、最大日期、source status 和构建脚本以根目录 `warehouse_build_manifest.json` 与 `audit_reports/leakage_check_report.json`、`audit_reports/source_status_audit_r7.json`、`audit_reports/feature_label_panel_v1_manifest.json`、`audit_reports/p1_data_preconditions_validation.json` 为准；策略文档不得把手工复制的行数当作单一权威。

## 核心目录

- `raw_manifest/`：原始文件清单，不做默认全量 hash，避免 104GB 数据的重复 IO。
- `security_master/`：证券主数据。`equity_master` 同时包含当前股票列表和日 K ZIP 中出现的历史/退市证券。
- `industry_classification/`：当前行业快照表，以及 AkShare/巨潮行业归属变动事件和 PIT 行业区间表。
- `calendar/`：交易日历、第一版交易规则、最低可用成本模型。
- `prices_daily_unadjusted/`：未复权日 K，可用于执行价、涨跌停、停牌和成交额约束。
- `prices_daily_returns/`：`return_raw` 与 `return_adjusted_pit`。后者按相邻累计复权因子增量计算，不使用全样本最新因子。
- `tradability_daily/`：逐日可交易性伴生表，显式标记观测 bar、推断停牌/无成交和 bar 质量不可交易。
- `suspension_events/`：由连续缺失 bar 聚合的推断停牌/无成交事件表，以及 AkShare/百度股市通 2023 年以来 A 股停复牌提醒。
- `valuation_daily/`：每日指标 2000-2026 年度 Parquet，按 T 日 16:00 可见处理。
- `benchmarks/`：内部全市场代理 benchmark + AkShare 中证指数沪深300/中证500/中证1000日频 benchmark。
- `reference_rates/`：固定 CNY 无风险利率 fallback + AkShare 中国国债 2Y/5Y/10Y/30Y 收益率 + Shibor 实际序列。
- `processed_inventory/`：旧 `processed` 产物盘点，用于判断可复用性。
- `schemas/`：字段登记和质量规则。
- `configs/retention_policy.yaml`：派生产物、缓存、临时解压和告警归档策略；原始数据不删除。
- `features/market_daily_v1`、`labels/forward_returns_v1`：R7 已生成 market-only 日频特征和 forward return 标签面板，各 15,420,654 行，正式 S1 训练前仍需 walk-forward calendar、holdout log 和实验登记。
- `corporate_actions/`：R7 AkShare/Sina/Eastmoney 公司行为 sanity reference，不是完整官方公司行为主表。

## 使用建议

1. 回测成交价只使用 `prices_daily_unadjusted` 的未复权 OHLCV。
2. 动量、收益标签和绩效统计优先使用 `prices_daily_returns.return_adjusted_pit`。
3. `return_raw` 只用于检查未复权价格跳变和除权除息影响，不作为最终 alpha 标签。
4. 日频字段默认 T 日盘后可见，T+1 执行；使用前检查 `available_at <= decision_time`。
5. 当前股票列表不是 PIT 历史 universe，长期回测必须使用 `equity_master` 中从日 K ZIP 补入的历史证券。
6. 交易日历含未来开市日不代表行情已落地，需结合 `calendar.is_data_available` 和日 K 最大日期。
7. `valuation_daily` 中的估值和股本字段默认 T 日盘后可见，不能用于 T 日开盘前决策。
8. `valuation_daily` 中市值、股本、换手率可先作为市场可得慢变量；PE/PB/PS/TTM 等财报派生字段仍需公告日和供应商计算时点 PIT 审计。
9. 因子研究和执行回测必须拆分 `research_observable_universe`、`entry_eligible_universe` 和 `execution_accounting_universe`；当前 `universe_daily.in_factor_research_universe` 是保守 close-based 因子 universe，不能覆盖全部风险样本研究。
10. `prices_daily_unadjusted`、`prices_daily_returns`、`valuation_daily` 和 `security_master.equity_master` 已在 R7 补齐表级或字段级 source/time/status 字段；后续重建后必须复跑 `source_status_audit_r7.json` 或等价审计。

## 2026-04-29 P1 优化补充

- 新增 `D:\data\scripts\warehouse\build_valuation_daily.py`，用 6 worker 按年份并行构建每日指标。
- `valuation_daily` 已生成 27 个年度分区、16,642,794 行，覆盖 2000-01-04 至 2026-04-27。
- 新增 `D:\data\scripts\warehouse\enhance_warehouse_metadata.py`，补齐证券状态推断、复权因子滞后影响报告、目录状态、质量告警和轻量增量计划。
- `security_master/equity_master` 已增加 `is_delisted`、`listing_status_inferred`、`last_bar_staleness_days`；这些字段是工程推断，不是交易所官方退市公告。
- `calendar/stamp_tax_history.csv` 和 `calendar/cost_model.csv` 已补充历史印花税与佣金研究假设；佣金不是统一税率，回测前可按实际账户覆盖。
- `leakage_check.py` 已支持多进程分区检查，并纳入 `valuation_daily`。

## 2026-04-29 三方审议第二轮优化

- 新增 `D:\data\scripts\warehouse\apply_review_consensus_improvements.py`，以年度分区为单位并行处理，默认 6 worker，并限制 BLAS/Arrow 内部线程避免过度抢占 CPU。
- `benchmarks/benchmark_returns.parquet` 已生成 14,976 行，包含：
  - `CN_A_ALL_EQW_PROXY`：全 A 可得收益等权代理。
  - `CN_A_ALL_MV_WEIGHTED_PROXY`：2000 年以来全 A 上一交易日总市值加权代理。
- 第二轮审议指出旧 `CN_A_ALL_AMOUNT_WEIGHTED_PROXY` 使用同日成交额加权，会产生非可投资的爆炸指数；该默认基准已移除，详见 `audit_reports/benchmark_sanity_report.md`。
- `reference_rates/reference_rates.parquet` 已生成 8,629 行，覆盖 1990-12-19 至 2026-04-27，固定年化 1.5% 研究假设。
- `calendar/trading_rules.csv` 已结构化补充科创板、创业板注册制后、北交所上市前 5 个交易日不设涨跌幅限制。
- `calendar/cost_model.csv` 已将 `transfer_fee` 从 0 升级为 0.001% 双向研究假设。
- `audit_reports/valuation_return_key_diff_summary.csv` 显示 2000-2026 全量对齐下，估值表 extra 5,562 个 key，missing 146,208 个 key；报告原文的 241 行差异只对应局部年份，不适合作为全量结论。
- `audit_reports/suspension_volume_coverage_summary.csv` 显示当前日 K 没有显式 `volume == 0` 停牌 bar；构建脚本没有过滤零成交行，因此缺失停牌 bar 更可能来自源数据表示。
- `audit_reports/suspension_missing_bar_summary.csv` 已按交易日历和证券首末 bar 统计潜在停牌/无成交/源数据缺口：缺失 bar 577,897 行，不合成写入价格主表。
- `schemas/schema_registry.csv` 已补全核心表字段登记：`valuation_daily` 27 列、`calendar.trading_rules` 12 列、`benchmarks.benchmark_returns` 16 列。
- `leakage_check.py` 已纳入 `benchmarks` 和 `reference_rates`，并检查 `benchmark_id/trade_date`、`rate_id/trade_date` 重复键。

## 2026-04-29 三方审议第三轮优化

- 新增 `D:\data\scripts\warehouse\build_tradability_daily.py`，按年度分区多进程构建逐日可交易性伴生表，默认 6 worker，并限制 BLAS/Arrow 内部线程避免过度抢占 CPU。
- `tradability_daily` 已生成 37 个年度分区、18,177,689 行：
  - `bar_present_rows=17,599,789`，与未复权价格主表一致。
  - `is_suspended_inferred=True` 577,900 行。
  - `not_tradable_bar_quality_rows=232`。
  - `calendar_gap_price_bar_rows=3`，为历史价格 bar 存在但交易日历未覆盖的边界行。
- `suspension_events/inferred_suspension_events.parquet` 已生成 75,630 个推断事件，覆盖 3,455 只证券、577,900 个交易日。
- `schemas/schema_registry.csv` 已增至 177 行，新增 `tradability_daily` 23 列和 `suspension_events.inferred_suspension_events` 10 列。
- `leakage_check.py` 已纳入 `tradability_daily` 的时点与重复键检查。
- 所有停牌标记均为工程推断，不等同交易所官方停牌公告；后续仍应接入官方停牌/复牌事件源做校验。

## 2026-04-29 三方审议第四轮优化

- 新增 `D:\data\scripts\warehouse\apply_round4_consensus_improvements.py`，用 6 worker 并行验证 `tradability_daily` 分区，并限制 BLAS/Arrow 内部线程避免过度抢占 CPU。
- 新增 `industry_classification/current_industry_snapshot.*`：5,834 行，行业非空 5,488 行，缺失 346 行；该表是当前快照、非 PIT 历史行业分类。
- 增强 `suspension_events/inferred_suspension_events.*`：事件表增至 16 列，补充 `event_length_bucket`、`event_type_inferred`、`tradability_constraint_confidence`、`official_suspension_validation_status` 等字段。
- 新增 `audit_reports/suspension_inference_validation_report.md`：37 个 `tradability_daily` 分区、18,177,689 行、577,900 个推断停牌行验证通过；`is_suspended_inferred=True` 且 `bar_present=True` 为 0，且 `is_tradable=True` 为 0。
- 新增 `audit_reports/round4_source_gap_report.md`：本地未发现可靠官方指数价格、真实 reference rate 或官方停牌/复牌公告源；行业源仅为当前快照。
- `schemas/schema_registry.csv` 已增至 201 行，新增 `industry_classification.current_industry_snapshot` 18 列，并将增强后的 `suspension_events.inferred_suspension_events` 更新为 16 列。
- `leakage_check.py` 已纳入 `suspension_events` 和 `industry_classification` 的时点与重复键检查。

## 2026-04-29 三方审议第五轮 AkShare 接入

- 新增 `D:\data\scripts\warehouse\apply_round5_akshare_sources.py`，用 6 worker 接入 AkShare 外部源，并限制 BLAS/Arrow 内部线程避免过度抢占 CPU。
- AkShare 已在本地 `ptorch` 环境安装，版本 1.18.57；目标接口存在，无需额外安装。
- `benchmarks/benchmark_returns.parquet` 已追加官方中证指数：
  - `CSI_000300_OFFICIAL_AKSHARE`、`CSI_000905_OFFICIAL_AKSHARE`、`CSI_000852_OFFICIAL_AKSHARE`。
  - benchmark 总行数增至 31,229 行。
- `reference_rates/reference_rates.parquet` 已追加 AkShare 中国国债收益率：
  - `CNY_GOVT_BOND_2Y_AKSHARE`、`CNY_GOVT_BOND_5Y_AKSHARE`、`CNY_GOVT_BOND_10Y_AKSHARE`、`CNY_GOVT_BOND_30Y_AKSHARE`。
  - 实际利率覆盖 2002-01-04 至 2026-04-27，reference_rates 总行数增至 32,921 行。
  - 固定 1.5% 序列保留为早期缺口/测试 fallback。
- `industry_classification/industry_change_events_akshare.*` 与 `pit_industry_intervals_akshare.*` 已生成：
  - 尝试 5,834 只证券，成功 5,510 只。
  - 行业变更事件 53,925 行，PIT 行业区间 53,925 行，覆盖 12 个分类标准。
- `suspension_events/official_suspension_events_akshare.*` 已生成：
  - 2023-01-01 至 2026-04-27 共尝试 801 个交易日。
  - A 股停复牌提醒 1,447 行，覆盖 980 只证券。
  - 历史深度有限，不能替代完整交易所公告库。
- `schemas/schema_registry.csv` 已增至 259 行。
- `leakage_check.py --workers 6` 八类目录全部 PASS；其中 `benchmarks` 31,229 行、`reference_rates` 32,921 行、`suspension_events` 77,077 行、`industry_classification` 113,684 行。
- `rate_interbank` Shibor 接口在当前环境中文参数触发 KeyError；本轮采用国债收益率替代固定 reference rate，Shibor 后续单独修复。

上述 Shibor 状态已被后续 P1 data preconditions update 取代：`reference_rates` 当前为 55,964 行，含 9 条 Shibor 序列和国债收益率序列。正式引用时以 `audit_reports/p1_data_preconditions_build_summary.json`、`audit_reports/p1_data_preconditions_validation.json` 和最新 `leakage_check_report.json` 为准。

## 构建摘要

```json
{
  "mode": "full",
  "sample_stocks": 0,
  "disk_space_ok": true,
  "raw_manifest_files": 74490,
  "daily_summary": {
    "processed_stock_files": 5834,
    "sample_mode": false,
    "factor_after_last_bar_assets": 255,
    "factor_duplicate_rows_dropped": 4468,
    "price_rows_by_year": {
      "1991": 2553,
      "1992": 7507,
      "1993": 25591,
      "1994": 64770,
      "1995": 73001,
      "1996": 94358,
      "1997": 153166,
      "1998": 188859,
      "1999": 206510,
      "2000": 230153,
      "2001": 259861,
      "2002": 269651,
      "2003": 290284,
      "2004": 312837,
      "2005": 313904,
      "2006": 287666,
      "2007": 323133,
      "2008": 360090,
      "2009": 375067,
      "2010": 431327,
      "2011": 511273,
      "2012": 565436,
      "2013": 563943,
      "2014": 569948,
      "2015": 569688,
      "2016": 641304,
      "2017": 743002,
      "2018": 816745,
      "2019": 884623,
      "2020": 949337,
      "2021": 1072907,
      "2022": 1170796,
      "2023": 1258260,
      "2024": 1293409,
      "2025": 1313629,
      "2026": 405167,
      "1990": 34
    },
    "return_rows_by_year": {
      "1991": 2553,
      "1992": 7507,
      "1993": 25591,
      "1994": 64770,
      "1995": 73001,
      "1996": 94358,
      "1997": 153166,
      "1998": 188859,
      "1999": 206510,
      "2000": 230153,
      "2001": 259861,
      "2002": 269651,
      "2003": 290284,
      "2004": 312837,
      "2005": 313904,
      "2006": 287666,
      "2007": 323133,
      "2008": 360090,
      "2009": 375067,
      "2010": 431327,
      "2011": 511273,
      "2012": 565436,
      "2013": 563943,
      "2014": 569948,
      "2015": 569688,
      "2016": 641304,
      "2017": 743002,
      "2018": 816745,
      "2019": 884623,
      "2020": 949337,
      "2021": 1072907,
      "2022": 1170796,
      "2023": 1258260,
      "2024": 1293409,
      "2025": 1313629,
      "2026": 405167,
      "1990": 34
    },
    "min_trade_date": "1990-12-19",
    "max_trade_date": "2026-04-27"
  },
  "calendar_rows": 13162,
  "processed_inventory_files": 52,
  "schema_registry_rows": 259
}
```

## P1 data preconditions update (2026-04-29)

新增脚本：`D:\data\scripts\warehouse\apply_p1_data_preconditions.py`。

新增/增强产物：

- `reference_rates/reference_rates.parquet`：总行数 55,964，新增 Shibor 9 条序列、23,043 行。隔夜 Eastmoney/AkShare 序列覆盖 2006-10-08 至 2026-04-27；金十/AkShare 多期限 Shibor 覆盖 2015-05-08 至 2026-04-27。
- `risk_warning_events/`：深交所简称变更事件和当前风险警示快照，共 13,142 行。深市带日期 ST/摘帽摘星事件可作 PIT 输入；沪/北历史 ST 仍缺官方带日期源。
- `risk_warning_daily/`：37 个年度分区、8,973,264 行，其中风险警示日 412,842 行。
- `tradability_daily_enriched/`：37 个年度分区、18,177,689 行，补充板块、上市交易日年龄、涨跌停幅度、涨跌停触及、买卖阻断和风险警示来源状态。
- `universe_daily/`：37 个年度分区、18,177,689 行；基础可交易 universe 17,181,250 行，默认因子研究 universe 16,586,748 行。
- `exchange_calendar/exchange_trading_calendar.parquet`：39,486 行，按 SH/SZ/BJ 复制统一 A 股交易日历；Sina 市场级日历校验至 2026-04-27 差异为 0，但交易所级历史差异未独立验证。
- `trading_costs/equity_cost_history.parquet`：23 行；印花税为官方/高置信历史，佣金、过户费、规费和滑点仍为研究假设。
- `index_membership/`：沪深300、中证500、中证1000当前成分和最新月末权重快照各 1,800 行；不是历史 PIT 成分权重。

验证：

- `leakage_check.py --workers 6` 已扩展到 15 类目录，全部 PASS。
- `audit_reports/p1_data_preconditions_validation.json` PASS：行数对齐、可交易约束、风险警示日表、指数权重、Shibor 覆盖、交易所日历唯一性和成本源分层均通过。

剩余缺口和状态分层：

- 单一事实源：当前 `warehouse_build_manifest.json` 已在策略 Git 项目中建立为依据文档镜像；仓库侧如果重建，应由构建脚本生成同名 manifest，并用它派生 STATUS 和目录状态，避免手工状态文件漂移。
- `available_now`：日 K、PIT adjusted return、tradability/universe、benchmark、reference rates、PIT 行业、估值里的市值/换手等市场慢变量、R7 feature/label panel 和核心 source status 字段可用于 market-only S1 研究准备；仍需引用 manifest/hash 并完成 walk-forward/holdout 实验登记。
- `missing`：`walk_forward_calendar_v1`、`holdout_access_log.tsv`、测试族台账和完整官方/授权公司行为主表仍未生成。
- `blocked_by_source_gap`：沪/北历史 ST、摘帽/摘星、完整交易所官方停复牌历史、历史 PIT 指数成分/权重、独立公司行为/除权除息/分红送配主表仍缺官方、授权或可靠历史源。
- `candidate_etl`：融资融券、北向资金、限售解禁、ETF flow、股指期货 basis/OI、市场宽度、分钟/集合竞价、财报披露、股东户数、质押、龙虎榜、大宗交易和新闻公告只登记为候选源；未入仓、未 PIT 审计前不得进入官方 S1 keep。
- 手工状态文件：`reference_rates/STATUS.md`、`benchmarks/STATUS.md` 和 `audit_reports/warehouse_directory_status.csv` 可能滞后于 P1 更新；正式实验引用 Git 侧 manifest、leakage check 和 P1 validation，不以这些手工状态文件为单一事实源。
- 交易所级日历当前为统一 A 股日历代理，不是三所各自官方历史日历。
- `return_adjusted_pit` 可作为 adjusted-return proxy；在公司行为主表和 total-return audit 未完成前，不能宣称完整 total-return accounting 闭环。

## R7 feature-label panel and source status update (2026-04-30)

新增脚本：`D:\data\scripts\warehouse\apply_r7_feature_label_panel.py`。

新增/增强产物：

- `features/market_daily_v1/`：22 个年度分区，15,420,654 行，覆盖 2005-2026；包含 market-only 日频特征、trailing return/volatility/ADV、估值市场慢变量 mask/ffill、tradability/universe、benchmark 和 PIT 申万行业字段。
- `labels/forward_returns_v1/`：22 个年度分区，15,420,654 行；包含 1/5/10/20 日 forward adjusted return、全 A 等权代理超额、rank 和 top-decile 标签。
- `audit_reports/feature_label_panel_v1_manifest.json`：记录 feature/label parquet 文件 hash、行数和审计 hash。
- `audit_reports/pit_feature_audit_market_daily_v1.json`：PIT feature audit PASS；财报依赖估值字段未进入 market-only 面板。
- `audit_reports/label_audit_forward_returns_v1.json`：label audit PASS；所有成熟标签满足 label end date 晚于 feature decision time。
- `audit_reports/source_status_audit_r7.json`：核心表 source/time/status 字段审计 PASS。
- `schemas/valuation_field_pit_tier_registry.csv`：把 `valuation_daily` 字段拆分为 market-derived PIT candidate 和 financial-statement-dependent unverified PIT。
- `corporate_actions/`：AkShare/Sina 历史分红摘要 5,675 行和 Eastmoney 2023 年报分红送配样本 3,859 行。
- `audit_reports/corporate_action_adjustment_sanity_report.json`：adjusted-vs-raw sanity check；1990-2026 共 106,923 行 adjustment event-like 样本。该审计不等于完整 total-return accounting。
- 根目录 `warehouse_build_manifest.json`：现在由 R7 脚本生成，并已同步到策略 Git 项目。

验证：

- `leakage_check.py --workers 6` 已扩展到 17 类目录，全部 PASS；新增覆盖 `features`、`labels` 和 `corporate_actions`。
- `features/market_daily_v1` 与 `labels/forward_returns_v1` 行数一致。

剩余阻塞：

- 官方 S1 训练仍需先固化 `walk_forward_calendar_v1`、`holdout_access_log.tsv`、测试族台账和实验登记。
- 完整官方或授权公司行为主表仍缺；当前只允许声明 adjusted-return proxy 和 sanity check。
