# 任务计划：策略研究计划 Git 维护

## 目标

1. 以 `quant_strategy_plan.md` 作为短总纲，维护研究方向、证据、优先级和禁用结论。
2. 以 `quant_strategy_research_plan_detailed.md` 作为详细执行规范，维护数据口径、标签、验证、回测、台账、验收和 review 清单。
3. 吸收 `三方审计报告_20260430.md` 的合理意见，并对不合理或证据不足的意见做独立裁决。
4. 修改完成后同步到 GitHub 仓库 `dance9527-lab/quant-strategy-study-plan`。

## 审计吸收计划（2026-04-30）

### 输入

- `三方审计报告_20260430.md`
- `quant_strategy_plan.md`
- `quant_strategy_research_plan_detailed.md`
- `D:\data\warehouse` 当前可审计数据底座和历史 qant 实验结论

### 本轮范围

- [x] 拉取/获取三方审计报告。
- [x] 建立 Git 项目内规划文件。
- [x] 并行评估审计意见、当前文档缺口和本地数据证据。
- [x] 独立裁决 P0/P1/P2 建议。
- [x] 修订短总纲。
- [x] 修订详细执行规范。
- [x] 校验文档不引入未经验证收益承诺或泄漏风险。
- [x] 提交并同步到 GitHub。

### 主控原则

- 不把审计报告的收益预估直接写成策略承诺。
- P0/P1/P2 的排序以当前可验证数据、执行风险和泄漏风险为准。
- 继续坚持 `D:\data\warehouse` 为 canonical 数据源。
- 所有 qant 类 10 日标签实验默认 OOT purge、validation purge 或 embargo，并做 split label audit。
- 若审计建议需要新增数据或依赖，先检查本地可用性；必要时执行低风险安装或数据准备。

### 独立裁决摘要

- 采纳：涨跌停执行、因子 PIT、walk-forward 固化、DSR/holdout、实验层审计、台账扩展。
- 部分采纳：开盘冲击三段模型、分红送配 P1.5、风险开关 v1、S1 完成量化标准。
- 不机械采纳：`S2 完全后置`。最小交易可行性必须进入 S1；S2 仅承担深度容量、分档滑点、冲击成本和组合约束优化。
- 不作为结论采纳：DeepSeek 收益路径和 alpha 区间。它们只进入假设队列，不能写成收益承诺。

### 校验结果

- `validation_params.json` 已通过 `python -m json.tool`。
- `git diff --check` 无空白错误，仅提示 Windows 下 LF 可能转换为 CRLF。
- 搜索确认未将 `15-35%`、`2-4%`、`3-5%` 等收益路径写成承诺；只保留“不得承诺未经实证收益”的约束。
- Git 项目两份策略文档已同步回 `D:\data\strategy` 作为本地镜像，SHA256 一致。

### 同步结果

- 提交：`0ffc11f Incorporate three-party audit feedback`。
- 推送：`main -> origin/main` 成功。
