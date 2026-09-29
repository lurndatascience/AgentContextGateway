# Gateway evaluation

Gateway: https://contextgateway.vaibhavkadam.online

Items in store: 1272. LLM configured: True.
## Showcase queries

### Factual lookup combining prose and a structured record

Task: *Which company became a premium supplier of RISE with SAP?*  
Result: **PASS** (5229 ms)

scopes `public`, as of 2024-07-01, 3 items, 998/1500 tokens, 30 candidates considered


**[1] T-Systems becomes premium supplier of RISE with SAP in Germany** (unstructured, unknown, score 0.0325)
> T-Systems today announced that it is a premium supplier of RISE with SAP. This announcement makes T-Systems the first SAP partner in Germany to offer infrastructure, technical managed services, business transformation and application management services in connection with RISE with SAP. This designation will make it easier for customers to move their mission-critical workloads into the cloud. T-Sy
- evidence: `press_release/43#0` scope=public conf=0.9 observed=unknown (unknown)
- why: lexical match (contextual index) rank 1, covers 71% of the task's term weight: premium, rise, sap, supplier / semantic match (contextual index) rank 2 / LLM reranker score 10/10 / indexed with context note: The speaker is Thomas Saueressig, a member of the Executive Board of SAP SE, and Ferri Abolhassan, CEO of T-Systems. The / confidence 0.9: verbatim primary text / freshness unknown: observed no timestamp in source

**[2] T-Systems becomes premium supplier of RISE with SAP in Germany** (structured, unknown, score 0.0325)
> T-Systems becomes premium supplier of RISE with SAP in Germany. T-Systems announced it is a premium supplier of RISE with SAP, the first SAP partner in Germany to deliver end-to-end services around the offering. The move supports customer cloud migrations, including delivery on select hyperscalers and on T-Systems' private cloud FCI with German/EU data protection compliance. Key metrics: First SAP
- evidence: `record/43` scope=public conf=0.75 observed=unknown (unknown)
- why: lexical match (contextual index) rank 2, covers 71% of the task's term weight: premium, rise, sap, supplier / semantic match (contextual index) rank 1 / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness unknown: observed no timestamp in source

**[3] ISG names T-Systems a Leader in four AWS Provider Lens categories in Germany** (structured, unknown, score 0.0137)
> ISG names T-Systems a Leader in four AWS Provider Lens categories in Germany. ISG recognized T-Systems as a top “Leader” in four of five categories in its Provider Lens report on AWS ecosystem partners in Germany. The report highlights strengths including security focus, multi-cloud expertise, and SAP workloads capabilities. Key metrics: Leader status in 4 of 5 categories; 5 categories in the repo
- evidence: `record/61` scope=public conf=0.75 observed=unknown (unknown)
- why: semantic match (contextual index) rank 13 / LLM reranker score 5/10 / confidence 0.75: record extracted by an LLM from the release / freshness unknown: observed no timestamp in source

### Conflicting fact: FY 2022 service revenue was restated

Task: *What was Deutsche Telekom's service revenue in FY 2022?*  
Result: **PASS** (3882 ms)

scopes `public+internal`, as of 2024-07-01, 4 items, 982/1500 tokens, 30 candidates considered

- **conflict** [1]: Service revenue|FY 2022 has 2 different values: 91,988 from financial_fact/28:Service revenue|FY 2022 (2024-02-25, confidence 0.85); 91,947 from internal_note/n02:fact0 (2023-03-02, confidence 0.6); 91,947 from financial_fact/163:Service revenue|FY 2022 (2023-02-25, confidence 0.85). *Resolution: Kept 91,988 from financial_fact/28:Service revenue|FY 2022; later reports restate earlier figures. All values are cited so the agent can disclose the discrepancy.*

