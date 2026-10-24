-- 1. Overall sales summary
SELECT
    SUM(amount) AS total_sales,
    SUM(profit) AS total_profit,
    SUM(quantity) AS total_quantity
FROM sales;

-- 2. Sales by category
SELECT
    category,
    SUM(amount) AS total_sales,
    SUM(profit) AS total_profit
FROM sales
GROUP BY category
ORDER BY total_sales DESC;

-- 3. Sales by state
SELECT
    state,
    SUM(amount) AS total_sales
FROM sales
GROUP BY state
ORDER BY total_sales DESC;

-- 4. Top sub-categories by sales
SELECT
    sub_category,
    SUM(amount) AS total_sales
FROM sales
GROUP BY sub_category
ORDER BY total_sales DESC
LIMIT 10;

-- 5. Monthly sales
SELECT
    year_month,
    SUM(amount) AS total_sales
FROM sales
GROUP BY year_month
ORDER BY year_month;