# Review Agent R4 - Final Position

## Background
OOT steps, S1 threshold, training window, and bootstrap all reached consensus. This doc focuses only on the implementation details of the Exploratory Tracking mechanism.

## Four Disputes - Final Positions

### 1. Naming
| Option | Proposer | Assessment |
|--------|---------|-----------|
| Edge Signal Log | Review | Descriptive but negative connotation (edge implies unimportant) |
| Exploratory Observation Table | DeepSeek | Neutral but Table implies structured data |
| Exploratory Tracking | Main | Most accurate - Tracking implies time series and dynamic evaluation |

**Final Position: Accept Main proposal Exploratory Tracking as formal name.**

### 2. Confidentiality from PM
**Position: Insist on confidentiality.**

Key arguments:
- Path dependency prevention: PM naturally tends to integrate exploratory signals into portfolio to prove value, polluting iteration independence
- Anonymization insufficient: Even anonymized, the info itself triggers PM integration impulse
- Trust boundary: Strategy iteration is R scope, PM scope is execution. Asymmetric info access required

### 3. Cooldown Period >= 6 Months
**Position: Insist on >= 6 months.**

Key arguments:
- Avoid short-term re-triggering: 3-month re-flagging creates false signal reinforcement
- Matches S1 threshold: S1 requires >= 60% directional consistency and >= 3 months persistence. 6 months provides adequate window
- Prevents strategy hunting: Cooldown is artificial constraint on impulse to add interesting anomalies

**Compromise: Can accept >= 4 months as floor, >= 6 months preferred.**

### 4. Directional Consistency Threshold 70% vs 60%
**Position: Accept compromise of 65%.**

- 60% too low to distinguish real directionality from random noise
- 70% is ideal but 60% is not unreasonable for exploratory signals
- 65% is rational compromise: stricter than original, captures genuine directional signals

**Bottom line: Will not accept 60% as final threshold. At least 65%.**

## Non-Negotiable List
1. PM confidentiality - absolute, anonymization is not substitute
2. No inclusion in portfolio - until S1 threshold met
3. Complete record keeping - all flags, evaluations, retrospective conclusions archived

## Acceptable Compromises
1. Naming: Accept Exploratory Tracking (Main proposal)
2. Cooldown: Accept >= 4 months as floor, >= 6 months as preferred
3. Threshold: Accept 65% as compromise between 60-70%

## Summary Recommendation
If Main and DeepSeek accept above positions, Exploratory Tracking mechanism:
- Name: Exploratory Tracking
- PM confidentiality: Yes
- Cooldown: >= 6 months (preferred), >= 4 months (floor)
- Directional consistency threshold: >= 65%
- Portfolio inclusion: No (until S1)
- Record keeping: Yes (complete with retrospective conclusions)