# 外部数据获取与审计 — 最终汇总文档（v3 修正版）

**项目**: quant-strategy-study-plan  
**Run ID**: 20260501  
**日期**: 2026-05-01  
**状态**: ⚠️ 外部抓取与初步审计完成，仍为 candidate/raw 数据包  

> **⚠️ 重要声明**：本批数据不可直接用于策略回测。当前状态为 `source_registration_or_candidate_audit_only`。在完成统一 schema、行级 PIT 字段、后验字段隔离、覆盖率审计和交易日历校验前，不进入 official S1 回测、warehouse available_now、holdout 终验或对外绩效叙述。

---

## 一、审计修正说明

本版本修正了前两版（FINAL_AUDIT_REPORT.md 和 FULL_SUMMARY.md v2）的以下问题：

| 问题 | 修正 |
|---|---|
| "PIT PASS / 可直接用于回测" 结论过强 | 改为 `candidate_audit_only`，按 pit_status 逐数据集标注 |
| 后验字段未完全隔离 | 新增龙虎榜后验字段（上榜后1/2/5/10日） |
| 统计口径混用 raw/staging/最佳版本 | 分离 4 套口径：physical files / candidate datasets / best staging / raw evidence |
| 路径不可直接解析 | 新增 data_manifest_v2.csv 含精确物理路径 |
| GMSL 口径混用 | 统一使用 mimo staging parquet（23个），标记为 stress_report_candidate |
| 停复牌 raw 有未来日期和重复键 | 标记为 candidate_raw_blocked，需重建 staging |
| FINAL_AUDIT_REPORT.md 口径更激进 | 本文档为唯一权威汇总，FINAL_AUDIT_REPORT.md 废弃 |
| 文件结构引用不存在文件 | 移除 EXTERNAL_DATA_REQUIREMENTS.md 引用 |
| review 数据质量被高估 | 整体降级为 source_probe_only |

---

## 二、四套统计口径

### 2.1 Physical Files（磁盘文件）

| worker | layer | files | rows |
|---|---|---:|---:|
| deepseek | raw | 15 | 194,455 |
| deepseek | staging | 7 | 44,187 |
| coder | raw | 21 | 103,531 |
| coder | staging | 6 | 917 |
| mimo | raw | 30 | 161,751 |
| mimo | staging | 23 | 142,924 |
| review | raw | 15 | 8,263 |
| review | staging | 12 | 8,253 |
| **合计** | | **129** | **664,281** |

### 2.2 Candidate Datasets（逻辑数据集）

经去重、版本选择和状态标注后：

| pit_status | datasets | rows |
|---|---:|---:|
| candidate_staging_pit_fields_present | 1 | 5,000 |
| candidate_staging_needs_pit | 8 | 23,640 |
| candidate_partial_window | 3 | 18,000 |
| candidate_snapshot_only | 1 | 300 |
| candidate_raw_needs_pit | 11 | 84,612 |
| candidate_raw_blocked | 1 | 127,114 |
| stress_report_candidate | 24 | 0 (parquet) |
| reference_only | 5 | 5,719 |
| raw_evidence_only | 1 | 6,000 |
| unusable | 2 | 81 |
| fetch_empty_or_failed | 2 | 0 |
| **合计** | **59** | **~270,466** + parquet |

### 2.3 Best Candidate Staging（满足基本 schema 的可候选数据集）

仅 `candidate_staging_pit_fields_present` 和 `candidate_staging_needs_pit`：

| 数据集 | 行数 | PIT | 说明 |
|---|---:|---|---|
| 停复牌(staging) | 5,000 | ✅ 有PIT字段 | 仅1999-2001早期窗口 |
| 历史ST/更名 | 10,000 | ⚠️ 需补PIT | key重复;公告日缺失 |
| 沪深300成分 | 6,000 | ⚠️ 需补PIT | 仅2025-2026截面 |
| 中证500成分 | 6,000 | ⚠️ 需补PIT | 仅2025-2026截面 |
| 中证1000成分 | 6,000 | ⚠️ 需补PIT | 仅2025-2026截面 |
| 股票基础信息 | 5,512 | ⚠️ 需补PIT | delist_date全空 |
| 分红累计统计 | 5,675 | reference | 非逐笔事件流 |
| **合计** | **44,187** | | |