**[1] Service revenue, FY 2022** (structured, aging, score 0.0479)
> Deutsche Telekom Service revenue for FY 2022: 91,988 (as reported in the Q4 2023 results release, doc 28; millions of € unless the metric is a percentage or per-share figure).
- evidence: `financial_fact/28:Service revenue|FY 2022` scope=public conf=0.85 observed=2024-02-25 (inferred); `internal_note/n02:fact0` scope=internal conf=0.6 observed=2023-03-02 (day); `financial_fact/163:Service revenue|FY 2022` scope=public conf=0.85 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 1, covers 100% of the task's term weight: 2022, deutsche, fy, revenue, service, telekom / semantic match (contextual index) rank 1 / LLM reranker score 10/10 / structured fact for FY 2022, compact and directly quotable / chosen over 1 conflicting value(s) as the most recent, most confident source / confidence 0.85: deterministic parse of a reported table / freshness aging: observed 2024-02-25 (inferred precision)

**[2] Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023** (structured, stale, score 0.0318)
> Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023. Deutsche Telekom reports 2022 results above raised guidance, driven by service revenue growth and strong free cash flow. For 2023, it forecasts further EBITDA AL growth and a free cash flow AL increase to over 16 billion euros, while completing the sale of a majority stake in GD Towers. Key metrics: FY 202
- evidence: `record/163` scope=public conf=0.75 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 1, covers 100% of the task's term weight: 2022, deutsche, fy, revenue, service, telekom / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness stale: observed 2023-02-25 (inferred precision)

**[3] Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023** (unstructured, stale, score 0.0141)
> Deutsche Telekom stays on track despite unsteady conditions. Europe’s largest telecommunications group has not only met, but exceeded its guidance for 2022, which it raised multiple times throughout the year. Total revenue increased by 6.1 percent compared with 2021 to 114.4 billion euros. Service revenue increased by 10.6 percent to 91.9 billion euros. Adjusted EBITDA AL was up by 7.7 percent to 
- evidence: `press_release/163#1` scope=public conf=0.9 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 11, covers 68% of the task's term weight: 2022, deutsche, revenue, service, telekom / LLM reranker score 10/10 / indexed with context note: The speaker is Tim Höttges, Chairman of the Board of Management of Deutsche Telekom, discussing the company's financial  / confidence 0.9: verbatim primary text / freshness stale: observed 2023-02-25 (inferred precision)

