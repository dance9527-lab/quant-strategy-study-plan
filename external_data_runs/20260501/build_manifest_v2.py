import os
import pandas as pd

base = "D:/quantum_a0/quant-strategy-study-plan/external_data_runs/20260501"
datasets = []

def add(ds_id, path, role, coverage, scope, pit, posthoc="", issues=""):
    full = f"{base}/{path}"
    ok = os.path.exists(full)
    rows = 0
    if ok:
        try:
            with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                rows = sum(1 for _ in f) - 1
        except:
            rows = -1
    datasets.append({
        'dataset_id': ds_id, 'physical_path': path, 'row_count': rows,
        'version_role': role, 'coverage_scope': coverage,
        'sample_or_full': scope, 'pit_status': pit,
        'posthoc_fields': posthoc, 'blocking_issues': issues,
        'exists': ok
    })

# === P0 阻塞数据 ===
add("suspend_d_raw", "deepseek/raw/tushare/suspension_events/suspend_d_full.csv",
    "raw_evidence", "2000-2026", "full", "candidate_raw_blocked",
    "", "缺PIT字段;未来日期38行;主键重复82行;suspend_timing缺失99%")

add("suspend_d_staging", "deepseek/staging/suspend_d/suspend_d.csv",
    "staging_candidate", "1999-2001", "sample", "candidate_staging_pit_fields_present",
    "", "仅5000行早期窗口,不是完整历史")

add("namechange", "deepseek/staging/namechange/namechange.csv",
    "staging_candidate", "2020-2026", "partial", "candidate_staging_needs_pit",
    "", "key重复3758行;公告日缺失;未来start/end date")

add("index_000300", "deepseek/staging/index_000300/index_000300.csv",
    "staging_candidate", "2025-2026", "sample", "candidate_partial_window",
    "", "仅20个月度截面,无法构建完整PIT universe")

add("index_000905", "deepseek/staging/index_000905/index_000905.csv",
    "staging_candidate", "2025-2026", "sample", "candidate_partial_window",
    "", "仅12个月度截面")

add("index_000852", "deepseek/staging/index_000852/index_000852.csv",
    "staging_candidate", "2025-2026", "sample", "candidate_partial_window",
    "", "仅6个月度截面")

add("idx_cons_300", "deepseek/raw/tushare/index_membership/000300_cons.csv",
    "raw_evidence", "当前快照", "snapshot", "candidate_snapshot_only",
    "", "无移除记录,幸存者偏差")

add("idx_daily_300", "deepseek/raw/tushare/index_membership/000300_SH_daily.csv",
    "raw_candidate", "2005-2026", "full", "candidate_raw_needs_pit",
    "", "缺available_at/decision_time")

add("idx_daily_500", "deepseek/raw/tushare/index_membership/000905_SH_daily.csv",
    "raw_candidate", "2005-2026", "full", "candidate_raw_needs_pit",
    "", "缺available_at/decision_time")

add("idx_daily_1000", "deepseek/raw/tushare/index_membership/000852_SH_daily.csv",
    "raw_candidate", "2005-2026", "full", "candidate_raw_needs_pit",
    "", "缺available_at/decision_time")

add("stock_basic", "deepseek/staging/stock_basic/stock_basic.csv",
    "staging_candidate", "1990-2026", "full", "candidate_staging_needs_pit",
    "", "delist_date全空,不能解除幸存者偏差")

add("dividend", "deepseek/staging/dividend/dividend.csv",
    "reference_only", "累计统计", "full", "reference_only",
    "", "非逐笔公司行为事件流;缺record_date/ex_rights_date等")

# === P1 风控执行 ===
add("margin_tushare", "coder/raw/tushare/margin_trading/margin_detail_tushare.csv",
    "raw_candidate", "2025-2026", "sample", "candidate_raw_needs_pit",
    "", "仅2025-2026多月采样,非全历史")

add("northbound_tushare", "coder/raw/tushare/northbound_flow/hk_hold_tushare.csv",
    "raw_candidate", "2025-2026", "sample", "candidate_raw_needs_pit",
    "", "仅2025-2026采样")