### 2.4 Raw Evidence（仅作原始证据的文件）

包括所有 `raw_candidate`、`raw_evidence`、`stress_report_candidate` 等，不计入回测可用数据。

---

## 三、数据集状态清单

### 3.1 P0 阻塞数据

| # | 数据集 | 状态 | 行数 | 阻塞问题 |
|---|---|---|---:|---|
| 1 | 停复牌(raw) | candidate_raw_blocked | 127,114 | 缺PIT字段;未来日期38行;主键重复82行 |
| 2 | 停复牌(staging) | candidate_staging_pit_fields_present | 5,000 | 仅1999-2001,不是完整历史 |
| 3 | 历史ST/更名 | candidate_staging_needs_pit | 10,000 | key重复3758行;公告日缺失 |
| 4 | 沪深300成分 | candidate_partial_window | 6,000 | 仅20个月度截面 |
| 5 | 中证500成分 | candidate_partial_window | 6,000 | 仅12个月度截面 |
| 6 | 中证1000成分 | candidate_partial_window | 6,000 | 仅6个月度截面 |
| 7 | 股票基础信息 | candidate_staging_needs_pit | 5,512 | delist_date全空 |
| 8 | 分红累计统计 | reference_only | 5,675 | 非逐笔事件流 |
| 9 | 沪深300当前成分 | candidate_snapshot_only | 300 | 无移除记录,幸存者偏差 |
| 10 | 沪深300日线 | candidate_raw_needs_pit | 5,178 | 缺available_at/decision_time |
| 11 | 中证500日线 | candidate_raw_needs_pit | 5,178 | 同上 |
| 12 | 中证1000日线 | candidate_raw_needs_pit | 5,178 | 同上 |

### 3.2 P1 风控执行数据

| # | 数据集 | 状态 | 行数 | 阻塞问题 |
|---|---|---|---:|---|
| 13 | 融资融券 | candidate_raw_needs_pit | 8,600 | 仅2025-2026采样,非全历史 |
| 14 | 北向资金 | candidate_raw_needs_pit | 1,787 | 仅2025-2026采样 |
| 15 | 限售解禁(AkShare) | candidate_raw_needs_pit | 23,149 | 后验字段需禁用 |
| 16 | 限售解禁(Tushare) | raw_evidence_only | 6,000 | 全部为未来解禁计划 |
| 17 | 涨跌停价格 | candidate_raw_needs_pit | 15,140 | 仅2026采样 |
| 18 | 龙虎榜(Tushare) | candidate_raw_needs_pit | 177 | 仅2026采样 |
| 19 | 股指期货 | candidate_raw_needs_pit | 18,990 | 覆盖较好但缺PIT字段 |
| 20 | 涨停板池 | candidate_raw_needs_pit | 1,055 | 仅近1个月 |
| 21 | 跌停板池 | candidate_raw_needs_pit | 180 | 仅近1个月 |

### 3.3 P1.5 GMSL外生冲击

全部标记为 **stress_report_candidate**，不得用于 alpha、选模、阈值或 tighten-only。

| 类别 | 系列数 | 存储格式 | 状态 |
|---|---:|---|---|
| 能源 | 3 | staging parquet | stress_report_candidate |
| FX | 2 | staging parquet | stress_report_candidate |
| 利率 | 4 | staging parquet | stress_report_candidate |
| 波动率 | 5 | staging parquet | stress_report_candidate |
| 商品 | 7 | staging parquet | stress_report_candidate |
| 股指 | 2 | staging parquet | stress_report_candidate |
| **合计** | **23** | | |

需复核：海外 session cutoff、source_status、license/vendor/hash。

### 3.4 P2 财报事件

整体降级为 **source_probe_only / reference_only**。

| # | 数据集 | 状态 | 行数 | 问题 |
|---|---|---|---:|---|
| 22 | 龙虎榜(AkShare) | candidate_staging_needs_pit | 6,562 | 后验字段需禁用;asset_id疑似映射错误 |
| 23 | 股东户数 | candidate_staging_needs_pit | 889 | 缺available_at/decision_time |
| 24 | CNINFO评级 | candidate_staging_needs_pit | 391 | 核心字段全空;主键重复 |
| 25 | 资产负债表 | candidate_staging_needs_pit | 119 | 仅000001.SZ |
| 26 | 利润表 | candidate_staging_needs_pit | 122 | 仅000001.SZ |
| 27 | 分钟数据 | unusable | 78 | SSL阻断;单股;集合竞价空 |
| 28 | 股东增减持 | candidate_staging_needs_pit | 45 | 样本极少 |
| 29-32 | 新闻类(4个) | reference_only | 44 | 仅smoke test |
| 33 | 同花顺评级 | unusable | 3 | 仅3行 |
| 34-35 | ETF/RV分钟 | fetch_empty_or_failed | 0 | 空文件 |

