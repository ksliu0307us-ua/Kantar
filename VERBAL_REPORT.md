# Verbal Report for Moshe - BLS Project Update

## Full Verbal Report (3-5 minutes)

---

**Opening:**

Hey Moshe, so I wanted to give you an update on the BLS work. Things are going really well - I've got the system built and running, and I've got some initial findings to share.

**What I Built:**

So, you asked me to get the Kantar data into a usable format and start identifying consistent patterns. I've built a complete automated analysis pipeline that does exactly that.

The system automatically loads all the CSV files - the metrics, the filter metadata, everything - and it joins them together using FILTER_ID as the key. It cleans the data, extracts channels and demographics from the filter names, and then runs the analysis to separate signal from noise.

I also built a web UI using Streamlit, so anyone on the team can run the analysis without writing code. Just click a few buttons and get results. Everything's organized into a clean structure with full documentation.

**What the Data Shows:**

I ran the analysis on our current Kantar data, and here's what we're seeing:

We processed about 21,500 observations across 347 unique filters. The system identified 26 metrics that are showing consistent signal across multiple filters - these are the ones we can actually trust.

The top performers right now are DashPass-related metrics. Specifically, DashPass Benefit Awareness - things like the HBO subscription benefit - is showing consistent lift around 2 percent. Brand Affinity and DashPass Worth are also in that top tier, showing around 1 to 2 percent lift.

Now, these are small numbers - we're talking 1 to 3 percent lift - but the key thing is they're consistent. The system is showing these metrics perform reliably across different channels and demographics, which is what we're looking for.

**The Reality Check:**

Here's the honest assessment: Most of our metrics right now are classified as "noise" - meaning we need more data before we can confidently say they're showing real patterns. That's actually the system working correctly. It's being appropriately cautious.

We're seeing data across multiple channels - OTT, Social, Podcast, and others - but the channel-level differences aren't strong enough yet to make confident calls. Again, this is expected with the amount of data we have so far.

**What This Means:**

The good news is the system is working exactly as designed. We now have:
- Complete visibility into all our metrics
- A clear baseline of current performance
- Automatic identification of which metrics we can trust vs. which need more data
- A way to track improvements as we get more monthly snapshots

The DashPass messaging is showing early positive signals, which is encouraging. As we get more data over the coming months, we should see more metrics move from "noise" to "signal" - that's when we can make stronger strategic decisions.

**Next Steps:**

The system is production-ready. As new monthly CSV snapshots come in from Kantar, we can easily process them. The analysis will automatically update, and we'll start seeing clearer patterns as the sample sizes grow.

I'm ready to integrate with Snowflake when those product updates are available in Q1. For now, the CSV workflow is solid and automated.

**Closing:**

So bottom line: The foundation is built, the system is working, and we have our baseline established. The initial results show some promising signals, especially around DashPass messaging, but we need more data to see stronger patterns - which is exactly what we expected.

Everything's documented and ready for the team to use. Happy to walk you through the results or demo the UI anytime you want to see it in action.

---

## Short Verbal Report (1-2 minutes)

---

Hey Moshe, quick update on BLS:

I've got the analysis system built and running. It automatically processes all the Kantar data, joins the tables, and identifies which metrics are showing consistent signal versus noise.

I ran it on our current data - about 21,500 observations across 347 filters. The system found 26 metrics with consistent cross-filter signal. Top performers are DashPass Benefit Awareness metrics, showing around 2 percent lift, and Brand Affinity.

The reality is most metrics are still classified as "noise" - meaning we need more data before we can confidently act on them. That's the system working correctly, being appropriately cautious.

The good news is we now have complete visibility, a clear baseline, and an automated way to track improvements as we get more monthly data. The system is production-ready for regular runs.

I also built a web UI so the team can use it without coding. Everything's documented and ready to go.

Happy to walk you through the results or demo it anytime.

---

## Very Brief Verbal Update (30 seconds)

---

Hey Moshe, BLS update:

Got the analysis system built and running. Processed our current data - found 26 metrics with consistent signal, top ones are DashPass Benefit Awareness showing around 2 percent lift.

Most metrics still need more data before we can act on them, which is expected. System is production-ready and automated for monthly runs. Also built a web UI for the team.

Everything's documented and ready. Happy to show you the results anytime.

---

## Tips for Delivery:

1. **Pause for questions** - After mentioning key numbers, pause briefly
2. **Emphasize the value** - "The system is working correctly" and "We have visibility now"
3. **Be honest about limitations** - "We need more data" shows you understand the situation
4. **End with action** - "Happy to demo" shows you're ready to engage
5. **Use natural transitions** - "So," "Now," "Here's the thing" - makes it conversational

