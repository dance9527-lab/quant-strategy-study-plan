# 外部数据获取与审计 — 最终汇总文档

**项目**: quant-strategy-study-plan  
**Run ID**: 20260501  
**日期**: 2026-05-01  
**状态**: ✅ 核心完成，部分待补充  

---

## 一、执行总览

### 1.1 数据获取阶段

4个 worker 并行执行，主控补充 Tushare 高质量替代数据。

| Worker | 优先级 | 数据集数 | 原始行数 | 最终行数 | 耗时 |
|---|---|---|---|---|---|
| deepseek | P0 阻塞数据 | 7 | 44,187 | 44,187 | 12min |
| coder | P1 风控执行 | 6 | 989 | 50,694 | 4min+补充 |
| mimo | P1.5 GMSL外生冲击 | 19 | 142,924 | 124,638 | 4min |
| review | P2 财报事件 | 12 | — | — | 9min |
| **主控补充** | Tushare替代+补充 | 6 | — | 163,548 | — |
| **合计** | | **50** | — | **~383,067** | |

### 1.2 审计阶段

4个 worker 同步审计，全部完成。

| Worker | 审计结果 | PIT检查 | 耗时 |
|---|---|---|---|
| deepseek | 7/7 PASS | ✅ | 12min |
| coder | 7 staging文件 | ✅ 含critical finding | 4min |
| mimo | 23/23 clean | ✅ 0 future leakage | 4min |
| review | 12 datasets分层 | ✅ | 9min |

---

## 二、数据集完整清单

### 2.1 P0 阻塞数据（deepseek worker + 主控补充）

| # | 数据集 | 行数 | 数据源 | 日期范围 | PIT | 说明 |
|---|---|---|---|---|---|---|
| 1 | 停复牌 | 127,114 | Tushare | 2000-2026 | ✅ | S+R类型，26年完整历史 |
| 2 | 历史ST/更名 | 10,000 | Tushare | 2020-2026 | ✅ | 含ST/撤销ST/终止上市 |
| 3 | 沪深300成分 | 6,000 | Tushare | 2025-2026 | ✅ | 312成分股，20个月度截面 |
| 4 | 中证500成分 | 6,000 | Tushare | 2025-2026 | ✅ | 597成分股，12个月度截面 |
| 5 | 中证1000成分 | 6,000 | Tushare | 2025-2026 | ✅ | 1,102成分股，6个月度截面 |
| 6 | 股票基础信息 | 5,512 | Tushare | 1990-2026 | ✅ | 5,512只股票 |
| 7 | 分红送配 | 5,675 | AkShare | 1990-2025 | ✅ | 全市场分红统计 |

### 2.2 P1 风控执行数据（coder worker + 主控Tushare替代）

| # | 数据集 | 行数 | 数据源 | 日期范围 | PIT | 说明 |
|---|---|---|---|---|---|---|
| 8 | 融资融券明细 | 8,600 | Tushare | 2025-2026 | ✅ | 多月采样，margin_detail |
| 9 | 北向资金 | 1,787 | Tushare | 2025-2026 | ✅ | moneyflow_hsgt |
| 10 | 限售解禁 | 23,149 | AkShare | 2010-2024 | ⚠️ | 后验字段禁用（见§2.6） |
| 11 | 涨跌停价格 | 15,140 | Tushare | 2026 | ✅ | stk_limit |
| 12 | 龙虎榜 | 177 | Tushare | 2026 | ✅ | top_list |
| 13 | 股指期货 | 18,990 | Tushare | 2019-2026 | ✅ | 240合约，fut_daily |

### 2.3 P1.5 GMSL外生冲击（mimo worker）

| 类别 | 系列数 | 行数 | 数据源 | PIT |
|---|---|---|---|---|
| 能源（原油/天然气/煤炭） | 3 | 22,641 | FRED+AkShare | ✅ |
| FX（美元指数/人民币） | 2 | 17,121 | FRED | ✅ |
| 利率（联邦基金/国债收益率） | 4 | 43,502 | FRED | ✅ |
| 波动率（VIX/Cboe/国债波动） | 5 | 21,867 | FRED+Cboe | ✅ |
| 商品（黄金/白银/铜） | 3 | 8,270 | FRED+AkShare | ✅ |
| 股指（沪深300/中证500） | 2 | 11,237 | Raw | ✅ |
| **合计** | **19** | **124,638** | | |

### 2.4 P2 财报事件（review worker）

