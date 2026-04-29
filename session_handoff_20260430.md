# 新会话最小交接（2026-04-30）

## 启动顺序

1. 先读 `C:\Users\LeoShu\.codex\memories\PROFILE.md`、`C:\Users\LeoShu\.codex\memories\ACTIVE.md`。
2. 在 `D:\quantum_a0\quant-strategy-study-plan` 工作。
3. 读取本仓库：
   - `task_plan.md`
   - `findings.md`
   - `progress.md`
   - `quant_strategy_plan.md`
   - `quant_strategy_research_plan_detailed.md`
   - `validation_params.json`
   - `三方审计报告_20260430.md`

## 当前状态

- 两份策略计划已迁移到 Git 项目 `dance9527-lab/quant-strategy-study-plan`，后续以 Git 仓库版本为权威。
- `D:\data\strategy\quant_strategy_plan.md` 与 `D:\data\strategy\quant_strategy_research_plan_detailed.md` 已作为本地镜像从 Git 项目同步回写。
- 已吸收 `三方审计报告_20260430.md`：
  - 采纳：涨跌停执行、因子 PIT、walk-forward 固化、DSR/holdout、实验层审计、台账扩展。
  - 部分采纳：开盘三段模型、分红送配 P1.5、风险开关 v1、S1 完成量化门槛。
  - 不机械采纳：`S2 完全后置`。S1 内置最小交易可行性；S2 只做深度容量、分档滑点、冲击成本和组合约束优化。
  - 不作为结论采纳：DeepSeek 收益区间，只作为假设队列。
- 新增 `validation_params.json`，官方策略证据默认：
  - 5 年训练窗口。
  - 21 个交易日测试/调仓窗口。
  - `purge_days >= max(label_horizon, 20)`。
  - `embargo_days = 5`。
  - 至少 12 个 OOT step。
  - keep/晋级需要 holdout、DSR/PBO 或等价过拟合审计。

## 数据和实验边界

- Canonical 数据源仍是 `D:\data\warehouse`。
- 最近一次 warehouse `leakage_check`：`2026-04-29 10:38:49`，15 类目录 PASS。
- 当前 warehouse 支持日频研究所需核心表：价格/收益、估值、可交易性、涨跌停执行约束、风险警示、PIT 行业、benchmark、reference_rates、trading_costs。
- 必须披露缺口：沪/北历史 ST 不完整、全历史官方停复牌公告不完整、估值 2026-01-05 至 2026-02-05 覆盖缺口、历史 PIT 指数成分权重缺失、开盘集合竞价容量缺失、冲击成本曲线仍需上层建模。
- `qant random 8/2 +531.43%` 只能作为 label 泄漏/验证污染反例，不得作为稳健基线。

## 下一步建议

1. 构建日频研究面板 v1。
2. 运行实验层三件套：`pit_factor_audit`、`split label audit`、`benchmark_audit`。
3. 做单因子 IC/RankIC/ICIR、分层收益和季度衰减监控。
4. 做 S1 强基线：单因子、等权、ICIR、线性、LightGBM/Ranker。
5. S1 内必须带最小交易可行性：T+1、涨跌停、停牌、ST、上市年龄、成本、开盘 L1 冲击、成交失败和基础容量。
6. S1 通过后再进入 S2 深度容量、分档滑点、冲击成本和风险开关 v1 验证。

## 新 session 最小提示词

```text
你在 D:\quantum_a0\quant-strategy-study-plan 工作，默认中文。先读 PROFILE.md、ACTIVE.md，再读本仓库 task_plan.md、findings.md、progress.md、session_handoff_20260430.md、quant_strategy_plan.md、quant_strategy_research_plan_detailed.md、validation_params.json、三方审计报告_20260430.md。

当前状态：两份策略文档已迁移到 Git 项目并吸收 2026-04-30 三方审计意见；Git 仓库版本是权威，D:\data\strategy 下两份文件只是镜像。D:\data\warehouse 仍是 canonical 数据源，最近一次 leakage_check 为 2026-04-29 10:38:49，15 类目录 PASS。

后续实验必须遵守 PIT、T+1、涨跌停、停牌、ST、上市年龄、成本、滑点、冲击成本、非幸存者股票池、purge/embargo、split label audit 和 holdout/DSR 约束。官方策略证据默认使用 validation_params.json：5 年训练、21 个交易日测试/调仓、purge_days >= max(label_horizon,20)、embargo 5、至少 12 个 OOT step。

qant random 8/2 的 +531.43% 只能作为 label 泄漏/验证污染反例，不得作为稳健基线。下一步优先做日频研究面板 v1、实验层 PIT/label/benchmark audit、单因子和 S1 强基线；S1 必须内置最小交易可行性，S2 只在 S1 通过后深化容量、分档滑点、冲击成本和风险开关。
```
