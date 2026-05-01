-- ============================================================================
-- E-commerce Growth Intelligence Platform — SQL Analytics
-- 12 advanced queries using CTEs, window functions, and aggregations
-- Dataset: Brazilian Olist E-Commerce (PostgreSQL)
-- ============================================================================


-- ─── 1. Revenue by State (Top 10) ──────────────────────────────────────────
-- Business Question: Which states generate the most revenue?
-- Techniques: JOIN, GROUP BY, ORDER BY, ROUND

SELECT
    c.customer_state                             AS state,
    COUNT(DISTINCT o.order_id)                   AS total_orders,
    ROUND(SUM(op.payment_value)::numeric, 2)     AS total_revenue,
    ROUND(AVG(op.payment_value)::numeric, 2)     AS avg_order_value
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC
LIMIT 10;


-- ─── 2. Monthly Revenue Trend ──────────────────────────────────────────────
-- Business Question: How does revenue trend month-over-month?
-- Techniques: DATE_TRUNC, Window Function (LAG), percentage growth

WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        ROUND(SUM(op.payment_value)::numeric, 2)              AS revenue
    FROM orders o
    JOIN order_payments op ON o.order_id = op.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY DATE_TRUNC('month', o.order_purchase_timestamp)
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month)                                         AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2
    )                                                                           AS growth_pct
FROM monthly_revenue
ORDER BY month;


-- ─── 3. Customer Cohort Analysis ───────────────────────────────────────────
-- Business Question: How does retention look across monthly acquisition cohorts?
-- Techniques: CTE, DATE_TRUNC, DENSE_RANK, cohort offset

WITH first_purchase AS (
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', MIN(o.order_purchase_timestamp))::date AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
orders_with_cohort AS (
    SELECT
        fp.customer_unique_id,
        fp.cohort_month,
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS order_month
    FROM first_purchase fp
    JOIN customers c ON fp.customer_unique_id = c.customer_unique_id
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
)
SELECT
    cohort_month,
    (EXTRACT(YEAR FROM order_month) - EXTRACT(YEAR FROM cohort_month)) * 12
        + EXTRACT(MONTH FROM order_month) - EXTRACT(MONTH FROM cohort_month) AS month_offset,
    COUNT(DISTINCT customer_unique_id) AS active_customers
FROM orders_with_cohort
GROUP BY cohort_month, month_offset
ORDER BY cohort_month, month_offset;


-- ─── 4. Repeat Purchase Rate ───────────────────────────────────────────────
-- Business Question: What % of customers make more than one purchase?
-- Techniques: CTE, HAVING, subquery

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    ) AS repeat_purchase_rate_pct
FROM customer_orders;


-- ─── 5. Top 10 Sellers by Revenue ──────────────────────────────────────────
-- Business Question: Who are the highest-revenue sellers?
-- Techniques: JOIN, GROUP BY, aggregate

SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS orders_fulfilled,
    ROUND(SUM(oi.price)::numeric, 2) AS total_revenue,
    ROUND(AVG(oi.price)::numeric, 2) AS avg_item_price
FROM order_items oi
JOIN sellers s ON oi.seller_id = s.seller_id
GROUP BY s.seller_id, s.seller_city, s.seller_state
ORDER BY total_revenue DESC
LIMIT 10;


-- ─── 6. Monthly Retention Rate ─────────────────────────────────────────────
-- Business Question: What fraction of customers from month M return in month M+1?
-- Techniques: CTE, SELF JOIN, window function

WITH monthly_customers AS (
    SELECT DISTINCT
        c.customer_unique_id,
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS active_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),
retention AS (
    SELECT
        a.active_month,
        COUNT(DISTINCT a.customer_unique_id) AS active_count,
        COUNT(DISTINCT b.customer_unique_id) AS retained_count
    FROM monthly_customers a
    LEFT JOIN monthly_customers b
        ON a.customer_unique_id = b.customer_unique_id
        AND b.active_month = a.active_month + INTERVAL '1 month'
    GROUP BY a.active_month
)
SELECT
    active_month,
    active_count,
    retained_count,
    ROUND(retained_count * 100.0 / NULLIF(active_count, 0), 2) AS retention_rate_pct
FROM retention
ORDER BY active_month;


-- ─── 7. Product Category Performance ───────────────────────────────────────
-- Business Question: Which product categories drive the most revenue?
-- Techniques: JOIN, LEFT JOIN for translation, aggregate