**[4] Deutsche Telekom hits raised 2023 targets; revenue €112.0bn and free cash flow AL €16.1bn** (structured, aging, score 0.0479)
> Deutsche Telekom hits raised 2023 targets; revenue €112.0bn and free cash flow AL €16.1bn. Deutsche Telekom reports it met repeatedly raised 2023 targets, with organic growth in service revenues and adjusted EBITDA AL and a sharp increase in free cash flow AL. The company also provided 2024 guidance and confirmed a proposed dividend and share buyback plan. Key metrics: Net revenue €112.0bn (organi
- evidence: `record/28` scope=public conf=0.75 observed=2024-02-25 (inferred)
- why: structured record for the same release as [1] / confidence 0.75: record extracted by an LLM from the release / freshness aging: observed 2024-02-25 (inferred precision)

### Duplicate fact confirmed by two internal notes

Task: *What FY 2023 dividend per share did the AGM approve?*  
Result: **PASS** (4915 ms)

scopes `public+internal`, as of 2024-07-01, 8 items, 1234/1500 tokens, 30 candidates considered

- **duplicate** [2]: Dividend per share|FY 2023 = 0.77 is reported by 2 sources. *Resolution: Merged into one item; every source is cited.*

**[1] #ir-comms message from Lena** (unstructured, fresh, score 0.0492)
> The AGM approved the FY 2023 dividend of 0.77 euros per share today. Payment date is next week.
- evidence: `internal_note/n11` scope=internal conf=0.6 observed=2024-04-10 (day)
- why: lexical match (contextual index) rank 1, covers 76% of the task's term weight: 2023, agm, dividend, fy, per, share / semantic match (contextual index) rank 1 / LLM reranker score 10/10 / confidence 0.6: informal message, not verified / freshness fresh: observed 2024-04-10 (day precision)

**[2] Dividend per share, FY 2023** (structured, fresh, score 0.0308)
> Deutsche Telekom Dividend per share for FY 2023: 0.77 (stated in a #ir-comms message by Lena).
- evidence: `internal_note/n11:fact0` scope=internal conf=0.6 observed=2024-04-10 (day); `internal_note/n06:fact0` scope=internal conf=0.6 observed=2023-11-02 (day)
- why: lexical match (contextual index) rank 7, covers 52% of the task's term weight: 2023, dividend, fy, per, share / semantic match (contextual index) rank 3 / LLM reranker score 10/10 / structured fact for FY 2023, compact and directly quotable / same value confirmed by 2 sources, merged into one item / confidence 0.6: informal message, not verified / freshness fresh: observed 2024-04-10 (day precision)

**[3] Deutsche Telekom plans higher 2023 dividend and up to €2B share buyback in 2024** (structured, aging, score 0.029)
> Deutsche Telekom plans higher 2023 dividend and up to €2B share buyback in 2024. Deutsche Telekom announced plans to raise the dividend for the 2023 financial year to €0.77 per share and to repurchase shares in 2024 for up to €2 billion. The company will release its first nine months 2023 financial figures on November 9, 2023. Key metrics: Dividend 2023 planned at €0.77 per share; Dividend 2022 wa
- evidence: `record/65` scope=public conf=0.75 observed=2023-11-09 (day)
- why: lexical match (contextual index) rank 4, covers 52% of the task's term weight: 2023, dividend, fy, per, share / semantic match (contextual index) rank 15 / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness aging: observed 2023-11-09 (day precision)

**[4] Deutsche Telekom Q3 2023: guidance raised, dividend to 0.77€ and up to 2bn€ share buyback planned** (structured, aging, score 0.0273)
> Deutsche Telekom Q3 2023: guidance raised, dividend to 0.77€ and up to 2bn€ share buyback planned. Deutsche Telekom reported Q3 2023 growth in key indicators, raised full-year guidance, and announced a higher proposed dividend plus a 2024 share buyback program. Customer growth continued in Germany, the U.S. (T-Mobile US), and Europe. Key metrics: Dividend proposed: 0.77€ per share (2022: 0.70€); P
- evidence: `record/62` scope=public conf=0.75 observed=2023-11-10 (inferred)
- why: lexical match (contextual index) rank 5, covers 52% of the task's term weight: 2023, dividend, fy, per, share / semantic match (contextual index) rank 24 / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness aging: observed 2023-11-10 (inferred precision)

**[5] Deutsche Telekom plans higher 2023 dividend and up to €2B share buyback in 2024** (unstructured, aging, score 0.0267)
> Financial figures for the first nine months of 2023 to be released on November 9 The Board of Management of Deutsche Telekom today presented its plans for the company’s upcoming shareholder remuneration. These entail increasing the dividend for the 2023 financial year to 0.77 euros per dividend-bearing share. The dividend paid for the 2022 financial year amounted to 0.70 euros per share. In additi
- evidence: `press_release/65#0` scope=public conf=0.9 observed=2023-11-09 (day)
- why: lexical match (contextual index) rank 17, covers 41% of the task's term weight: 2023, dividend, per, share / semantic match (contextual index) rank 13 / LLM reranker score 10/10 / indexed with context note: The speaker is Tim Höttges, discussing Deutsche Telekom's plans for shareholder remuneration, including a dividend incre / confidence 0.9: verbatim primary text / freshness aging: observed 2023-11-09 (day precision)

**[6] Deutsche Telekom Q3 2023: guidance raised, dividend to 0.77€ and up to 2bn€ share buyback planned** (unstructured, aging, score 0.0127)
> Dividend to increase to 77 eurocents per share, share buy-backs of up to 2 billion euros planned Germany: strong growth in mobile and broadband customer bases T-Mobile US: industry leader in customer net additions Europe: Growth trend continues
- evidence: `press_release/62#0` scope=public conf=0.9 observed=2023-11-10 (inferred)
- why: lexical match (contextual index) rank 19, covers 41% of the task's term weight: 2023, dividend, per, share / LLM reranker score 10/10 / indexed with context note: The speaker is Deutsche Telekom, discussing its financial performance and plans for dividends and share buy-backs in the / confidence 0.9: verbatim primary text / freshness aging: observed 2023-11-10 (inferred precision)

**[7] #ir-comms message from Lena** (unstructured, aging, score 0.0306)
> Draft of the Q3 2023 release mentions a dividend proposal of 0.77 euros per share for FY 2023, up from 0.70. Legal review is still pending, so treat the number as draft until Thursday.
- evidence: `internal_note/n06` scope=internal conf=0.6 observed=2023-11-02 (day)
- why: lexical match (contextual index) rank 9, covers 52% of the task's term weight: 2023, dividend, fy, per, share / semantic match (contextual index) rank 2 / LLM reranker score 5/10 / confidence 0.6: informal message, not verified / freshness aging: observed 2023-11-02 (day precision)

**[8] Deutsche Telekom plans higher 2023 dividend and up to €2B share buyback in 2024** (unstructured, aging, score 0.0292)
> At the Capital Markets Day 2021, Deutsche Telekom’s Board of Management had also announced that it would take share buy-backs into consideration in the future. The planned share buy-backs in the coming year amounting to up to 2 billion euros are intended to recoup part of the dilution effect from Deutsche Telekom’s 2021 capital increase. The Board of Management’s plans for this shareholder remuner
- evidence: `press_release/65#2` scope=public conf=0.9 observed=2023-11-09 (day)
- why: lexical match (contextual index) rank 6, covers 52% of the task's term weight: 2023, dividend, fy, per, share / semantic match (contextual index) rank 11 / LLM reranker score 5/10 / indexed with context note: The speaker is Deutsche Telekom's Board of Management, discussing plans for shareholder remuneration, including share bu / confidence 0.9: verbatim primary text / freshness aging: observed 2023-11-09 (day precision)

### Tempting private item must stay out (internal scope)

Task: *What are the preliminary Q1 2026 results, net revenue and adjusted EBITDA?*  
Result: **PASS** (4047 ms)

scopes `public+internal`, as of 2026-05-01, 0 items, 0/1500 tokens, 30 candidates considered

- **missing** : No in-scope evidence found for this task. *Resolution: The agent should say it cannot answer from available context.*
- **missing** : The task mentions Q1 2026 but no in-scope evidence covers that period. *Resolution: Do not infer the figure; report it as unavailable.*

Same task with the `finance` key (private scope allowed):

scopes `public+internal+private`, as of 2026-05-01, 3 items, 103/1500 tokens, 30 candidates considered


**[1] #finance-close message from Tomasz** (unstructured, fresh, score 0.0328)
> Preliminary, unaudited Q1 2026 figures: net revenue 29,410 million euros, adjusted EBITDA AL 11,180 million, free cash flow AL 4,020 million. Embargoed until the May 14 release. Finance only, do not forward.
- evidence: `internal_note/n03` scope=private conf=0.6 observed=2026-04-28 (day)
- why: lexical match (contextual index) rank 1, covers 94% of the task's term weight: 2026, adjusted, ebitda, net, preliminary, q1 / semantic match (contextual index) rank 1 / LLM reranker score 10/10 / confidence 0.6: informal message, not verified / freshness fresh: observed 2026-04-28 (day precision)

**[2] Net revenue, Q1 2026** (structured, fresh, score 0.0318)
> Deutsche Telekom Net revenue for Q1 2026: 29,410 (stated in a #finance-close message by Tomasz).
- evidence: `internal_note/n03:fact0` scope=private conf=0.6 observed=2026-04-28 (day)
- why: lexical match (contextual index) rank 4, covers 51% of the task's term weight: 2026, net, q1, revenue / semantic match (contextual index) rank 2 / LLM reranker score 10/10 / structured fact for Q1 2026, compact and directly quotable / confidence 0.6: informal message, not verified / freshness fresh: observed 2026-04-28 (day precision)

**[3] Adjusted EBITDA AL, Q1 2026** (structured, fresh, score 0.0317)
> Deutsche Telekom Adjusted EBITDA AL for Q1 2026: 11,180 (stated in a #finance-close message by Tomasz).
- evidence: `internal_note/n03:fact1` scope=private conf=0.6 observed=2026-04-28 (day)
- why: lexical match (contextual index) rank 3, covers 52% of the task's term weight: 2026, adjusted, ebitda, q1 / semantic match (contextual index) rank 3 / LLM reranker score 10/10 / structured fact for Q1 2026, compact and directly quotable / confidence 0.6: informal message, not verified / freshness fresh: observed 2026-04-28 (day precision)

### Stale guidance when the task asks for the current figure

Task: *What is the current full-year guidance for adjusted EBITDA AL?*  
Result: **PASS** (4115 ms)

scopes `public+internal`, as of 2024-07-01, 6 items, 1420/1500 tokens, 30 candidates considered

- **duplicate** [1]: Adjusted EBITDA AL|FY 2022 = 40,208 is reported by 2 sources. *Resolution: Merged into one item; every source is cited.*
- **stale** [3] [5] [6]: 3 item(s) are older than 365 days as of 2024-07-01 and the task does not ask about their period. *Resolution: Prefer a newer source if one appears in the package; otherwise say the information may be outdated.*

**[1] Adjusted EBITDA AL, FY 2022** (structured, aging, score 0.0164)
> Deutsche Telekom Adjusted EBITDA AL for FY 2022: 40,208 (as reported in the Q4 2023 results release, doc 28; millions of € unless the metric is a percentage or per-share figure).
- evidence: `financial_fact/28:Adjusted EBITDA AL|FY 2022` scope=public conf=0.85 observed=2024-02-25 (inferred); `financial_fact/163:Adjusted EBITDA AL|FY 2022` scope=public conf=0.85 observed=2023-02-25 (inferred)
- why: semantic match (contextual index) rank 1 / LLM reranker score 10/10 / structured fact for FY 2022, compact and directly quotable / same value confirmed by 2 sources, merged into one item / confidence 0.85: deterministic parse of a reported table / freshness aging: observed 2024-02-25 (inferred precision)

**[2] Adjusted EBITDA AL, FY 2023** (structured, aging, score 0.0161)
> Deutsche Telekom Adjusted EBITDA AL for FY 2023: 40,497 (as reported in the Q4 2023 results release, doc 28; millions of € unless the metric is a percentage or per-share figure).
- evidence: `financial_fact/28:Adjusted EBITDA AL|FY 2023` scope=public conf=0.85 observed=2024-02-25 (inferred)
- why: semantic match (contextual index) rank 2 / LLM reranker score 10/10 / structured fact for FY 2023, compact and directly quotable / confidence 0.85: deterministic parse of a reported table / freshness aging: observed 2024-02-25 (inferred precision)

**[3] Deutsche Telekom Q1 2023: EBITDA AL guidance raised to ~€40.9bn; strong customer growth** (structured, stale, score 0.0145)
> Deutsche Telekom Q1 2023: EBITDA AL guidance raised to ~€40.9bn; strong customer growth. Deutsche Telekom reported solid Q1 2023 results with service revenue growth and raised full-year adjusted EBITDA AL guidance to around €40.9 billion, supported by T-Mobile US. Net profit jumped mainly due to the closing of the tower transaction in Germany and Austria. Key metrics: FY2023 adjusted EBITDA AL gui
- evidence: `record/132` scope=public conf=0.75 observed=2023-05-15 (inferred)
- why: lexical match (contextual index) rank 9, covers 79% of the task's term weight: adjusted, ebitda, fy, guidance / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness stale: observed 2023-05-15 (inferred precision)

**[4] Deutsche Telekom raises 2023 earnings guidance after strong Q2 results** (structured, aging, score 0.0143)
> Deutsche Telekom raises 2023 earnings guidance after strong Q2 results. Deutsche Telekom reported solid Q2 2023 operating and customer growth and raised its full-year adjusted EBITDA AL guidance to around €41.0 billion. Free cash flow AL guidance remains unchanged at more than €16 billion, with continued strength in Germany, T-Mobile US and Europe. Key metrics: 2023 adjusted EBITDA AL guidance rai
- evidence: `record/109` scope=public conf=0.75 observed=2023-08-10 (inferred)
- why: lexical match (contextual index) rank 10, covers 79% of the task's term weight: adjusted, ebitda, fy, guidance / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness aging: observed 2023-08-10 (inferred precision)

**[5] Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023** (unstructured, stale, score 0.0161)
> Deutsche Telekom stays on track despite unsteady conditions. Europe’s largest telecommunications group has not only met, but exceeded its guidance for 2022, which it raised multiple times throughout the year. Total revenue increased by 6.1 percent compared with 2021 to 114.4 billion euros. Service revenue increased by 10.6 percent to 91.9 billion euros. Adjusted EBITDA AL was up by 7.7 percent to 
- evidence: `press_release/163#1` scope=public conf=0.9 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 2, covers 80% of the task's term weight: adjusted, current, ebitda, guidance / LLM reranker score 5/10 / indexed with context note: The speaker is Tim Höttges, Chairman of the Board of Management of Deutsche Telekom, discussing the company's financial  / confidence 0.9: verbatim primary text / freshness stale: observed 2023-02-25 (inferred precision)

**[6] Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023** (unstructured, stale, score 0.0154)
> T-Mobile US added 6.4 million new postpaid customers in 2022. A key driver of this trend was the lower churn rate among former Sprint customers. As of the year-end, 2.6 million customers were using the high-speed internet, i.e., wireless internet access. That is 2 million more than one year ago. T-Mobile US is systematically scaling back the terminal equipment lease business for its customers, whi
- evidence: `press_release/163#3` scope=public conf=0.9 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 5, covers 80% of the task's term weight: adjusted, current, ebitda, guidance / LLM reranker score 5/10 / indexed with context note: The source is Deutsche Telekom, discussing T-Mobile US's customer growth and financial performance in 2022, with project / confidence 0.9: verbatim primary text / freshness stale: observed 2023-02-25 (inferred precision)

### Out-of-corpus question should come back empty

Task: *Who won the Champions League in 2023?*  
Result: **PASS** (3995 ms)

scopes `public`, as of 2024-07-01, 0 items, 0/1500 tokens, 30 candidates considered

- **missing** : No in-scope evidence found for this task. *Resolution: The agent should say it cannot answer from available context.*

## Golden set: retrieval relevance and attribution

Default configuration: channels ['lexical_ctx', 'dense_ctx'], reranker on.

| metric | value |
|---|---|
| answerable questions | 80 |
| hit rate (an expected doc is in the package) | 91% |
| expected-doc recall | 81% |
| MRR | 0.85 |
| refusal questions returned empty or a missing warning | 55% of 20 |
| attribution completeness (item has evidence with ref, scope, confidence, timestamp precision, quote, and reasons) | 100% of 340 items |
| average items per package | 3.4 |
| out-of-scope evidence returned | 0 |
| average latency | 5404 ms |

## Retrieval ablation

Same golden set, same deployment; the reranker column also acts as the relevance judge. Rows whose channels this deployment cannot serve are skipped.

| configuration | hit rate | doc recall | MRR | refusals empty | avg items | latency |
|---|---|---|---|---|---|---|
| lexical only | 79% | 72% | 0.69 | 20% | 4.0 | 3473 ms |
| lexical + dense (baseline) | 90% | 79% | 0.76 | 0% | 5.8 | 4021 ms |
| baseline + LLM reranker | 90% | 78% | 0.82 | 45% | 3.5 | 5740 ms |
| contextual retrieval | 86% | 77% | 0.74 | 0% | 5.7 | 3722 ms |
| contextual retrieval + LLM reranker | 91% | 81% | 0.86 | 55% | 3.4 | 5529 ms |

## Downstream agents on the same contract

### answer: *What was Deutsche Telekom's service revenue in FY 2022?*

Sentence citation coverage: **100%** (4919 ms)

```
Deutsche Telekom's service revenue for FY 2022 was reported as €91,988 million [1]. However, there is a discrepancy with another source reporting it as €91.9 billion [2][3]. The resolution kept the figure of €91,988 million from the later report [1].
```

Package handed to the agent:

scopes `public+internal`, as of 2024-07-01, 4 items, 982/1200 tokens, 30 candidates considered

- **conflict** [1]: Service revenue|FY 2022 has 2 different values: 91,988 from financial_fact/28:Service revenue|FY 2022 (2024-02-25, confidence 0.85); 91,947 from internal_note/n02:fact0 (2023-03-02, confidence 0.6); 91,947 from financial_fact/163:Service revenue|FY 2022 (2023-02-25, confidence 0.85). *Resolution: Kept 91,988 from financial_fact/28:Service revenue|FY 2022; later reports restate earlier figures. All values are cited so the agent can disclose the discrepancy.*

**[1] Service revenue, FY 2022** (structured, aging, score 0.0479)
> Deutsche Telekom Service revenue for FY 2022: 91,988 (as reported in the Q4 2023 results release, doc 28; millions of € unless the metric is a percentage or per-share figure).
- evidence: `financial_fact/28:Service revenue|FY 2022` scope=public conf=0.85 observed=2024-02-25 (inferred); `internal_note/n02:fact0` scope=internal conf=0.6 observed=2023-03-02 (day); `financial_fact/163:Service revenue|FY 2022` scope=public conf=0.85 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 1, covers 100% of the task's term weight: 2022, deutsche, fy, revenue, service, telekom / semantic match (contextual index) rank 1 / LLM reranker score 10/10 / structured fact for FY 2022, compact and directly quotable / chosen over 1 conflicting value(s) as the most recent, most confident source / confidence 0.85: deterministic parse of a reported table / freshness aging: observed 2024-02-25 (inferred precision)

**[2] Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023** (structured, stale, score 0.0318)
> Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023. Deutsche Telekom reports 2022 results above raised guidance, driven by service revenue growth and strong free cash flow. For 2023, it forecasts further EBITDA AL growth and a free cash flow AL increase to over 16 billion euros, while completing the sale of a majority stake in GD Towers. Key metrics: FY 202
- evidence: `record/163` scope=public conf=0.75 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 1, covers 100% of the task's term weight: 2022, deutsche, fy, revenue, service, telekom / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness stale: observed 2023-02-25 (inferred precision)

**[3] Deutsche Telekom exceeds 2022 guidance; targets higher EBITDA AL and free cash flow in 2023** (unstructured, stale, score 0.0141)
> Deutsche Telekom stays on track despite unsteady conditions. Europe’s largest telecommunications group has not only met, but exceeded its guidance for 2022, which it raised multiple times throughout the year. Total revenue increased by 6.1 percent compared with 2021 to 114.4 billion euros. Service revenue increased by 10.6 percent to 91.9 billion euros. Adjusted EBITDA AL was up by 7.7 percent to 
- evidence: `press_release/163#1` scope=public conf=0.9 observed=2023-02-25 (inferred)
- why: lexical match (contextual index) rank 11, covers 68% of the task's term weight: 2022, deutsche, revenue, service, telekom / LLM reranker score 10/10 / indexed with context note: The speaker is Tim Höttges, Chairman of the Board of Management of Deutsche Telekom, discussing the company's financial  / confidence 0.9: verbatim primary text / freshness stale: observed 2023-02-25 (inferred precision)

**[4] Deutsche Telekom hits raised 2023 targets; revenue €112.0bn and free cash flow AL €16.1bn** (structured, aging, score 0.0479)
> Deutsche Telekom hits raised 2023 targets; revenue €112.0bn and free cash flow AL €16.1bn. Deutsche Telekom reports it met repeatedly raised 2023 targets, with organic growth in service revenues and adjusted EBITDA AL and a sharp increase in free cash flow AL. The company also provided 2024 guidance and confirmed a proposed dividend and share buyback plan. Key metrics: Net revenue €112.0bn (organi
- evidence: `record/28` scope=public conf=0.75 observed=2024-02-25 (inferred)
- why: structured record for the same release as [1] / confidence 0.75: record extracted by an LLM from the release / freshness aging: observed 2024-02-25 (inferred precision)

### brief: *T-Systems and SAP partnership*

Sentence citation coverage: **100%** (5534 ms)

```
- T-Systems has become the first SAP partner in Germany to offer end-to-end services for RISE with SAP, including infrastructure, technical managed services, and business transformation [1][2].

- As a premium supplier, T-Systems supports customer cloud migrations on select hyperscalers and its private cloud, Future Cloud Infrastructure, ensuring compliance with German and EU data protection regulations [1][2].

- The partnership aims to simplify and accelerate business transformation in the cloud, providing flexibility and support for organizations to adapt to digitalization, globalization, and sustainability challenges [1].
```

Package handed to the agent:

scopes `public`, as of 2024-07-01, 4 items, 1492/1600 tokens, 30 candidates considered


**[1] T-Systems becomes premium supplier of RISE with SAP in Germany** (unstructured, unknown, score 0.0328)
> T-Systems today announced that it is a premium supplier of RISE with SAP. This announcement makes T-Systems the first SAP partner in Germany to offer infrastructure, technical managed services, business transformation and application management services in connection with RISE with SAP. This designation will make it easier for customers to move their mission-critical workloads into the cloud. T-Sy
- evidence: `press_release/43#0` scope=public conf=0.9 observed=unknown (unknown)
- why: lexical match (contextual index) rank 1, covers 32% of the task's term weight: partnership, sap, t-systems / semantic match (contextual index) rank 1 / LLM reranker score 10/10 / indexed with context note: The speaker is Thomas Saueressig, a member of the Executive Board of SAP SE, and Ferri Abolhassan, CEO of T-Systems. The / confidence 0.9: verbatim primary text / freshness unknown: observed no timestamp in source

**[2] T-Systems becomes premium supplier of RISE with SAP in Germany** (structured, unknown, score 0.0311)
> T-Systems becomes premium supplier of RISE with SAP in Germany. T-Systems announced it is a premium supplier of RISE with SAP, the first SAP partner in Germany to deliver end-to-end services around the offering. The move supports customer cloud migrations, including delivery on select hyperscalers and on T-Systems' private cloud FCI with German/EU data protection compliance. Key metrics: First SAP
- evidence: `record/43` scope=public conf=0.75 observed=unknown (unknown)
- why: lexical match (contextual index) rank 7, covers 21% of the task's term weight: sap, t-systems / semantic match (contextual index) rank 2 / LLM reranker score 10/10 / confidence 0.75: record extracted by an LLM from the release / freshness unknown: observed no timestamp in source

**[3] T-Systems moves 450+ Continental SAP systems to private cloud in Frankfurt** (unstructured, unknown, score 0.0306)
> One of Germany's largest SAP system landscapes is moving to the cloud: T-Systems is transferring more than 450 SAP systems from Continental AG to the private cloud in Frankfurt am Main. There, the IT service provider will support the SAP operating system until at least the end of 2027. The contract covers all services related to operation: from consulting to the hotline. "We are pleased to continu
- evidence: `press_release/230#0` scope=public conf=0.9 observed=unknown (unknown)
- why: lexical match (contextual index) rank 8, covers 21% of the task's term weight: sap, t-systems / semantic match (contextual index) rank 3 / LLM reranker score 5/10 / indexed with context note: The document features statements from Christian Eigler, Group CIO at Continental AG, and Adel Al-Saleh, CEO of T-Systems / confidence 0.9: verbatim primary text / freshness unknown: observed no timestamp in source

**[4] T-Systems moves 450+ Continental SAP systems to private cloud in Frankfurt** (structured, unknown, score 0.0286)
> T-Systems moves 450+ Continental SAP systems to private cloud in Frankfurt. T-Systems will migrate more than 450 SAP systems from Continental AG to its private cloud in Frankfurt am Main and operate them through at least the end of 2027. The deal includes end-to-end SAP services from consulting and migration to operations and a German-speaking hotline. Key metrics: more than 450 SAP systems; suppo
- evidence: `record/230` scope=public conf=0.75 observed=unknown (unknown)
- why: lexical match (contextual index) rank 9, covers 21% of the task's term weight: sap, t-systems / semantic match (contextual index) rank 11 / LLM reranker score 5/10 / confidence 0.75: record extracted by an LLM from the release / freshness unknown: observed no timestamp in source