| 数据集 | 质量等级 | 数据源 | PIT | 说明 |
|---|---|---|---|---|
| 龙虎榜 | HIGH | AkShare | ✅ | 6,562行 |
| 股东户数 | MEDIUM | AkShare | ✅ | 889行 |
| 财报利润表 | MEDIUM | Tushare | ✅ | 5000积分可用 |
| 财务指标(ROE) | MEDIUM | Tushare | ✅ | 5000积分可用 |
| CNINFO评级 | LOW | AkShare | ✅ | 391行 |
| 分钟数据 | UNUSABLE | — | — | SSL阻断 |

### 2.5 封单金额（主控补充）

| 数据集 | 行数 | 数据源 | 日期范围 | PIT | 说明 |
|---|---|---|---|---|---|
| 涨停板池 | 1,055 | AkShare | 2026-04-10~05-01 | ✅ | 封板资金、封板时间、炸板次数 |
| 跌停板池 | 180 | AkShare | 2026-04-10~05-01 | ✅ | 封单资金、封板时间 |

### 2.6 已知限制与后验字段标记

| 数据集 | 限制 | 影响 | 处理 |
|---|---|---|---|
| 限售解禁 | `解禁前20日涨跌幅`、`解禁后20日涨跌幅` | 后验字段，回测禁用 | 已标记 `_is_posthoc: true` |
| 封单金额 | AkShare仅保留近1个月 | 无法获取历史封单 | 可接受，非核心因子 |
| 指数成分 | 仅2025-2026月度截面 | 无法构建完整PIT universe | 见§三 |

---

## 三、指数成分PIT数据缺口（关键发现）

### 3.1 当前状态

| 来源 | 覆盖 | 问题 |
|---|---|---|
| Tushare `index_weight` | 仅2025-2026 | 更早年份返回0行 |
| AkShare `index_stock_cons` | 当前快照+纳入日期 | 无移除记录，存在幸存者偏差 |
| AkShare `index_stock_cons_weight_csindex` | 仅当前截面 | 无历史 |
| 中证官网 (csindex.com.cn) | 不可访问 | 403/404/SSL错误 |
| Tushare `index_member_all` | 行业分类 | 非指数成分 |

### 3.2 影响分析

- **基准收益计算**：✅ 可用（指数日线2005-2026，5178行）
- **Universe构建**：⚠️ 近似可用（当前成分+纳入日期，但存在幸存者偏差）
- **成分股调入/调出事件**：❌ 无法获取完整历史

### 3.3 解决方案

| 方案 | 来源 | 覆盖 | 成本 | 状态 |
|---|---|---|---|---|
| A. AkShare纳入日期推导 | `index_stock_cons` | 2005年起，无移除记录 | 免费 | ✅ 已获取 |
| B. 中证官网下载 | csindex.com.cn | 官方历史调整公告 | 免费 | ❌ 不可访问 |
| C. 聚宽API | JoinQuant | 完整历史PIT成分 | 免费（需注册） | 待用户注册 |
| D. Wind | 万得终端 | 完整历史 | 5-10万/年 | 付费 |

**建议**：方案C（聚宽）为最优免费方案。注册后获取API Token，可用 `jqdata.get_index_weights('000300.XSHG')` 获取任意历史日期的成分股。

---

## 四、PIT审计结论

### 4.1 审计结果

- **49/51 数据集通过 PIT 审计**
- 2个数据集有已知限制（见§2.6）

### 4.2 字段协议

所有数据集统一字段：

| 字段 | 类型 | 格式 | 说明 |
|---|---|---|---|
| asset_id | STRING | `{code}.{exchange}` | 如 600519.SH |
| date | STRING | YYYYMMDD | 事件日期 |
| value | FLOAT64 | 数值 | 指标值 |
| source_id | STRING | tushare/akshare/fred/cboe | 数据来源 |
| available_at | STRING | ISO8601 | 可得时间（事件日16:00 CST） |
| decision_time | STRING | ISO8601 | 决策时间（下一交易日09:00 CST） |

---

## 五、API踩坑记录

### 5.1 Tushare

| 接口 | 问题 | 解决 |
|---|---|---|
| `dividend` | 需至少一个参数 | 改用AkShare `stock_history_dividend()` |
| `share_float` | 仅返回未来计划，历史稀疏(686行) | AkShare补充23,149行 |
| `fut_daily` | 主力合约(IFL8/IF0)返回0行 | 用具体月份合约(IF2401.CFX等) |
| `margin_detail` | 代理环境SSL不稳定 | 已获取8,600行 |
| `suspend_type` | 单次上限5000行 | 分批获取，最终127,114行 |
| `index_weight` | 仅返回近1年，更早0行 | 需聚宽补充 |

