**Omnichannel Supply Chain Analytics Platform**

![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge&logo=sql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Medallion-blue?style=for-the-badge)

---

## 🏢 Business Context & Background

**Nordmark Retail Group** is a European omnichannel retailer operating across physical stores, central distribution centers (DCs), and an e-commerce platform. As customer shopping patterns shifted online, Nordmark expanded its fulfillment model to enable cross-channel stock transfers and direct-to-consumer delivery.

While expanding sales opportunities, this omnichannel transition introduced significant operational friction:
* Inventory is no longer dedicated to a single channel; a single unit in a warehouse or store might fulfill walk-in retail sales, e-commerce orders, or emergency store reallocations.
* Functional teams operated in silos—merchandising focused on sell-through, logistics on transit times, and store operations on local availability.
* Legacy descriptive reporting provided static historical views, making it difficult to understand root causes of stock imbalances or take proactive corrective action.

---

## 🎯 Business Problem

Despite maintaining high total inventory levels across the distribution network, Nordmark experienced persistent **localized stockouts and availability risks** at customer touchpoints. 

This created a double penalty:
1. **Lost Revenue & Customer Friction:** Inability to fulfill demand in high-performing channels/stores led to unfulfilled orders and degraded customer loyalty.
2. **Capital Leakage:** Excess stock accumulated in slow-moving channels, tying up working capital and increasing markdown exposure.

The fundamental issue was the disconnect between **demand signals, daily stock positions, and replenishment flows**.

---

## 🚩 Strategic Objectives

1. **Unify Operational Signals:** Integrate transactional sales, daily inventory snapshots, and stock movement logs into a single analytical data model.
2. **Establish Common Metrics:** Define explicit, cross-functional KPIs around inventory availability, stockout exposure, and replenishment cadence.
3. **Monitor Channel Disconnects:** Identify specific SKUs and locations where demand velocity exceeds inbound replenishment.
4. **Deliver Decision Infrastructure:** Build executive and operational Power BI dashboards structured to help planners make data-informed stock re-allocation and replenishment decisions.

---

## 📐 Data Architecture & Medallion Pipeline

The platform uses a **3-Layer Medallion Architecture** built on DuckDB and SQL to transform unstructured operational logs into structured analytical assets.


```

```
              ┌─────────────────────────────────────────┐
              │          RAW SOURCE SYSTEMS             │
              │  Sales Logs | Snapshots | Movements    │
              └────────────────────┬────────────────────┘
                                   │
                                   ▼

```

┌──────────────────────────────────────────────────────────────────────────┐
│ BRONZE LAYER (Raw Integration)                                           │
│ • Ingestion of sales, snapshots, movements, products, & locations        │
└─────────────────────────────────────┬────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────────────────┐
│ SILVER LAYER (Cleaned & Standardized)                                    │
│ • Data parsing & ISO date formatting                                     │
│ • Standardized movement types (SALE, REPLENISH, ADJUSTMENT)             │
│ • Referential integrity validation & key coverage checks                │
└─────────────────────────────────────┬────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GOLD LAYER (Business Aggregations & Analytical Exposures)                │
│ • Full Outer Joined Weekly Exposure: gold__fact_inventory_exposure__lite │
│ • Combines Weekly Sales Demand, Week-End Stock, and Net Flow             │
└─────────────────────────────────────┬────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (Power BI Dashboard Suite)                            │
│ • Executive Overview | Sales Analysis | Inventory | Movements            │
└──────────────────────────────────────────────────────────────────────────┘

```

---

## 🛠️ Data Modeling & Dimensional Schema

The Gold presentation layer follows a **Kimball Star Schema** design optimized for analytical query performance and DAX calculations.

### Fact Tables
* **`gold__fact_sales__lite`**: Granular transactional demand record (Quantity, Unit Price, Sales Date, Channel, Location, SKU).
* **`gold__fact_inventory_snapshots__lite`**: Daily stock level snapshots by Location and SKU.
* **`gold__fact_inventory_movements__lite`**: Event stream for inventory transfers (`SALE`, `REPLENISH`, `ADJUSTMENT`).
* **`gold__fact_inventory_exposure__lite`**: Unified weekly aggregated model joining weekly sales demand, week-end on-hand quantities, and net movement flow across all nodes.

