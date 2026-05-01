# 外部数据获取与审计 — 最终汇总文档（v4 审计封口版）

**项目**: quant-strategy-study-plan  
**Run ID**: 20260501  
**日期**: 2026-05-02  
**状态**: ⚠️ 外部抓取与审计完成，仍为 candidate/raw 数据包  

> **⚠️ 重要声明**：本批数据不可直接用于策略回测。当前状态为 `source_registration_or_candidate_audit_only`。在完成统一 schema、行级 PIT 字段、后验字段隔离、覆盖率审计和交易日历校验前，不进入 official S1 回测、warehouse `available_now`、holdout 终验或对外绩效叙述。

---

## 一、v4 修正说明

本版本修正了 V2 审计报告指出的所有 P0 问题：

| 审计问题 | 修正 |
|---|---|
| P0-1: GMSL manifest 路径错误，24条全部 exists=False | 重建为23条，使用实际路径 `mimo/staging/{id}/{id}.parquet`，pyarrow 统计行数 |
| P0-2: Best Candidate Staging 口径错误 | 严格按 manifest pit_status 筛选，拆分为6个状态层 |
| P0-3: suspend_d_staging 状态过强 | 降为 `candidate_staging_partial_pit_no_lineage` |
| P0-4: namechange 状态过宽 | Tushare 重拉去重后 3,731行，ann_date 100%，状态改为 `candidate_staging_ready_pit_no_lineage` |
| P1-1: Physical Files 表不可复现 | 改为目录扫描口径（136文件，667,196行） |
| P1-2: data_inventory_detailed.csv 旧口径 | 标记为 legacy |
| P1-3: FIELD_PROTOCOL 缺 source_status | 已补充 |
| P1-5: 后验字段 blacklist 不完整 | 新增英文字段名 |
| P1-6: P1 staging 样本易被误用 | 标记为 `sample_probe_only` |
| P2-1: review 降级口径与状态表冲突 | 统一为 source_probe_only |
| P2-2: event_lhb 映射错误 | 降为 `blocked_mapping_error` |
| P2-3: analyst/fundamental 不可作研究候选 | 降为 `source_probe_only` |
| P2-4: 文档小问题 | 删除"待推送"，改为"交接优先引用摘要" |

---

## 二、Physical Files 统计（目录扫描口径）

基于 `physical_files_scan.csv` 实际扫描：

| worker | layer | files | rows |
|---|---|---:|---:|
| deepseek | raw | 15 | 194,455 |
| deepseek | staging | 8 | 46,119 |
| coder | raw | 20 | 103,525 |
| coder | staging | 13 | 1,906 |
| mimo | raw | 30 | 161,751 |
| mimo | staging | 23 | 142,924 |
| review | raw | 15 | 8,263 |
| review | staging | 12 | 8,253 |
| **合计** | | **136** | **667,196** |

> deepseek/staging 含 namechange 修复后文件（3,731行）。

---

## 三、GMSL 外生冲击（23 parquet，142,924行）

全部标记为 **stress_report_candidate**，不得用于 alpha、选模、阈值或 tighten-only。

| 数据集 | 路径 | 行数 |
|---|---|---:|
| brent_crude | mimo/staging/brent_crude/brent_crude.parquet | 10,159 |
| wti_crude | mimo/staging/wti_crude/wti_crude.parquet | 10,518 |
| sc_crude | mimo/staging/sc_crude/sc_crude.parquet | 1,964 |
| dxy | mimo/staging/dxy/dxy.parquet | 5,300 |
| usdcny_akshare | mimo/staging/usdcny_akshare/usdcny_akshare.parquet | 1,731 |
| usdcny_fred | mimo/staging/usdcny_fred/usdcny_fred.parquet | 11,821 |
| fed_funds | mimo/staging/fed_funds/fed_funds.parquet | 861 |
| ust_10y_fred | mimo/staging/ust_10y_fred/ust_10y_fred.parquet | 16,782 |
| ust_10y_akshare | mimo/staging/ust_10y_akshare/ust_10y_akshare.parquet | 1,689 |
| ust_2y_fred | mimo/staging/ust_2y_fred/ust_2y_fred.parquet | 13,022 |
| ust_2y_akshare | mimo/staging/ust_2y_akshare/ust_2y_akshare.parquet | 1,689 |
| ust_30y_fred | mimo/staging/ust_30y_fred/ust_30y_fred.parquet | 12,837 |
| cboe_vix | mimo/staging/cboe_vix/cboe_vix.parquet | 9,175 |
| fred_vix | mimo/staging/fred_vix/fred_vix.parquet | 9,477 |
| vix9d | mimo/staging/vix9d/vix9d.parquet | 3,853 |
| vxn | mimo/staging/vxn/vxn.parquet | 4,185 |
| gvz | mimo/staging/gvz/gvz.parquet | 4,177 |
| ovx | mimo/staging/ovx/ovx.parquet | 4,177 |
| gold_futures | mimo/staging/gold_futures/gold_futures.parquet | 4,459 |
| silver_futures | mimo/staging/silver_futures/silver_futures.parquet | 3,400 |
| copper_fred | mimo/staging/copper_fred/copper_fred.parquet | 411 |
| spx | mimo/staging/spx/spx.parquet | 5,620 |
| nasdaq | mimo/staging/nasdaq/nasdaq.parquet | 5,617 |

