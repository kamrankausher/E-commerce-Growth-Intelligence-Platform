-- 1. Revenue by state
SELECT c.customer_state, ROUND(SUM(op.payment_value), 2) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_payments op ON o.order_id = op.order_id
GROUP BY c.customer_state
ORDER BY revenue DESC;

-- 2. Monthly revenue trend
SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
       ROUND(SUM(op.payment_value), 2) AS revenue
FROM orders o
JOIN order_payments op ON o.order_id = op.order_id
GROUP BY 1
ORDER BY 1;

-- 3. Monthly retention (CTE + self-join)
WITH customer_months AS (
    SELECT c.customer_unique_id,
           DATE_TRUNC('month', o.order_purchase_timestamp) AS month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
), retained AS (
    SELECT a.month,
           COUNT(DISTINCT a.customer_unique_id) AS active_customers,
           COUNT(DISTINCT b.customer_unique_id) AS retained_next_month
    FROM customer_months a
    LEFT JOIN customer_months b
      ON a.customer_unique_id = b.customer_unique_id
     AND b.month = a.month + INTERVAL '1 month'
    GROUP BY a.month
)
SELECT month,
       active_customers,
       retained_next_month,
       ROUND(100.0 * retained_next_month / NULLIF(active_customers, 0), 2) AS retention_rate_pct
FROM retained
ORDER BY month;

-- 4. Repeat purchase rate
WITH customer_orders AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
)
SELECT ROUND(100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_purchase_rate_pct
FROM customer_orders;

-- 5. Top sellers by GMV
SELECT oi.seller_id,
       ROUND(SUM(oi.price + oi.freight_value), 2) AS gmv,
       COUNT(DISTINCT oi.order_id) AS orders
FROM order_items oi
GROUP BY oi.seller_id
ORDER BY gmv DESC
LIMIT 10;

-- 6. Cohort analysis (month 0 to month 6)
WITH cohorts AS (
    SELECT c.customer_unique_id,
           DATE_TRUNC('month', MIN(o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
), customer_activity AS (
    SELECT c.customer_unique_id,
           DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
)
SELECT co.cohort_month,
       EXTRACT(MONTH FROM AGE(ca.order_month, co.cohort_month)) AS month_number,
       COUNT(DISTINCT ca.customer_unique_id) AS active_customers
FROM cohorts co
JOIN customer_activity ca ON co.customer_unique_id = ca.customer_unique_id
WHERE EXTRACT(MONTH FROM AGE(ca.order_month, co.cohort_month)) BETWEEN 0 AND 6
GROUP BY 1, 2
ORDER BY 1, 2;

-- 7. RFM-style customer ranking using windows
WITH customer_metrics AS (
    SELECT c.customer_unique_id,
           MAX(o.order_purchase_timestamp) AS last_purchase,
           COUNT(DISTINCT o.order_id) AS frequency,
           SUM(op.payment_value) AS monetary
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_payments op ON o.order_id = op.order_id
    GROUP BY c.customer_unique_id
)
SELECT customer_unique_id,
       CURRENT_DATE - DATE(last_purchase) AS recency_days,
       frequency,
       monetary,
       NTILE(5) OVER (ORDER BY CURRENT_DATE - DATE(last_purchase) DESC) AS recency_score,
       NTILE(5) OVER (ORDER BY frequency) AS frequency_score,
       NTILE(5) OVER (ORDER BY monetary) AS monetary_score
FROM customer_metrics;

-- 8. Category-level average review score and sales
SELECT p.product_category_name,
       ROUND(AVG(r.review_score), 2) AS avg_review,
       COUNT(DISTINCT oi.order_id) AS orders
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN order_reviews r ON oi.order_id = r.order_id
GROUP BY p.product_category_name
HAVING COUNT(DISTINCT oi.order_id) > 50
ORDER BY avg_review DESC;

-- 9. Delivery delay by state
SELECT c.customer_state,
       ROUND(AVG(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date)) / 86400), 2) AS avg_delay_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delay_days DESC;

-- 10. Payment method mix with percentage
WITH payment_mix AS (
    SELECT payment_type,
           COUNT(*) AS txns
    FROM order_payments
    GROUP BY payment_type
)
SELECT payment_type,
       txns,
       ROUND(100.0 * txns / SUM(txns) OVER (), 2) AS txn_pct
FROM payment_mix
ORDER BY txns DESC;

-- 11. Best weekday by revenue
SELECT TO_CHAR(o.order_purchase_timestamp, 'Dy') AS weekday,
       ROUND(SUM(op.payment_value), 2) AS revenue
FROM orders o
JOIN order_payments op ON o.order_id = op.order_id
GROUP BY 1
ORDER BY revenue DESC;
