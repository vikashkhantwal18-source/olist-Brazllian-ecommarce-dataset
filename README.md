# Olist Cohort Retention Analysis

A cohort retention analysis using PostgreSQL and Python, built on the
**Brazilian E-Commerce Public Dataset by Olist** (~99,000 orders from a
Brazilian online marketplace, Sept 2016 to Oct 2018).

## Business question

When customers first buy from the marketplace in a given month, how many
of them come back and buy again in later months? And separately, how many
ever come back at all, regardless of timing?

## Headline finding

**Month-by-month retention is under 1% for every cohort after month 1.**
This is a genuine characteristic of the business, not a data error: Olist
is a marketplace where most customers buy a single, often one-off item
(furniture, electronics, etc.), rather than a subscription or grocery
service where customers are expected to return monthly.

Looking instead at whether a customer **ever** makes a second purchase,
regardless of when: **3.0% of customers (2,801 of 93,358) eventually place
a second order.** This is a small but real repeat-buyer segment that the
monthly view alone hides, since these repeat purchases are spread
unpredictably over time rather than following a monthly pattern.

**Takeaway for the business:** retention strategy for a marketplace like
this should not assume monthly repeat behaviour. A better question than
"did they come back this month" is "will they ever come back", and
identifying what distinguishes the 3% who do (state, product category,
first-order value) is a natural next step.

## Pipeline

**1. Data cleaning and joining (PostgreSQL)** — [`sql/cleaning.sql`](sql/cleaning.sql)

The dataset's `customer_id` is unique **per order**, not per person;
`customer_unique_id` identifies the actual customer across multiple
orders. The pipeline joins the orders and customers tables on
`customer_id` to attach the real `customer_unique_id` to every order —
a step that is essential before any retention analysis is possible.

Non-delivered orders (cancelled, unavailable, still processing — about
3% of orders) are kept in the cleaned table with an `is_delivered` flag
rather than removed, so they remain available for other questions
without needing to redo the cleaning.

**2. Cohort assignment and retention calculation (Python)** — [`cohort_analysis.py`](cohort_analysis.py)

- Filters to delivered orders (a delivered order is the clearest signal
  of a genuine completed purchase)
- Assigns each customer to a cohort: the month of their first delivered order
- Calculates, for each cohort, the % of customers still buying in each
  month afterwards (the classic cohort retention table)
- Separately calculates the % of each cohort that **ever** repeat-purchases,
  regardless of timing

**3. Dashboard (Power BI)**

Cohort retention heatmap and a repeat-purchase-rate comparison.
*(screenshot / .pbix link here once added)*

## Tech stack

PostgreSQL &middot; Python (pandas) &middot; Power BI

## Data source

[Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

## Repo structure

```
olist-cohort-retention/
├── data/                   (not included — see Data source above)
├── sql/
│   └── cleaning.sql
├── cohort_analysis.py
├── requirements.txt
└── README.md
```

## Running it yourself

1. Download the dataset from the link above and load `olist_customers_dataset.csv`
   and `olist_orders_dataset.csv` into PostgreSQL using `sql/cleaning.sql`
2. Export the cleaned, joined table to `data/olist_clean.csv`
3. `pip install -r requirements.txt`
4. `python cohort_analysis.py`
