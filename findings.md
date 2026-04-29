# 研究发现：策略计划审计吸收

## 2026-04-30 初始发现

- 本地 `git pull --ff-only` 首次失败：`RPC failed; curl 56 Recv failure: Connection was reset`。
- 改用 `git -c http.version=HTTP/1.1 fetch origin main --depth=1 --prune` 后仍失败：`Recv failure: Connection was reset`。
- GitHub 连接器可正常读取远端文件，因此本轮以连接器获取 `三方审计报告_20260430.md`，后续如本地 git 网络继续失败，将用 GitHub Contents API 同步远端文件。
- `三方审计报告_20260430.md` 远端 SHA：`67f17ac0c186d4183ac5798cd6c2b29264f83525`。
- 审计报告共识评分为 `6.0-6.5/10`，核心批评集中在执行可成交性、开盘冲击、因子 PIT、walk-forward 固化和过拟合审计默认化。
- 本地 schema 核验显示 `tradability_daily_enriched` 已包含 `can_buy_close_based`、`can_sell_close_based`、`buy_blocked_close_based`、`sell_blocked_close_based`、`close_at_limit_up/down`、`high_hit_limit_up`、`low_hit_limit_down`、`listing_age_trading_days`、`is_risk_warning_pit` 等字段，足够支持日频层面的涨跌停/停牌/ST/上市年龄成交过滤。
- `prices_daily_unadjusted` 已包含 `open/high/low/close/pre_close/volume/amount`，可以做开盘成交和成交额参与率的保守建模；但本地 warehouse 尚未形成可审计的集合竞价或分钟主表，因此审计提出的“三段模型”只能部分采纳：日频基线先做保守开盘冲击和容量惩罚，完整集合竞价/分钟分段模型后置到分钟表入仓后。
- `valuation_daily` 有 `available_at` 和 `decision_time`，但估值字段是否完全基于已公开财报仍需因子层 PIT 审计；应把 `pit_factor_audit.py` 或等价检查列为 S1 官方结果前置门槛。
- `leakage_check_report.json` 只证明 warehouse 层 15 类目录 `available_at <= decision_time` PASS，不能替代实验层标签、特征、切分和 early stopping 审计。审计报告这一点应采纳。
- 当前 `D:\data\scripts\warehouse` 没有独立 `pit_factor_audit.py` 或 `benchmark_audit.py`；已有 `leakage_check.py` 和 `benchmark_sanity_report.*` 可作为基础，但计划文档应新增实验层审计交付物。
- `benchmark_sanity_report.md` 已确认同日成交额加权 proxy 被移除；当前 `CN_A_ALL_MV_WEIGHTED_PROXY` 使用上一交易日 `valuation_daily.total_mv`，更适合作内部代理。官方指数仍需持续披露 source/available_at。
- Subagent 共识：PIT、涨跌停、成本、过拟合审计必须前置；`S2 完全后置` 不应机械采纳，因为最小交易约束必须进入 S1，否则会把不可交易 alpha 带入基线。
- Subagent 对文档缺口的主要发现：当前文档原先对 walk-forward 参数、S1 硬门槛、实验台账、Deflated Sharpe/holdout、连续涨跌停队列、分档滑点和风险开关 v1 写得不够具体。
- 最终裁决：S1 内置 T+1、涨跌停、停牌、ST、上市年龄、基础成本、保守滑点和日频开盘冲击；S2 仅在 S1 通过后深化容量压力、分档滑点、冲击成本和组合约束优化。