add("share_float_akshare", "coder/raw/tushare/restricted_unlock/share_float_akshare_combined.csv",
    "raw_candidate", "2010-2024", "full", "candidate_raw_needs_pit",
    "解禁前20日涨跌幅;解禁后20日涨跌幅", "后验字段需禁用")

add("share_float_tushare", "coder/raw/tushare/restricted_unlock/share_float_tushare.csv",
    "raw_evidence", "2015-2035", "future_plans", "raw_evidence_only",
    "", "全部为未来解禁计划;以ann_date为可得性锚点")

add("stk_limit", "coder/raw/tushare/limit_events/stk_limit_tushare.csv",
    "raw_candidate", "2026", "sample", "candidate_raw_needs_pit",
    "", "仅2026采样")

add("top_list", "coder/raw/tushare/limit_events/top_list_tushare.csv",
    "raw_candidate", "2026", "sample", "candidate_raw_needs_pit",
    "", "仅2026采样")

add("fut_daily", "coder/raw/tushare/index_futures/fut_daily_tushare.csv",
    "raw_candidate", "2019-2026", "full", "candidate_raw_needs_pit",
    "", "覆盖较好但缺PIT字段")

add("zt_pool", "coder/raw/akshare/seal_amount/zt_pool.csv",
    "raw_candidate", "2026-04~05", "sample", "candidate_raw_needs_pit",
    "", "仅近1个月")

add("dt_pool", "coder/raw/akshare/seal_amount/dt_pool.csv",
    "raw_candidate", "2026-04~05", "sample", "candidate_raw_needs_pit",
    "", "仅近1个月")

# === P1.5 GMSL (mimo staging parquet) ===
gmsl = [
    ("gmsl_wti", "mimo/staging/wti_crude.parquet", "WTI原油"),
    ("gmsl_brent", "mimo/staging/brent_crude.parquet", "布伦特原油"),
    ("gmsl_sc_crude", "mimo/staging/sc_crude.parquet", "上海原油"),
    ("gmsl_dxy", "mimo/staging/dxy.parquet", "美元指数"),
    ("gmsl_usdcny", "mimo/staging/usdcny.parquet", "美元/人民币"),
    ("gmsl_fed_funds", "mimo/staging/fed_funds.parquet", "联邦基金利率"),
    ("gmsl_ust_10y", "mimo/staging/ust_10y.parquet", "10年国债"),
    ("gmsl_ust_2y", "mimo/staging/ust_2y.parquet", "2年国债"),
    ("gmsl_ust_30y", "mimo/staging/ust_30y.parquet", "30年国债"),
    ("gmsl_vix", "mimo/staging/vix.parquet", "VIX"),
    ("gmsl_vix9d", "mimo/staging/vix9d.parquet", "VIX9D"),
    ("gmsl_vxn", "mimo/staging/vxn.parquet", "VXN"),
    ("gmsl_gvz", "mimo/staging/gvz.parquet", "GVZ"),
    ("gmsl_ovx", "mimo/staging/ovx.parquet", "OVX"),
    ("gmsl_gold", "mimo/staging/gold_futures.parquet", "黄金期货"),
    ("gmsl_silver", "mimo/staging/silver_futures.parquet", "白银期货"),
    ("gmsl_copper", "mimo/staging/shfe_copper.parquet", "铜期货"),
    ("gmsl_spx", "mimo/staging/spx.parquet", "标普500"),
    ("gmsl_nasdaq", "mimo/staging/nasdaq.parquet", "纳斯达克"),
    ("gmsl_usdcnh_boc", "mimo/staging/usdcnh_boc.parquet", "美元/人民币BOC"),
    ("gmsl_gold_sge", "mimo/staging/gold_sge.parquet", "黄金SGE"),
    ("gmsl_silver_sge", "mimo/staging/silver_sge.parquet", "白银SGE"),
    ("gmsl_shfe_gold", "mimo/staging/shfe_gold.parquet", "沪金"),
    ("gmsl_shfe_silver", "mimo/staging/shfe_silver.parquet", "沪银"),
]
for ds_id, path, name in gmsl:
    add(ds_id, path, "staging_candidate", "历史", "full", "stress_report_candidate",
        "", "需session_cutoff/source_status/license复核;不得用于alpha/选模/阈值")

