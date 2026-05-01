# 外部数据获取统一字段协议

> run_id: 20260501
> 日期: 2026-05-01
> 主控: main agent

## 统一必填字段

| 字段 | 类型 | 说明 |
|---|---|---|
| source_name | string | 数据源名称（如 tushare_dividend, akshare_margin） |
| vendor | string | 数据供应商（如 tushare, akshare, wind） |
| license_status | string | public/unknown_or_internal/requires_case_by_case_audit |
| raw_code | string | 原始代码（股票代码、基金代码、合约代码等） |
| asset_id | string | 统一资产ID（映射后） |
| index_id | string | 指数ID（如 CSI300, CSI500, CSI1000） |
| fund_id | string | 基金ID |
| contract | string | 期货合约ID |
| trade_date | date | 交易日期 |
| event_time | datetime | 事件时间（精确到秒） |
| announcement_time | datetime | 公告时间 |
| available_at | datetime | 数据可见时间（PIT关键字段） |
| decision_time | datetime | 策略决策时间 |
| time_zone | string | 时区（Asia/Shanghai 或 UTC） |
| session_cutoff_rule | string | session截止规则 |
| source_hash | string | 源数据SHA256 |
| source_status | string | 数据状态（raw_candidate/staging_candidate/reference_only/blocked等） |
| ingested_at | datetime | 抓取时间 |

## PIT/available_at/decision_time 规则

1. A股日频行情: available_at = T日16:00 Asia/Shanghai后
2. 公告/事件: available_at = 公告发布时间；无时分秒时保守用公告日16:00后
3. 海外宏观: 先转UTC，再转Asia/Shanghai；晚于A股16:00顺延到下一决策日
4. 指数成分: 公告日优先；不得用当前快照倒灌历史
5. 财报/预期: 公告日优先；不得用后验重述覆盖历史

## 禁止事项

1. 不得写入 D:\data\warehouse（只交付 raw/staging/audit）
2. 不得宣称 available_now 或 official keep
3. 不得将当前快照、未来成分、未来ST、未来公告倒灌历史
4. 海外数据必须转UTC并按A股T日16:00顺延
5. 未通过PIT/available_at审计的数据只能 source_registration_or_audit_only