需复核：海外 session cutoff、source_status、license/vendor/hash。

---

## 四、数据集状态清单（Manifest v3）

共 61 个逻辑数据集。按 pit_status 分层：

### 4.1 candidate_staging_ready_pit_no_lineage（1个，3,731行）

已补 PIT 时间字段，但缺 lineage（source_name/vendor/license/source_hash/time_zone/session_cutoff_rule）。

| 数据集 | 行数 | 覆盖 | 说明 |
|---|---:|---|---|
| 历史ST/更名(namechange) | 3,731 | 2010-2026 | Tushare重拉去重，ann_date 100%，0重复 |

### 4.2 candidate_staging_partial_pit_no_lineage（1个，5,000行）

有 PIT 字段但覆盖窗口不足或 schema 不完整。

| 数据集 | 行数 | 覆盖 | 说明 |
|---|---:|---|---|
| 停复牌(staging) | 5,000 | 1999-2001 | 仅早期窗口，缺 lineage |

### 4.3 candidate_raw_needs_pit（11个，84,612行）

raw 大行数但无 PIT 字段，需重建 staging。

| 数据集 | 行数 | 覆盖 | 说明 |
|---|---:|---|---|
| 沪深300日线 | 5,178 | 2005-2026 | 缺 available_at/decision_time |
| 中证500日线 | 5,178 | 2005-2026 | 同上 |
| 中证1000日线 | 5,178 | 2005-2026 | 同上 |
| 融资融券 | 8,600 | 2025-2026 | 仅多月采样 |
| 北向资金 | 1,787 | 2025-2026 | 仅采样 |
| 涨跌停价格 | 15,140 | 2026 | 仅2026采样 |
| 龙虎榜(Tushare) | 177 | 2026 | 仅2026采样 |
| 股指期货 | 18,990 | 2019-2026 | 覆盖较好 |
| 涨停板池 | 1,055 | 2026-04~05 | 仅近1个月 |
| 跌停板池 | 180 | 2026-04~05 | 仅近1个月 |
| 限售解禁(AkShare) | 23,149 | 2010-2024 | 含后验字段 |

### 4.4 partial_effective_snapshot_no_removal_history（4个，18,300行）

仅当前快照或短窗口，无移除历史，不能构建完整 PIT universe。

| 数据集 | 行数 | 覆盖 | 说明 |
|---|---:|---|---|
| 沪深300成分 | 6,000 | 2025-2026 | 仅月度截面 |
| 中证500成分 | 6,000 | 2025-2026 | 同上 |
| 中证1000成分 | 6,000 | 2025-2026 | 同上 |
| 沪深300当前成分 | 300 | 当前快照 | 无移除记录 |

### 4.5 sample_probe_only（5个，808行）

极小样本/单日快照，仅作 smoke test。

| 数据集 | 行数 | 说明 |
|---|---:|---|
| 融资融券(staging) | 17 | 仅1个asset_id |
| 北向资金(staging) | 300 | 单日快照 |
| 股指期货(staging) | 400 | 远小于raw |
| 涨跌停(staging) | 90 | 单日,封板时间异常 |
| 市场宽度(staging) | 1 | 单日 |

### 4.6 source_probe_only（5个，1,566行）

数据存在但质量/覆盖不足以作研究候选。

| 数据集 | 行数 | 说明 |
|---|---:|---|
| 股东户数 | 889 | 缺PIT字段 |
| CNINFO评级 | 391 | 核心字段全空,主键重复 |
| 资产负债表 | 119 | 仅000001.SZ |
| 利润表 | 122 | 仅000001.SZ |
| 股东增减持 | 45 | 样本极少 |

### 4.7 其他受限状态

| 数据集 | 行数 | 状态 | 说明 |
|---|---:|---|---|
| 停复牌(raw) | 127,114 | candidate_raw_blocked | 未来日期+重复键+缺PIT |
| 股票基础信息 | 5,512 | reference_only_universe_metadata_blocked | delist_date全空 |
| 分红累计统计 | 5,675 | reference_only | 非逐笔事件流 |
| 限售解禁(Tushare) | 6,000 | raw_evidence_only | 全部为未来解禁计划 |
| 龙虎榜(AkShare) | 6,562 | blocked_mapping_error | asset_id映射错误+后验字段 |
| 分钟数据 | 78 | unusable | SSL阻断 |
| 同花顺评级 | 3 | unusable | 仅3行 |
| 新闻类(4个) | 44 | reference_only | 仅smoke test |
| ETF/RV分钟 | 0 | fetch_empty_or_failed | 空文件 |

---

## 五、后验字段黑名单

