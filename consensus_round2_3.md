# 多专家共识讨论 — Round 2 & 3

> Round 2：Main Agent 独立立场已给出
> Round 3：各方质证和辩驳

---

## Main Agent 的立场总结

| 分歧 | Main Agent 立场 | 建议方案 |
|---|---|---|
| 1日标签 purge | 折中：20天（DeepSeek 10天 vs 原文40天） | `max(label_horizon*5, 20)`，报告10/20/40敏感性 |
| Block bootstrap block_days | 支持 DeepSeek | IC用 `max(label_horizon, empirical_acf_cutoff)`，组合收益保持原规则 |
| Refit/Rebalance 不同步 | 不需要同步，用模型版本管理 | calendar 增加 model_refit_flag 和 frozen_model_version |
| 因子方向预注册 | 部分支持 | 高置信因子必须预注册方向，探索性因子只记录不强制 |
| Newey-West 带宽 | 支持增加敏感性 | 报告 default/andrews/lag6/lag12 四种带宽的 t-stat |

---

## 需要各方回应的问题

1. **1日标签 purge**：20天折中方案是否可接受？DeepSeek 是否坚持10天？
2. **Block bootstrap**：empirical_acf_cutoff 的估计方法是否可行？在小样本（24步）下是否可靠？
3. **因子方向预注册**：高置信/探索性的分类标准是否清晰？如何避免分类本身成为自由度？
4. **其他未覆盖的分歧**：是否有agent发现其他审计中提出但未被讨论的关键问题？

---

## 各方回应（待填写）

### Review Agent 回应
（基于 review_agent_audit.md 中的观点）

### DeepSeek Agent 回应
（基于 deepseek_agent_audit.md 中的观点）

### Coder Agent 回应
（基于 coder_agent_audit.md 中的观点）