SELECT
    COALESCE(ct.product_category_name_english, p.product_category_name) AS category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.order_item_id)       AS total_items_sold,
    ROUND(SUM(oi.price)::numeric, 2) AS total_revenue,
    ROUND(AVG(oi.price)::numeric, 2) AS avg_price,
    ROUND(AVG(r.review_score)::numeric, 2) AS avg_review_score
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
LEFT JOIN order_reviews r ON oi.order_id = r.order_id
GROUP BY COALESCE(ct.product_category_name_english, p.product_category_name)
ORDER BY total_revenue DESC
LIMIT 15;


-- ─── 8. Delivery Performance Analysis ──────────────────────────────────────
-- Business Question: How does actual delivery compare to estimated delivery?
-- Techniques: DATE arithmetic, CASE, window function (PERCENTILE_CONT)

WITH delivery_stats AS (
    SELECT
        o.order_id,
        c.customer_state,
        o.order_delivered_customer_date - o.order_purchase_timestamp AS actual_days,
        o.order_estimated_delivery_date - o.order_purchase_timestamp AS estimated_days,
        CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
                THEN 'on_time'
            ELSE 'late'
        END AS delivery_status
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
)
SELECT
    customer_state,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN delivery_status = 'late' THEN 1 ELSE 0 END) AS late_orders,
    ROUND(
        SUM(CASE WHEN delivery_status = 'late' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    ) AS late_pct,
    ROUND(AVG(EXTRACT(EPOCH FROM actual_days) / 86400)::numeric, 1) AS avg_delivery_days
FROM delivery_stats
GROUP BY customer_state
ORDER BY late_pct DESC;


-- ─── 9. RFM Segmentation ──────────────────────────────────────────────────
-- Business Question: How can we segment customers by Recency, Frequency, Monetary?
-- Techniques: CTE, NTILE window function, CASE for segment labels

WITH rfm_raw AS (
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_purchase,
        COUNT(DISTINCT o.order_id)      AS frequency,
        ROUND(SUM(op.payment_value)::numeric, 2) AS monetary
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_payments op ON o.order_id = op.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scored AS (
    SELECT
        customer_unique_id,
        last_purchase,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY last_purchase DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)       AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)         AS m_score
    FROM rfm_raw
)
SELECT
    customer_unique_id,
    r_score, f_score, m_score,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Needs Attention'
    END AS segment
FROM rfm_scored
ORDER BY rfm_total DESC;


-- ─── 10. Payment Method Analysis ───────────────────────────────────────────
-- Business Question: How do different payment methods affect order value?
-- Techniques: GROUP BY, aggregate, RANK window function

SELECT
    payment_type,
    COUNT(*) AS transaction_count,
    ROUND(SUM(payment_value)::numeric, 2) AS total_value,
    ROUND(AVG(payment_value)::numeric, 2) AS avg_value,
    ROUND(AVG(payment_installments)::numeric, 1) AS avg_installments,
    RANK() OVER (ORDER BY SUM(payment_value) DESC) AS revenue_rank
FROM order_payments
GROUP BY payment_type
ORDER BY total_value DESC;


-- ─── 11. Customer Lifetime Value (CLV) Distribution ────────────────────────
-- Business Question: What does the CLV distribution look like?
-- Techniques: CTE, PERCENTILE_CONT, statistical aggregates

WITH clv AS (
    SELECT
        c.customer_unique_id,
        ROUND(SUM(op.payment_value)::numeric, 2) AS lifetime_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_payments op ON o.order_id = op.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*) AS total_customers,
    ROUND(AVG(lifetime_value), 2) AS avg_clv,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lifetime_value)::numeric, 2) AS median_clv,
    ROUND(MIN(lifetime_value), 2) AS min_clv,
    ROUND(MAX(lifetime_value), 2) AS max_clv,
    ROUND(STDDEV(lifetime_value)::numeric, 2) AS stddev_clv
FROM clv;


-- ─── 12. Review Sentiment by Category ─────────────────────────────────────
-- Business Question: Which categories have the best/worst reviews?
-- Techniques: CTE, LEFT JOIN, conditional aggregation

WITH category_reviews AS (
    SELECT
        COALESCE(ct.product_category_name_english, p.product_category_name) AS category,
        r.review_score
    FROM order_reviews r
    JOIN order_items oi ON r.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE r.review_score IS NOT NULL
)
SELECT
    category,
    COUNT(*) AS total_reviews,
    ROUND(AVG(review_score), 2) AS avg_score,
    SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END) AS positive_reviews,
    SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) AS negative_reviews,
    ROUND(
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    ) AS positive_rate_pct
FROM category_reviews
GROUP BY category
HAVING COUNT(*) >= 50
ORDER BY avg_score DESC;
