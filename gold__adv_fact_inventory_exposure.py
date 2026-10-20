from pathlib import Path
import duckdb

def main() -> None:
    script_dir = Path(__file__).resolve().parent
    db_path = (script_dir / ".." / ".." / "supply_chain_analytics.duckdb").resolve()
    con = duckdb.connect(str(db_path))

    # ---------------------------------------------------------
    # GOLD TABLE: Weekly Inventory Exposure
    #
    # Grain:
    #   One row per (WeekStartDate, LocationID, ProductSKU)
    #
    # Purpose:
    #   Combine demand (sales), stock levels (snapshots),
    #   and operational flow (movements) into one weekly table.
    # ---------------------------------------------------------

    con.execute("""
    CREATE OR REPLACE TABLE gold__fact_inventory_exposure__lite AS

    -- ---------------------------------------------------------
    -- 1. Weekly Sales (Demand)
    -- ---------------------------------------------------------
    WITH weekly_sales AS (
        SELECT
            DATE_TRUNC('week', SalesDate) AS WeekStartDate,
            LocationID,
            ProductSKU,
            SUM(Quantity) AS WeeklySalesQty
        FROM gold__fact_sales__lite
        GROUP BY 1,2,3
    ),

    -- ---------------------------------------------------------
    -- 2. Weekly Inventory (Stock Level)
    -- We use MAX as a simple proxy for week-end inventory.
    -- ---------------------------------------------------------
    weekly_inventory AS (
        SELECT
            DATE_TRUNC('week', SnapshotDate) AS WeekStartDate,
            LocationID,
            ProductSKU,
            MAX(OnHandQuantity) AS WeekEndOnHandQty
        FROM gold__fact_inventory_snapshots__lite
        GROUP BY 1,2,3
    ),

    -- ---------------------------------------------------------
    -- 3. Weekly Movements (Stock Flow)
    -- COALESCE ensures we always attach movement to a location
    -- even if one side (from/to) is null.
    -- ---------------------------------------------------------
    weekly_movements AS (
        SELECT
            DATE_TRUNC('week', MovementDate) AS WeekStartDate,
            COALESCE(ToLocationID, FromLocationID) AS LocationID,
            ProductSKU,
            SUM(Quantity) AS NetMovementQty
        FROM gold__fact_inventory_movements__lite
        GROUP BY 1,2,3
    )

    -- ---------------------------------------------------------
    -- 4. Combine All Weekly Signals
    -- FULL OUTER JOIN keeps rows even if data exists
    -- in only one of the three sources.
    -- COALESCE picks the first non-null key value.
    -- ---------------------------------------------------------
    SELECT
        COALESCE(s.WeekStartDate, i.WeekStartDate, m.WeekStartDate) AS WeekStartDate,
        COALESCE(s.LocationID, i.LocationID, m.LocationID) AS LocationID,
        COALESCE(s.ProductSKU, i.ProductSKU, m.ProductSKU) AS ProductSKU,
        s.WeeklySalesQty,
        i.WeekEndOnHandQty,
        m.NetMovementQty
    FROM weekly_sales s
    FULL OUTER JOIN weekly_inventory i
        ON s.WeekStartDate = i.WeekStartDate
       AND s.LocationID = i.LocationID
       AND s.ProductSKU = i.ProductSKU
    FULL OUTER JOIN weekly_movements m
        ON COALESCE(s.WeekStartDate, i.WeekStartDate) = m.WeekStartDate
       AND COALESCE(s.LocationID, i.LocationID) = m.LocationID
       AND COALESCE(s.ProductSKU, i.ProductSKU) = m.ProductSKU;
    """)

    con.close()
    print("✅ Created gold__fact_inventory_exposure__lite")

if __name__ == "__main__":
    main()