### Dimension Tables
* **`silver__product_master__lite`**: SKU level reference (Product Name, Category, Brand, Unit Cost).
* **`silver__location_master__lite`**: Fulfillment node details (Location ID, Location Name, Type [Store/DC/Web], Region).
* **`dim_date`**: Custom DAX calendar table supporting ISO week numbering, period-to-date (MTD, QTD, YTD), and dynamic rolling flags (Last 3/6/12 Months).

---

## ⚙️ Process & Implementation Steps

### Phase 1: Data Validation & Silver Normalization
* Standardized raw date strings into ISO date format.
* Applied domain rules to classify inventory movement types into normalized enumerations (`SALE`, `REPLENISH`, `ADJUSTMENT`).
* Executed 5 automated SQL quality checks covering SKU/Location uniqueness, referential integrity coverage, date null rates, and quantity range sanity checks.

### Phase 2: Gold Layer Transformation (DuckDB & Python)
* Built `gold__fact_inventory_exposure__lite` via Python SQL pipeline (`gold__adv_fact_inventory_exposure.py`).
* Aggregated weekly demand (`WeeklySalesQty`), week-end stock positions (`WeekEndOnHandQty`), and stock transfers (`NetMovementQty`) using `FULL OUTER JOIN` logic to preserve stock records even when no sales occurred in a given week.

### Phase 3: Metric Engineering & Power BI Development
* Implemented dynamic DAX measures for core KPIs:
  * **Total Sales Volume:** `SUM(gold__fact_sales__lite[Quantity])`
  * **Revenue Proxy:** `SUMX(gold__fact_sales__lite, [Quantity] * [UnitPrice])`
  * **Week-End Inventory:** `MAX(gold__fact_inventory_snapshots__lite[OnHandQuantity])`
* Established standardized dashboard views organized by operational workflow:
  1. **Executive Overview:** High-level network demand and inventory position health.
  2. **Sales Analysis:** Demand patterns by category, brand, and sales channel.
  3. **Inventory Analysis:** SKU stock exposure, low-stock warnings, and localized stockout risk.
  4. **Movement Analysis:** Transfer cadence, replenishment frequency, and operational flow.

---

## 📊 Business Key Metrics & KPIs

| Metric Domain | Key Performance Indicator | Business Purpose |
| :--- | :--- | :--- |
| **Availability Risk** | Stockout Risk Frequency | Identifies locations and SKUs where stock drops below critical safety levels. |
| **Demand Velocity** | Weekly Sales Quantity | Tracks sales demand across 40 SKUs and 5 nodes (Stores, DC, Web). |
| **Inventory Health** | Week-End On-Hand Quantity | Monitors stock holding levels to spot overstocked vs. depleted items. |
| **Replenishment Cadence** | Net Movement Quantity | Evaluates if transfer movements (`REPLENISH`) match actual sales burn rates. |
| **Financial Impact** | Sales Revenue Proxy | Quantifies financial impact ($\text{Quantity} \times \text{Unit Price}$) across product categories. |

---

## 🔍 Key Insights & Operational Takeaways

1. **Demand vs. Replenishment Misalignment:** Fast-moving electronics and personal care SKUs exhibited demand spikes that exceeded replenishment transfer rates, leading to recurring stock exposure in physical stores.
2. **Channel-Specific Stock Exposure:** E-commerce (Web) demand surged faster than direct replenishment cycles, forcing reactive stock transfers from retail stores rather than central DCs.
3. **Working Capital Optimization:** Analysis highlighted slow-moving household items maintaining high on-hand balances, identifying working capital that can be freed up through targeted reallocations.

---

## 📂 Repository Structure


```

.
├── 5_Module_Overview.pdf                       # Strategic portfolio & framing guidelines
├── Module_1_Overview.pdf                       # Business context & domain overview
├── Module_2_Data_Quality_Checks_Silver.pdf     # Silver layer validation criteria
├── Module_2_Stakeholders_Data_Needs.pdf        # Stakeholder mapping & requirement matrix
├── dim_date.txt                                # DAX code for custom dynamic Date Dimension
├── gold__adv_fact_inventory_exposure.py        # Python script generating Gold exposure table
├── raw__location_master__lite.xlsx             # Location reference data
└── supply_chain_analytics.duckdb              # Embedded DuckDB database instance

```

---

## 👤 Author & Contact

* **Shaik Mohammad Ismael Jabivulla**
* **Role:** Business Operations or Procurement Analyst / MIS Analyst
* **LinkedIn:** [linkedin.com/in/jabivulla369](https://linkedin.com/in/jabivulla369)
* **GitHub:** [github.com/Jabivulla369](https://github.com/Jabivulla369)

```
