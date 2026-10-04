import duckdb, numpy as np, pandas as pd
from faker import Faker

rng = np.random.default_rng(42)
Faker.seed(42)
fake = Faker()

# ---------- MASTER TABLES ----------
N_SUP, N_PROD, N_WH, N_CUST = 50, 200, 8, 300
countries = ["India", "China", "Germany", "USA", "Vietnam", "Mexico", "Brazil"]
categories = ["Electronics", "Apparel", "Home", "Food", "Industrial", "Toys"]

suppliers = pd.DataFrame({
    "supplier_id": range(1, N_SUP + 1),
    "supplier_name": [fake.company() for _ in range(N_SUP)],
    "country": rng.choice(countries, N_SUP),
    "lead_time_days": rng.integers(3, 45, N_SUP),
    "reliability_score": rng.uniform(0.70, 0.99, N_SUP).round(2),
})

unit_cost = rng.uniform(2, 200, N_PROD).round(2)
products = pd.DataFrame({
    "product_id": range(1, N_PROD + 1),
    "sku": [f"SKU-{i:05d}" for i in range(1, N_PROD + 1)],
    "product_name": [fake.catch_phrase() for _ in range(N_PROD)],
    "category": rng.choice(categories, N_PROD),
    "unit_cost": unit_cost,
    "unit_price": (unit_cost * rng.uniform(1.2, 2.0, N_PROD)).round(2),
    "supplier_id": rng.integers(1, N_SUP + 1, N_PROD),
})

warehouses = pd.DataFrame({
    "warehouse_id": range(1, N_WH + 1),
    "warehouse_name": [f"WH-{fake.city()}" for _ in range(N_WH)],
    "country": rng.choice(countries, N_WH),
    "capacity_units": rng.integers(50_000, 500_000, N_WH),
})

customers = pd.DataFrame({
    "customer_id": range(1, N_CUST + 1),
    "customer_name": [fake.company() for _ in range(N_CUST)],
    "segment": rng.choice(["Retail", "Wholesale", "Online"], N_CUST),
    "country": rng.choice(countries, N_CUST),
})

# ---------- TRANSACTIONAL: PURCHASING & INBOUND ----------
N_PO = 5000
po_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 700, N_PO), unit="D")
po_supplier = rng.integers(1, N_SUP + 1, N_PO)
lead = suppliers.set_index("supplier_id").loc[po_supplier, "lead_time_days"].values

purchase_orders = pd.DataFrame({
    "po_id": range(1, N_PO + 1),
    "supplier_id": po_supplier,
    "warehouse_id": rng.integers(1, N_WH + 1, N_PO),
    "order_date": po_dates,
    "expected_delivery_date": po_dates + pd.to_timedelta(lead, unit="D"),
    "status": rng.choice(["Open", "Received", "Cancelled"], N_PO, p=[0.1, 0.85, 0.05]),
})

prods_by_sup = products.groupby("supplier_id")["product_id"].apply(list).to_dict()
po_lines = []
for po_id, sup in zip(purchase_orders.po_id, purchase_orders.supplier_id):
    pool = prods_by_sup.get(sup) or products.product_id.tolist()
    for pid in rng.choice(pool, size=min(len(pool), rng.integers(1, 6)), replace=False):
        po_lines.append((po_id, pid, int(rng.integers(50, 2000))))
po_lines = pd.DataFrame(po_lines, columns=["po_id", "product_id", "quantity"])
po_lines.insert(0, "po_line_id", range(1, len(po_lines) + 1))
po_lines = po_lines.merge(products[["product_id", "unit_cost"]], on="product_id")

received = purchase_orders[purchase_orders.status == "Received"]
delay = rng.choice([-2, 0, 1, 3, 7, 14], len(received), p=[.1, .45, .2, .1, .1, .05])
shipments = pd.DataFrame({
    "shipment_id": range(1, len(received) + 1),
    "po_id": received.po_id.values,
    "carrier": rng.choice(["DHL", "FedEx", "Maersk", "UPS"], len(received)),
    "ship_date": received.order_date.values + pd.Timedelta(days=2),
    "actual_delivery_date": received.expected_delivery_date.values + pd.to_timedelta(delay, unit="D"),
})

# ---------- TRANSACTIONAL: SALES & OUTBOUND ----------
N_SO = 20000
so_dates = pd.to_datetime("2024-03-01") + pd.to_timedelta(rng.integers(0, 650, N_SO), unit="D")
sales_orders = pd.DataFrame({
    "so_id": range(1, N_SO + 1),
    "customer_id": rng.integers(1, N_CUST + 1, N_SO),
    "warehouse_id": rng.integers(1, N_WH + 1, N_SO),
    "order_date": so_dates,
    "status": rng.choice(["Shipped", "Delivered", "Returned", "Cancelled"], N_SO, p=[.1, .8, .05, .05]),
})
n_lines = rng.integers(1, 5, N_SO)
sales_order_lines = pd.DataFrame({
    "so_id": np.repeat(sales_orders.so_id.values, n_lines),
})
sales_order_lines["so_line_id"] = range(1, len(sales_order_lines) + 1)
sales_order_lines["product_id"] = rng.integers(1, N_PROD + 1, len(sales_order_lines))
sales_order_lines["quantity"] = rng.integers(1, 100, len(sales_order_lines))
sales_order_lines = sales_order_lines.merge(products[["product_id", "unit_price"]], on="product_id")

# ---------- LOAD INTO DUCKDB ----------
con = duckdb.connect("supply_chain.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")
tables = dict(suppliers=suppliers, products=products, warehouses=warehouses,
              customers=customers, purchase_orders=purchase_orders, po_lines=po_lines,
              shipments=shipments, sales_orders=sales_orders, sales_order_lines=sales_order_lines)
for name, df in tables.items():
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE raw.{name} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    print(f"raw.{name}: {len(df):,} rows")
con.close()