# === P2 review ===
add("rev_lhb", "review/staging/event_explainability/event_lhb_staged.csv",
    "staging_candidate", "样本", "sample", "candidate_staging_needs_pit",
    "上榜后1日;上榜后2日;上榜后5日;上榜后10日", "asset_id疑似全部映射为000001.SZ;后验字段需禁用")

add("rev_holder", "review/staging/event_explainability/event_holder_staged.csv",
    "staging_candidate", "样本", "sample", "candidate_staging_needs_pit",
    "", "缺available_at/decision_time")

add("rev_analyst_cninfo", "review/staging/analyst/analyst_cninfo_staged.csv",
    "staging_candidate", "样本", "sample", "candidate_staging_needs_pit",
    "", "核心字段全空;主键重复严重")

add("rev_bs", "review/staging/fundamental/fundamental_bs_staged.csv",
    "staging_candidate", "单股", "sample", "candidate_staging_needs_pit",
    "", "仅000001.SZ;大量财报科目为空")

add("rev_is", "review/staging/fundamental/fundamental_is_staged.csv",
    "staging_candidate", "单股", "sample", "candidate_staging_needs_pit",
    "", "仅000001.SZ;roe/gross_margin为空")

add("rev_minute", "review/staging/minute/minute_daily_staged.csv",
    "unusable", "单股", "sample", "unusable",
    "", "SSL阻断;仅78行单股;集合竞价字段全空")

add("rev_share_change", "review/staging/event_explainability/event_share_change_staged.csv",
    "staging_candidate", "样本", "sample", "candidate_staging_needs_pit",
    "", "样本极少")

add("rev_news_cctv", "review/staging/news/news_cctv_staged.csv",
    "reference_only", "样本", "sample", "reference_only", "", "仅11行")
add("rev_news_stock", "review/staging/news/news_stock_staged.csv",
    "reference_only", "样本", "sample", "reference_only", "", "仅10行")
add("rev_news_div", "review/staging/news/news_dividend_staged.csv",
    "reference_only", "样本", "sample", "reference_only", "", "仅15行")
add("rev_news_suspend", "review/staging/news/news_suspend_staged.csv",
    "reference_only", "样本", "sample", "reference_only", "", "仅8行")
add("rev_analyst_ths", "review/staging/analyst/analyst_ths_staged.csv",
    "unusable", "样本", "sample", "unusable", "", "仅3行,UNUSABLE")
add("rev_etf_1min", "review/raw/akshare/minute/minute_etf_1min.csv",
    "failed", "无", "empty", "fetch_empty_or_failed", "", "空文件")
add("rev_rv_1min", "review/raw/akshare/minute/minute_rv_1min.csv",
    "failed", "无", "empty", "fetch_empty_or_failed", "", "空文件")

# === 生成 manifest ===
df = pd.DataFrame(datasets)
df.to_csv(f"{base}/data_manifest_v2.csv", index=False)

# === 统计 ===
print("=" * 80)
print("数据集 Manifest v2 — 对账后")
print("=" * 80)
print(f"总数据集: {len(df)}")

print(f"\n--- 按 pit_status ---")
for s, g in df.groupby('pit_status'):
    print(f"  {s:45s} {len(g):>2} 个  {g['row_count'].sum():>10,} 行")

print(f"\n--- 按 sample_or_full ---")
for s, g in df.groupby('sample_or_full'):
    print(f"  {s:20s} {len(g):>2} 个  {g['row_count'].sum():>10,} 行")

print(f"\n--- 按 version_role ---")
for s, g in df.groupby('version_role'):
    print(f"  {s:20s} {len(g):>2} 个  {g['row_count'].sum():>10,} 行")

print(f"\n--- 后验字段 ---")
for _, r in df[df['posthoc_fields'] != ''].iterrows():
    print(f"  {r['dataset_id']:30s} → {r['posthoc_fields']}")

print(f"\n--- 阻塞/不可用 ---")
for _, r in df[df['pit_status'].str.contains('blocked|unusable|failed')].iterrows():
    print(f"  {r['dataset_id']:30s} → {r['pit_status']}: {r['blocking_issues'][:60]}")

print(f"\n✅ 已保存: {base}/data_manifest_v2.csv")