---

## 四、后验字段黑名单

以下字段已确认为后验，必须在特征构建阶段强制禁用：

| 数据集 | 后验字段 | 来源 |
|---|---|---|
| 限售解禁(AkShare) | `解禁前20日涨跌幅`、`解禁后20日涨跌幅` | coder/raw |
| 龙虎榜(AkShare) | `上榜后1日`、`上榜后2日`、`上榜后5日`、`上榜后10日` | review/staging |

---

## 五、指数成分PIT数据缺口

| 来源 | 覆盖 | 问题 |
|---|---|---|
| Tushare index_weight | 仅2025-2026 | 更早年份返回0行 |
| AkShare index_stock_cons | 当前快照+纳入日期 | 无移除记录,幸存者偏差 |
| 中证官网 | 不可访问 | 403/404/SSL错误 |

**解决方案**：注册聚宽(免费)获取完整历史PIT指数成分。

---

## 六、产出文件清单

```
external_data_runs/20260501/
├── FULL_SUMMARY.md                    ← 本文档（v3修正版，唯一权威）
├── INDEPENDENT_DATA_AUDIT_REPORT_20260501.md  ← 独立审计报告
├── data_manifest_v2.csv               ← 对账后数据集清单（59个）
├── data_inventory_detailed.csv        ← 详细对账清单
├── FIELD_PROTOCOL.md                  ← 字段协议
│
├── deepseek/
│   ├── staging/  (7 CSV, 44,187行)
│   ├── raw/      (15 CSV, 194,455行)
│   └── audit_reports/ + registry_patches/
│
├── coder/
│   ├── staging/  (6 CSV + 7 parquet, 917+989行)
│   ├── raw/      (21 CSV, 103,531行)
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
└── build_manifest_v2.py + inventory.py + reconcile.py
```

---

## 七、Git提交记录

| Commit | 内容 |
|---|---|
| c38396d | EXTERNAL_DATA_REQUIREMENTS.md |
| 871be72 | FINAL_AUDIT_REPORT.md（已废弃，口径过激） |
| bd02301 | FULL_SUMMARY.md v2（已修正） |
| d8f1402 | FULL_SUMMARY.md v2 对账版 |
| 本文档 | FULL_SUMMARY.md v3（待推送） |

---

## 八、下一步行动

### 阻塞项

| 行动 | 说明 | 优先级 |
|---|---|---|
| 注册聚宽 | 补充完整历史PIT指数成分 | P0 |
| 停复牌重建staging | 过滤未来日期、去重、补PIT字段 | P0 |
| ST/更名去重 | 处理3758行key重复,补公告日 | P0 |

### 非阻塞项

| 行动 | 说明 | 优先级 |
|---|---|---|
| staging补PIT字段 | 所有candidate_staging_needs_pit数据集补available_at/decision_time | P1 |
| 融资融券全历史 | 当前仅2025-2026采样 | P1 |
| 北向资金全历史 | 当前仅2025-2026采样 | P1 |
| 涨跌停全历史 | 当前仅2026采样 | P1 |
| GMSL session cutoff复核 | 海外源UTC→A股16:00判定 | P1 |
| review数据质量修复 | LHB asset_id映射;基本面单股扩展 | P2 |

---

## 九、最低通过条件

本批数据进入正式回测前必须满足：

1. 全部候选表完成统一 schema（含 source_name/vendor/license_status/source_hash/ingested_at/time_zone/session_cutoff_rule）
2. 行级 available_at/decision_time/source_status/source_hash 完整
3. 后验字段 blacklist 生效
4. 覆盖率、重复键、异常值、未来日期、交易日历和海外 session cutoff 审计 PASS
5. 每个数据集有清晰状态：full history / partial history / sample / snapshot / unusable
