# Kantar BLS Analysis - Results Interpretation Guide

## Overview

This document explains how to interpret the results from the Kantar BLS analysis system. It covers what each metric means, how to read the outputs, and what actions to take based on the findings.

---

## Table of Contents

1. [Understanding the Core Metrics](#understanding-the-core-metrics)
2. [Reading the Reports](#reading-the-reports)
3. [Interpreting Visualizations](#interpreting-visualizations)
4. [Signal vs. Noise: What to Trust](#signal-vs-noise-what-to-trust)
5. [Channel Performance Analysis](#channel-performance-analysis)
6. [Metric Performance Analysis](#metric-performance-analysis)
7. [Common Patterns and What They Mean](#common-patterns-and-what-they-mean)
8. [Decision-Making Framework](#decision-making-framework)
9. [Red Flags and Warnings](#red-flags-and-warnings)
10. [Action Items Based on Results](#action-items-based-on-results)

---

## 1. Understanding the Core Metrics

### Lift (%)

**What it is**: The percentage increase in a metric for the exposed group compared to the control group.

**Formula**: `(Exposed% - Control%) / Control% × 100`

**How to read it**:
- **Positive lift** = Good. The exposed group performed better.
- **Negative lift** = Bad. The exposed group performed worse (rare, but possible).
- **Zero lift** = No difference between groups.

**Example**:
- Control: 20% brand awareness
- Exposed: 25% brand awareness
- Lift: (25-20)/20 × 100 = **25% lift**

**What it means**: People who saw the ad were 25% more likely to be aware of the brand than those who didn't.

**Benchmarks**:
- **0-5% lift**: Small but potentially meaningful
- **5-15% lift**: Moderate, good performance
- **15-30% lift**: Strong performance
- **30%+ lift**: Exceptional performance

### Statistical Significance

**What it is**: The probability that the observed difference is real, not random chance.

**How to read it**:
- **p ≤ 0.05**: Statistically significant (95% confidence it's real)
- **p > 0.05**: Not significant (could be random)

**What it means**:
- **Significant**: You can trust this result. It's likely a real effect.
- **Not significant**: Be cautious. This could be random variation.

**Example**:
- Lift: 10%, p = 0.03 → **Trust this result**
- Lift: 10%, p = 0.15 → **Be skeptical, could be noise**

### Coefficient of Variation (CV)

**What it is**: A measure of consistency. How much does this metric vary across observations?

**Formula**: `Standard Deviation / Mean`

**How to read it**:
- **CV < 50%**: Consistent (signal)
- **CV 50-100%**: Moderate variation
- **CV > 100%**: High variation (noise)

**What it means**:
- **Low CV**: The metric shows stable patterns. You can rely on it.
- **High CV**: The metric bounces around a lot. Hard to predict.

**Example**:
- Average lift: 10%, CV = 30% → **Consistent signal**
- Average lift: 10%, CV = 150% → **Unreliable noise**

---

## 2. Reading the Reports

### Text Report Structure

The text report (`kantar_bls_report_YYYYMMDD.txt`) contains:

#### Executive Summary
- **Top 5 Metrics**: Highest average lift across all observations
- **Channel Performance**: Which channels are driving the most lift
- **Signal vs. Noise**: How many metrics are reliable vs. unreliable

**How to use it**:
- Start here for quick overview
- Identify your best-performing metrics
- See which channels to prioritize

#### Detailed Sections

**Top Metrics by Average Lift**:
```
Unaided Brand Awareness: 15.2% lift (n=45)
Brand Favorability: 12.8% lift (n=45)
Consideration: 11.5% lift (n=45)
```

**What this tells you**:
- Which metrics are responding best to advertising
- Sample size (n) shows how many observations you have
- Higher n = more reliable

**Channel Performance**:
```
TV: 12.5% avg lift, 75% consistent metrics
Social: 8.3% avg lift, 60% consistent metrics
Digital: 6.1% avg lift, 45% consistent metrics
```

**What this tells you**:
- Which channels are most effective
- Which channels have reliable results (consistency %)
- Where to allocate budget

**Signal vs. Noise**:
```
Metrics with consistent signal: 23
Metrics with high noise: 12
```

**What this tells you**:
- How many metrics you can trust
- How many metrics to ignore
- Overall data quality

---

## 3. Interpreting Visualizations

### Lift by Channel Chart

**What it shows**: Average lift percentage for each channel.

**How to read it**:
- **Bars above zero**: Positive lift (good)
- **Taller bars**: Better performance
- **Bars below zero**: Negative lift (concerning)

**What to look for**:
- Which channels are performing best
- Large differences between channels
- Any channels showing negative lift

**Example interpretation**:
```
TV: 15% lift
Social: 8% lift
Digital: 5% lift
```
→ **TV is performing best. Consider increasing TV budget.**

### Top Metrics Chart

**What it shows**: The highest-performing metrics by average lift.

**How to read it**:
- Metrics at the top are your strongest performers
- Longer bars = higher lift
- Look for patterns (e.g., all awareness metrics performing well)

**What to look for**:
- Which brand metrics are responding
- Whether awareness, consideration, or favorability is strongest
- If specific product categories are performing well

**Example interpretation**:
```
Unaided Brand Awareness: 18% lift
Brand Favorability: 14% lift
DashPass Awareness: 12% lift
```
→ **Awareness metrics are strongest. Focus messaging on brand awareness.**

### Lift Heatmap

**What it shows**: Lift values across metrics (rows) and channels (columns).

**How to read it**:
- **Green cells**: Positive lift (darker = stronger)
- **Red cells**: Negative lift
- **Yellow/neutral**: Near zero

**What to look for**:
- Which metric-channel combinations work best
- Patterns (e.g., TV works for awareness, Social works for consideration)
- Gaps (metrics/channels with no data)

**Example interpretation**:
```
                TV    Social  Digital
Awareness       15%    8%      5%
Favorability    12%    10%     4%
Consideration   10%    12%     6%
```
→ **TV is best for awareness. Social is best for consideration. Use channel-specific strategies.**

---

## 4. Signal vs. Noise: What to Trust

### Signal Metrics

**Characteristics**:
- Statistically significant (p ≤ 0.05)
- Consistent (CV < 50%)
- Sufficient sample size (n ≥ 3)

**What this means**:
- These results are reliable
- You can make decisions based on them
- They represent real patterns, not random variation

**Example**:
```
Metric: Unaided Brand Awareness
Average Lift: 15%
Significance: p = 0.02 (significant)
CV: 35% (consistent)
Observations: 12
```
→ **This is signal. Trust it. Act on it.**

### Noise Metrics

**Characteristics**:
- Not significant (p > 0.05) OR
- High variation (CV > 100%) OR
- Insufficient data (n < 3)

**What this means**:
- These results are unreliable
- Don't make decisions based on them
- Could be random variation

**Example**:
```
Metric: Brand Attribute X
Average Lift: 20%
Significance: p = 0.18 (not significant)
CV: 180% (high variation)
Observations: 2
```
→ **This is noise. Ignore it. Don't act on it.**

### How to Use This Classification

**For Decision-Making**:
1. **Focus on signal metrics** - These are your reliable insights
2. **Ignore noise metrics** - Don't waste time on unreliable data
3. **Investigate borderline cases** - If something is significant but inconsistent, dig deeper

**For Reporting**:
- Highlight signal metrics prominently
- Note noise metrics but explain why they're unreliable
- Show the ratio of signal to noise as a data quality indicator

---

## 5. Channel Performance Analysis

### Comparing Channels

**Key Questions to Answer**:
1. Which channel drives the highest lift?
2. Which channel is most consistent?
3. Which channel works best for which metrics?

### Channel Performance Matrix

Use this framework to evaluate channels:

| Channel | Avg Lift | Consistency | Best For | Recommendation |
|---------|----------|-------------|----------|----------------|
| TV | 15% | High (75%) | Awareness | Increase investment |
| Social | 8% | Medium (60%) | Consideration | Maintain current |
| Digital | 5% | Low (45%) | - | Review strategy |

### What Good Channel Performance Looks Like

**Strong Channel**:
- High average lift (>10%)
- High consistency (>70%)
- Significant results (p ≤ 0.05)
- Works across multiple metrics

**Weak Channel**:
- Low average lift (<5%)
- Low consistency (<50%)
- Few significant results
- Limited metric coverage

### Action Items by Channel Performance

**If a channel is performing well**:
- ✅ Increase budget allocation
- ✅ Expand to more campaigns
- ✅ Use as primary channel for that metric type
- ✅ Study what's working and replicate

**If a channel is underperforming**:
- ⚠️ Review creative strategy
- ⚠️ Check targeting
- ⚠️ Consider reducing investment
- ⚠️ Test different approaches before giving up

---

## 6. Metric Performance Analysis

### Understanding Metric Types

**Awareness Metrics**:
- Unaided Brand Awareness
- Aided Brand Awareness
- Product Category Awareness

**What they measure**: Whether people know about your brand/product.

**What good performance looks like**: 10-20% lift is typical for awareness.

**Attitude Metrics**:
- Brand Favorability
- Brand Consideration
- Brand Preference

**What they measure**: How people feel about your brand.

**What good performance looks like**: 8-15% lift is typical for attitudes.

**Behavioral Intent Metrics**:
- Purchase Intent
- Recommendation Intent
- Subscription Interest

**What they measure**: Likelihood to take action.

**What good performance looks like**: 5-12% lift is typical (harder to move).

### Metric Performance Hierarchy

**Top Performers** (15%+ lift):
- These are your strongest metrics
- Focus messaging on these areas
- Use in campaign reporting

**Good Performers** (8-15% lift):
- Solid performance
- Maintain current approach
- Look for opportunities to improve

**Moderate Performers** (3-8% lift):
- Acceptable but room for improvement
- Test different creative approaches
- Review targeting

**Underperformers** (<3% lift):
- Concerning
- Requires investigation
- May need strategy change

### What Strong Metric Performance Indicates

**If awareness metrics are strong**:
- Your creative is memorable
- Media placement is effective
- Consideration and purchase intent may follow

**If consideration metrics are strong**:
- You're moving people down the funnel
- Creative is persuasive
- Close to conversion

**If favorability metrics are strong**:
- Brand perception is improving
- Long-term brand building is working
- Foundation for future growth

---

## 7. Common Patterns and What They Mean

### Pattern 1: High Awareness, Low Consideration

**What it looks like**:
- Awareness lift: 20%
- Consideration lift: 3%

**What it means**:
- People know about you, but aren't considering you
- Creative may be memorable but not persuasive
- Messaging might not address barriers to consideration

**What to do**:
- Review creative messaging
- Add consideration-focused messaging
- Address common objections
- Highlight competitive advantages

### Pattern 2: Consistent High Performance Across Channels

**What it looks like**:
- TV: 12% lift
- Social: 11% lift
- Digital: 10% lift

**What it means**:
- Your creative/messaging is universally effective
- Brand is resonating across audiences
- Strong brand foundation

**What to do**:
- Scale successful campaigns
- Maintain current creative approach
- Consider increasing overall investment

### Pattern 3: Channel-Specific Metric Performance

**What it looks like**:
- TV: Strong awareness, weak consideration
- Social: Strong consideration, weak awareness

**What it means**:
- Different channels serve different purposes
- TV is good for reach/awareness
- Social is good for engagement/consideration

**What to do**:
- Use channel-specific strategies
- TV for awareness campaigns
- Social for consideration campaigns
- Don't expect one channel to do everything

### Pattern 4: High Variance (Inconsistent Results)

**What it looks like**:
- Average lift: 10%
- CV: 120% (high variation)
- Some months: 25% lift
- Other months: -5% lift

**What it means**:
- Results are unreliable
- Could be due to:
  - Small sample sizes
  - External factors (seasonality, competition)
  - Inconsistent creative quality

**What to do**:
- Don't make decisions based on this metric
- Investigate causes of variation
- Increase sample size if possible
- Standardize creative approach

### Pattern 5: Significant but Small Lift

**What it looks like**:
- Lift: 3%
- Significance: p = 0.01 (highly significant)
- Consistency: CV = 25% (very consistent)

**What it means**:
- The result is real and reliable
- But the effect size is small
- May not be practically meaningful

**What to do**:
- Consider if 3% lift is worth the investment
- Look for ways to amplify the effect
- May indicate need for strategy change
- Don't ignore it (it's real), but don't over-invest

---

## 8. Decision-Making Framework

### Step 1: Identify Signal Metrics

**Action**: Filter to only signal metrics (significant + consistent).

**Why**: Focus on reliable data, ignore noise.

**Output**: List of trustworthy metrics.

### Step 2: Rank by Performance

**Action**: Sort by lift percentage (highest first).

**Why**: Identify your strongest performers.

**Output**: Prioritized list of metrics.

### Step 3: Analyze by Dimension

**Action**: Break down by channel, demographic, time period.

**Why**: Understand what's working where.

**Output**: Performance matrix by dimension.

### Step 4: Identify Patterns

**Action**: Look for common themes across metrics/channels.

**Why**: Find strategic insights, not just tactical ones.

**Output**: Key insights and patterns.

### Step 5: Make Recommendations

**Action**: Based on findings, recommend:
- Budget allocation
- Channel strategy
- Creative focus
- Metric priorities

**Why**: Turn insights into actions.

**Output**: Actionable recommendations.

### Decision Matrix

Use this framework for each decision:

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Lift % | High | ___ | Higher is better |
| Significance | High | ___ | Must be significant |
| Consistency | Medium | ___ | Lower CV is better |
| Sample Size | Medium | ___ | More observations = better |
| Strategic Fit | Low | ___ | Aligns with goals? |

**Scoring**:
- Calculate weighted score
- Rank options
- Make decision based on top scores

---

## 9. Red Flags and Warnings

### Red Flag 1: Negative Lift

**What it looks like**: Lift < 0%

**What it means**: Exposed group performed worse than control.

**Possible causes**:
- Poor creative
- Wrong targeting
- Competitive interference
- Measurement error

**What to do**:
- Investigate immediately
- Review creative
- Check targeting
- Verify data quality

### Red Flag 2: High Noise Ratio

**What it looks like**: >50% of metrics classified as noise

**What it means**: Data quality issues or insufficient sample sizes.

**Possible causes**:
- Too few observations
- Inconsistent measurement
- External factors causing variation

**What to do**:
- Increase sample sizes
- Review measurement methodology
- Check for data quality issues
- Be cautious with conclusions

### Red Flag 3: Inconsistent Channel Performance

**What it looks like**: Same channel shows 20% lift one month, -5% next month

**What it means**: Unreliable channel performance.

**Possible causes**:
- Inconsistent creative quality
- Varying audience quality
- External factors

**What to do**:
- Don't make long-term decisions based on this
- Investigate month-to-month variation
- Standardize approach
- Consider pausing if consistently unreliable

### Red Flag 4: No Significant Results

**What it looks like**: All metrics have p > 0.05

**What it means**: No statistically reliable results.

**Possible causes**:
- Insufficient sample size
- Weak creative
- Poor targeting
- Measurement issues

**What to do**:
- Review campaign strategy
- Check sample sizes
- Verify targeting
- Consider pausing and reassessing

### Red Flag 5: Declining Performance Over Time

**What it looks like**: Lift decreasing month over month

**What it means**: Campaign fatigue or market changes.

**Possible causes**:
- Creative fatigue
- Market saturation
- Competitive response
- External factors

**What to do**:
- Refresh creative
- Review strategy
- Check competitive landscape
- Consider campaign pause

---

## 10. Action Items Based on Results

### If TV is Performing Best

**Actions**:
- ✅ Increase TV budget allocation
- ✅ Expand TV campaign reach
- ✅ Test new TV creative
- ✅ Consider TV-first strategy

**Metrics to track**:
- TV lift trends over time
- Cost per lift point
- Reach and frequency

### If Social is Underperforming

**Actions**:
- ⚠️ Review social creative strategy
- ⚠️ Check audience targeting
- ⚠️ Test different platforms
- ⚠️ Consider reducing investment if consistently poor

**Metrics to track**:
- Platform-specific performance
- Creative format performance
- Audience segment performance

### If Awareness is Strong but Consideration is Weak

**Actions**:
- ✅ Maintain awareness strategy
- ⚠️ Add consideration-focused messaging
- ⚠️ Review conversion funnel
- ⚠️ Test consideration-focused creative

**Metrics to track**:
- Awareness to consideration conversion
- Consideration lift trends
- Message testing results

### If Signal Metrics are Limited

**Actions**:
- ⚠️ Increase sample sizes
- ⚠️ Review measurement methodology
- ⚠️ Check data quality
- ⚠️ Be cautious with conclusions

**Metrics to track**:
- Sample size trends
- Data quality scores
- Signal-to-noise ratio

### If Multiple Channels are Performing Well

**Actions**:
- ✅ Maintain multi-channel approach
- ✅ Optimize channel mix
- ✅ Test channel synergies
- ✅ Scale successful campaigns

**Metrics to track**:
- Channel performance trends
- Cross-channel attribution
- Overall campaign ROI

---

## Quick Reference: Interpretation Checklist

When reviewing results, ask:

- [ ] Are the results statistically significant? (p ≤ 0.05)
- [ ] Are the results consistent? (CV < 50%)
- [ ] Is the sample size sufficient? (n ≥ 3, preferably more)
- [ ] Which channels are performing best?
- [ ] Which metrics are responding strongest?
- [ ] Are there any red flags?
- [ ] What patterns do I see?
- [ ] What actions should I take?

---

## Conclusion

Interpreting Kantar BLS results requires understanding:
1. **What the metrics mean** (lift, significance, consistency)
2. **What patterns to look for** (channel performance, metric performance)
3. **What to trust** (signal vs. noise)
4. **What actions to take** (based on findings)

Remember: **Not all results are equal**. Focus on signal metrics, ignore noise, and make decisions based on reliable, consistent patterns.

The goal isn't just to report numbers—it's to turn data into actionable insights that drive better marketing decisions.

---

*Document Version: 1.0*  
*Last Updated: November 2025*

