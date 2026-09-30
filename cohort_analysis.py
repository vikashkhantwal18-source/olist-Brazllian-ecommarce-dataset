"""
Cohort Retention Analysis
--------------------------
Reads cleaned Olist order data (produced by sql/cleaning.sql) and builds
a monthly cohort retention table: for each group of customers who first
purchased in a given month, what % were still buying in each month after.

Input:  data/olist_clean.csv (exported from PostgreSQL)
Output: data/cohort_retention.csv (long format, ready for Power BI)
"""

import pandas as pd


def load_delivered_orders(path: str) -> pd.DataFrame:
    """Load the cleaned orders and keep delivered orders only.

    Only delivered orders count as a genuine purchase for retention
    purposes. Postgres exports its boolean column as the strings 't'/'f'
    in CSV, not Python's True/False, so that conversion happens here.
    """
    df = pd.read_csv(path, parse_dates=["order_purchase_timestamp"])
    df["is_delivered"] = df["is_delivered"] == "t"
    return df[df["is_delivered"]].copy()


def assign_cohorts(delivered: pd.DataFrame) -> pd.DataFrame:
    """Assign each customer to a cohort: the month of their first delivered order."""
    delivered = delivered.copy()
    delivered["order_month"] = delivered["order_purchase_timestamp"].dt.to_period("M")

    cohort_map = (
        delivered.groupby("customer_unique_id")["order_month"].min().rename("cohort_month")
    )
    delivered = delivered.join(cohort_map, on="customer_unique_id")
    return delivered


def build_retention_table(delivered: pd.DataFrame) -> pd.DataFrame:
    """Build the long-format cohort retention table.

    One row per (cohort_month, months_since_first) combination, with the
    count of active customers and the retention % relative to that
    cohort's original size.
    """
    delivered = delivered.copy()
    delivered["months_since_first"] = (
        delivered["order_month"] - delivered["cohort_month"]
    ).apply(lambda x: x.n)

    cohort_activity = (
        delivered.groupby(["cohort_month", "months_since_first"])["customer_unique_id"]
        .nunique()
        .reset_index(name="active_customers")
    )

    cohort_sizes = cohort_activity.loc[
        cohort_activity["months_since_first"] == 0, ["cohort_month", "active_customers"]
    ].rename(columns={"active_customers": "cohort_size"})

    cohort_activity = cohort_activity.merge(cohort_sizes, on="cohort_month")
    cohort_activity["retention_pct"] = (
        cohort_activity["active_customers"] / cohort_activity["cohort_size"] * 100
    ).round(1)

    return cohort_activity


def repeat_purchase_rate(delivered: pd.DataFrame) -> pd.DataFrame:
    """For each cohort, the % of customers who EVER made a 2nd delivered
    order, regardless of how long it took. A complementary view to the
    month-by-month table, since monthly retention in this dataset is very
    low (see README): most customers here only ever buy once.
    """
    orders_per_customer = delivered.groupby("customer_unique_id").agg(
        cohort_month=("cohort_month", "first"),
        total_orders=("order_id", "nunique"),
    )
    orders_per_customer["repeated"] = orders_per_customer["total_orders"] > 1

    summary = orders_per_customer.groupby("cohort_month").agg(
        cohort_size=("repeated", "size"),
        repeat_customers=("repeated", "sum"),
    )
    summary["repeat_rate_pct"] = (
        summary["repeat_customers"] / summary["cohort_size"] * 100
    ).round(1)

    return summary.reset_index()


def main():
    input_path = "data/olist_clean.csv"
    retention_output = "data/cohort_retention.csv"
    repeat_output = "data/repeat_purchase_rate.csv"

    delivered = load_delivered_orders(input_path)
    delivered = assign_cohorts(delivered)

    retention = build_retention_table(delivered)
    retention.to_csv(retention_output, index=False)

    repeat = repeat_purchase_rate(delivered)
    repeat.to_csv(repeat_output, index=False)

    print(f"Delivered orders: {len(delivered):,}")
    print(f"Unique customers: {delivered['customer_unique_id'].nunique():,}")
    print()
    print("Month-1 retention by cohort (first 10 cohorts):")
    month1 = retention[retention["months_since_first"] == 1].head(10)
    print(month1[["cohort_month", "retention_pct"]].to_string(index=False))
    print()
    print("Overall repeat purchase rate (ever bought again, any timing):")
    print(f"  {repeat['repeat_customers'].sum():,} of {repeat['cohort_size'].sum():,} customers "
          f"({repeat['repeat_customers'].sum() / repeat['cohort_size'].sum() * 100:.1f}%)")
    print()
    print(f"Saved {retention_output} and {repeat_output}")


if __name__ == "__main__":
    main()
