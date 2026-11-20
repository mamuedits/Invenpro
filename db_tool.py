"""
Invenpro Direct Database Management CLI Tool
Run: python db_tool.py
"""
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

def get_connection():
    return sqlite3.connect(DB_FILE)

def list_products():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.name, c.name, p.current_stock, p.unit, p.purchase_price, p.minimum_stock
        FROM inventory_product p
        JOIN inventory_category c ON p.category_id = c.id
        ORDER BY p.id;
    """)
    rows = c.fetchall()
    print("\n" + "=" * 80)
    print(f"{'ID':<4} {'Product Name':<26} {'Category':<18} {'Stock':<10} {'Unit':<8} {'Price (₹)':<10}")
    print("-" * 80)
    for r in rows:
        print(f"{r[0]:<4} {r[1]:<26} {r[2]:<18} {r[3]:<10} {r[4]:<8} ₹{r[5]:<9.2f}")
    print("=" * 80 + "\n")
    conn.close()

def update_product():
    list_products()
    try:
        pid = int(input("Enter Product ID to update: ").strip())
    except ValueError:
        print("Invalid ID.")
        return

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, current_stock, purchase_price, unit FROM inventory_product WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        print(f"Product ID {pid} not found.")
        conn.close()
        return

    print(f"\nEditing: {row[1]} (Current Stock: {row[2]} {row[4]}, Current Price: ₹{row[3]})")
    new_stock = input(f"Enter new stock quantity [leave blank to keep {row[2]}]: ").strip()
    new_price = input(f"Enter new purchase price [leave blank to keep ₹{row[3]}]: ").strip()

    stock_val = float(new_stock) if new_stock else row[2]
    price_val = float(new_price) if new_price else row[3]

    c.execute("""
        UPDATE inventory_product
        SET current_stock = ?, purchase_price = ?, updated_at = datetime('now')
        WHERE id = ?;
    """, (stock_val, price_val, pid))
    conn.commit()
    print(f"Successfully updated '{row[1]}' -> Stock: {stock_val} {row[4]}, Price: ₹{price_val:.2f}\n")
    conn.close()

def run_custom_sql():
    conn = get_connection()
    c = conn.cursor()
    print("\nEnter custom SQL query (e.g., SELECT * FROM inventory_product;):")
    query = input("SQL > ").strip()
    if not query:
        return
    try:
        c.execute(query)
        if query.strip().upper().startswith("SELECT"):
            col_names = [desc[0] for desc in c.description]
            print("\nColumns:", " | ".join(col_names))
            print("-" * 60)
            rows = c.fetchall()
            for r in rows:
                print(r)
            print(f"Total rows: {len(rows)}\n")
        else:
            conn.commit()
            print(f"Query executed successfully. Rows affected: {c.rowcount}\n")
    except Exception as e:
        print("SQL Error:", e)
    finally:
        conn.close()

def list_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%';")
    tables = [row[0] for row in c.fetchall()]
    print("\nInvenpro Database Tables:")
    for t in tables:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        count = c.fetchone()[0]
        print(f"  - {t:<35} ({count} rows)")
    print()
    conn.close()

def main():
    while True:
        print("========================================")
        print("       Invenpro Direct DB Tool         ")
        print("========================================")
        print("1. View all products & stock levels")
        print("2. Update a product's stock or price")
        print("3. List database tables")
        print("4. Execute custom SQL query (SELECT / UPDATE / INSERT)")
        print("5. Exit")
        choice = input("\nSelect an option (1-5): ").strip()

        if choice == '1':
            list_products()
        elif choice == '2':
            update_product()
        elif choice == '3':
            list_tables()
        elif choice == '4':
            run_custom_sql()
        elif choice == '5':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please select 1-5.\n")

if __name__ == '__main__':
    main()