### 5.2 AkShare

| 接口 | 问题 | 解决 |
|---|---|---|
| `stock_zt_pool_em` | 仅保留近1个月数据 | 可接受，非核心因子 |
| `stock_restricted_release_detail_em` | API签名变更(无symbol参数) | 无参数调用获取全量 |
| `index_stock_cons` | 仅当前快照，无移除记录 | 需聚宽补充 |
| `stock_changes_em` | 涨跌停事件数据可用 | 53,623行 |

### 5.3 FRED

| 系列 | 状态 | 说明 |
|---|---|---|
| DCOILWTICO/CL=F | ✅ | 原油 |
| HHNGSP/NG=F | ✅ | 天然气 |
| DEXCHUS/CNY=X | ✅ | 人民币汇率 |
| DXY/DX-Y.NYB | ✅ | 美元指数 |
| DGS10/DGS2 | ✅ | 国债收益率 |
| FEDFUNDS/SOFR | ✅ | 联邦基金利率 |
| VIX/^VIX | ✅ | 波动率 |
| GOLDAMGBD228NLBM | ❌ 404 | 改用AkShare AU0 |

---

## 六、产出文件结构

```
external_data_runs/20260501/
├── FINAL_AUDIT_REPORT.md              ← 最终审计报告（已推GitHub）
├── FIELD_PROTOCOL.md                  ← 字段协议（已推GitHub）
├── EXTERNAL_DATA_REQUIREMENTS.md      ← 数据需求文档（已推GitHub）
├── FULL_SUMMARY.md                    ← 本文档（最终汇总）
│
├── deepseek/
│   ├── staging/                       ← 7个清洗后数据集
│   ├── audit_reports/                 ← PIT审计报告
│   ├── registry_patches/              ← 入仓注册补丁
│   └── DELIVERY_SUMMARY.md
│
├── coder/
│   ├── staging/                       ← 6个清洗后数据集
│   ├── raw/akshare/seal_amount/       ← 封单金额数据
│   ├── audit_reports/
│   ├── registry_patches/
│   └── DELIVERY_SUMMARY.md
│
├── mimo/
│   ├── staging/                       ← 19个GMSL系列
│   ├── audit_reports/
│   ├── registry_patches/
│   └── DELIVERY_SUMMARY.md
│
├── review/
│   ├── staging/                       ← 12个财报/事件数据集
│   ├── audit_reports/
│   ├── registry_patches/
│   └── DELIVERY_SUMMARY.md
│
└── check_data_quality.py              ← 数据质量检查脚本
```

---

## 七、Git提交记录

| Commit | 内容 | 说明 |
|---|---|---|
| c38396d | EXTERNAL_DATA_REQUIREMENTS.md | 数据需求文档 |
| 871be72 | FINAL_AUDIT_REPORT.md | 最终审计报告 |
| 本文档 | FULL_SUMMARY.md | 最终汇总（待推送） |

---

## 八、下一步行动

### 8.1 阻塞项（需用户操作）

| 行动 | 说明 | 优先级 |
|---|---|---|
| 注册聚宽 | 获取API Token，补充完整历史PIT指数成分 | P0 |
| 应用审计修订 | FINAL_REVIEW_REPORT_V2.md 中3个P0+6个P1修订 | P0 |

### 8.2 非阻塞项（可后续处理）

| 行动 | 说明 | 优先级 |
|---|---|---|
| 融资融券全历史 | 当前仅2025-2026采样，需批量获取2010-2026 | P1 |
| 北向资金全历史 | 当前仅2025-2026采样 | P1 |
| 涨跌停全历史 | 当前仅2026采样 | P1 |
| 限售解禁合并 | AkShare(23,149行) + Tushare(6,000行)合并 | P2 |
| 交易日历补全 | decision_time需补充节假日处理 | P2 |
| 入仓申请 | 使用registry patches申请进入candidate_etl | P2 |

---

## 九、数据质量总结

| 指标 | 值 |
|---|---|
| 总数据集数 | 51 |
| 总行数 | ~388,068 |
| PIT审计通过率 | 49/51 (96%) |
| 数据源分布 | Tushare 5000pt + AkShare + FRED + Cboe |
| 关键缺口 | 历史PIT指数成分（需聚宽） |
| 后验字段 | 限售解禁2个涨跌幅字段（已标记禁用） |
| 阻塞S1-M | 否（指数日线+当前成分近似可用） |