| 数据集 | 后验字段（中文+英文） |
|---|---|
| 限售解禁(AkShare) | `解禁前20日涨跌幅`、`解禁后20日涨跌幅`、`pre_20d_return`、`post_20d_return` |
| 龙虎榜(AkShare) | `上榜后1日`、`上榜后2日`、`上榜后5日`、`上榜后10日`、`post_1d`、`post_2d`、`post_5d`、`post_10d` |

> `pre_20d_return` 如以 announcement_date 为锚点，也可能是后验，需在 feature build 阶段验证。

---

## 六、指数成分PIT数据缺口

| 来源 | 覆盖 | 问题 |
|---|---|---|
| Tushare index_weight | 仅2025-2026 | 更早年份返回0行 |
| AkShare index_stock_cons | 当前快照+纳入日期 | 无移除记录,幸存者偏差 |
| 中证官网 | 不可访问 | 403/404/SSL错误 |

**解决方案**：注册聚宽(免费)获取完整历史PIT指数成分。

---

## 七、遗留文件说明

| 文件 | 状态 | 说明 |
|---|---|---|
| `data_manifest_v2.csv` | 废弃 | GMSL路径错误，exists=False |
| `data_inventory_detailed.csv` | legacy | 路径与当前磁盘不匹配 |
| `FINAL_AUDIT_REPORT.md` | 废弃 | 口径过激，本文档为权威 |
| `data_manifest_v3.csv` | 当前 | 61个数据集，全部 exists=True |
| `physical_files_scan.csv` | 当前 | 136文件目录扫描 |

---

## 八、产出文件清单

```
external_data_runs/20260501/
├── FULL_SUMMARY.md                    ← 本文档（v4，唯一权威交接摘要）
├── INDEPENDENT_DATA_AUDIT_REPORT_V2_20260501.md  ← V2审计报告
├── data_manifest_v3.csv               ← 当前 manifest（61个数据集）
├── physical_files_scan.csv            ← 目录扫描（136文件）
├── FIELD_PROTOCOL.md                  ← 字段协议（含 source_status）
│
├── deepseek/
│   ├── staging/  (8 CSV, 46,119行)  ← 含 namechange 修复版
│   ├── raw/      (15 CSV, 194,455行)
│   └── audit_reports/ + registry_patches/
│
├── coder/
│   ├── staging/  (13 files, 1,906行)
│   ├── raw/      (20 files, 103,525行)
│   └── audit_reports/ + registry_patches/
│
├── mimo/
│   ├── staging/  (23 parquet, 142,924行)
│   ├── raw/      (30 CSV, 161,751行)
│   └── audit_reports/ + registry_patches/
│
├── review/
│   ├── staging/  (12 CSV, 8,253行)
│   ├── raw/      (15 CSV, 8,263行)
│   └── audit_reports/ + registry_patches/
│
└── build_manifest_v3.py + scan_physical_files.py + reconcile.py
```

---

## 九、Git提交记录

| Commit | 内容 |
|---|---|
| c38396d | EXTERNAL_DATA_REQUIREMENTS.md |
| 871be72 | FINAL_AUDIT_REPORT.md（废弃） |
| bd02301 | FULL_SUMMARY.md v1 |
| d8f1402 | FULL_SUMMARY.md v2 对账版 |
| c542e0c | FULL_SUMMARY.md v3 + manifest v2 |
| e34c910 | ST/更名修复（3,731行） |
| 本文档 | FULL_SUMMARY.md v4（待推送） |

---

## 十、下一步行动

### 阻塞项

| 行动 | 说明 | 优先级 |
|---|---|---|
| 注册聚宽 | 补充完整历史PIT指数成分 | P0 |
| 停复牌重建staging | 过滤未来日期、去重、补PIT字段 | P0 |
| FIELD_PROTOCOL闭环 | 所有staging表补 source_status/source_hash/vendor/license/time_zone/session_cutoff_rule | P0 |

### 非阻塞项

| 行动 | 说明 | 优先级 |
|---|---|---|
| 融资融券全历史 | 当前仅2025-2026采样 | P1 |
| 北向资金全历史 | 当前仅2025-2026采样 | P1 |
| 涨跌停全历史 | 当前仅2026采样 | P1 |
| GMSL session cutoff复核 | 海外源UTC→A股16:00判定 | P1 |
| review数据质量修复 | LHB asset_id映射;基本面单股扩展 | P2 |

---

## 十一、最低通过条件

本批数据进入正式回测前必须满足：

1. 全部候选表完成统一 schema（含 source_name/vendor/license_status/source_hash/ingested_at/time_zone/session_cutoff_rule/source_status）
2. 行级 available_at/decision_time/source_status/source_hash 完整
3. 后验字段 blacklist 生效（中英文双语覆盖）
4. 覆盖率、重复键、异常值、未来日期、交易日历和海外 session cutoff 审计 PASS
5. 每个数据集有清晰状态：full history / partial history / sample / snapshot / unusable
6. manifest 所有条目 exists=True，physical_path 可直接解析
