import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

# إعداد قاعدة البيانات
def initialize_db():
    conn = sqlite3.connect("cashier_system.db")
    cursor = conn.cursor()

    # جدول المستخدمين
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')

    # جدول المنتجات
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE,
                        name TEXT,
                        quantity INTEGER,
                        wholesale_price REAL,
                        retail_price REAL)''')

    # جدول المعاملات
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        quantity INTEGER,
                        total_price REAL,
                        date TEXT,
                        FOREIGN KEY (product_id) REFERENCES products (id))''')

    # جدول المصروفات والإيرادات
    cursor.execute('''CREATE TABLE IF NOT EXISTS financials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT,
                        amount REAL,
                        description TEXT,
                        date TEXT)''')

    # إضافة مستخدم افتراضي
    cursor.execute('''INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)''', ("admin", "1234"))

    conn.commit()
    conn.close()

# شاشة تسجيل الدخول
def login_screen():
    def login():
        username = username_entry.get()
        password = password_entry.get()

        conn = sqlite3.connect("cashier_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            root.destroy()
            main_screen()
        else:
            messagebox.showerror("فشل تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")

    root = tk.Tk()
    root.title("تسجيل الدخول")

    tk.Label(root, text="اسم المستخدم").grid(row=0, column=0)
    username_entry = tk.Entry(root)
    username_entry.grid(row=0, column=1)

    tk.Label(root, text="كلمة المرور").grid(row=1, column=0)
    password_entry = tk.Entry(root, show="*")
    password_entry.grid(row=1, column=1)

    login_button = tk.Button(root, text="دخول", command=login)
    login_button.grid(row=2, columnspan=2)

    root.mainloop()

# الشاشة الرئيسية
def main_screen():
    total_expenses = 0
    total_revenue = 0

    def open_add_product():
        def add_product():
            code = code_entry.get()
            name = name_entry.get()
            quantity = int(quantity_entry.get())
            wholesale_price = float(wholesale_entry.get())
            retail_price = float(retail_entry.get())

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT INTO products (code, name, quantity, wholesale_price, retail_price) 
                                  VALUES (?, ?, ?, ?, ?)''', (code, name, quantity, wholesale_price, retail_price))
                conn.commit()
                messagebox.showinfo("نجاح", "تمت إضافة المنتج بنجاح.")
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "كود المنتج موجود بالفعل.")
            conn.close()

        product_window = tk.Toplevel()
        product_window.title("إضافة منتج")

        tk.Label(product_window, text="كود المنتج").grid(row=0, column=0)
        code_entry = tk.Entry(product_window)
        code_entry.grid(row=0, column=1)

        tk.Label(product_window, text="اسم المنتج").grid(row=1, column=0)
        name_entry = tk.Entry(product_window)
        name_entry.grid(row=1, column=1)

        tk.Label(product_window, text="الكمية").grid(row=2, column=0)
        quantity_entry = tk.Entry(product_window)
        quantity_entry.grid(row=2, column=1)

        tk.Label(product_window, text="سعر الجملة").grid(row=3, column=0)
        wholesale_entry = tk.Entry(product_window)
        wholesale_entry.grid(row=3, column=1)

        tk.Label(product_window, text="سعر البيع").grid(row=4, column=0)
        retail_entry = tk.Entry(product_window)
        retail_entry.grid(row=4, column=1)

        tk.Button(product_window, text="إضافة", command=add_product).grid(row=5, columnspan=2)

    def open_cashier():
        def add_to_invoice():
            code = code_entry.get()

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, quantity, retail_price, wholesale_price FROM products WHERE code = ?", (code,))
            product = cursor.fetchone()

            if product:
                name, available_quantity, retail_price, wholesale_price = product[1], product[2], product[3], product[4]
                name_var.set(name)
                price_var.set(retail_price)

                if int(quantity_entry.get()) <= available_quantity:
                    total = int(quantity_entry.get()) * retail_price
                    invoice_tree.insert("", "end", values=(code, name, quantity_entry.get(), retail_price, total))
                else:
                    messagebox.showerror("خطأ", "الكمية المطلوبة غير متوفرة.")

            conn.close()

        def save_invoice():
            nonlocal total_revenue
            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()

            for row in invoice_tree.get_children():
                code, name, quantity, price, total = invoice_tree.item(row, "values")
                total_revenue += float(total)

                cursor.execute("SELECT id FROM products WHERE code = ?", (code,))
                product_id = cursor.fetchone()[0]
                cursor.execute('''INSERT INTO transactions (product_id, quantity, total_price, date) 
                                  VALUES (?, ?, ?, ?)''', (product_id, int(quantity), float(total), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (int(quantity), product_id))

            cursor.execute('''INSERT INTO financials (type, amount, description, date) 
                              VALUES (?, ?, ?, ?)''', ("إيراد", total_revenue, "فاتورة مبيعات", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            conn.close()

            for row in invoice_tree.get_children():
                invoice_tree.delete(row)

            messagebox.showinfo("نجاح", "تم حفظ الفاتورة بنجاح.")

        cashier_window = tk.Toplevel()
        cashier_window.title("الكاشير")

        tk.Label(cashier_window, text="كود المنتج").grid(row=0, column=0)
        code_entry = tk.Entry(cashier_window)
        code_entry.grid(row=0, column=1)

        tk.Label(cashier_window, text="اسم المنتج").grid(row=1, column=0)
        name_var = tk.StringVar()
        tk.Entry(cashier_window, textvariable=name_var, state="readonly").grid(row=1, column=1)

        tk.Label(cashier_window, text="سعر البيع").grid(row=2, column=0)
        price_var = tk.StringVar()
        tk.Entry(cashier_window, textvariable=price_var, state="readonly").grid(row=2, column=1)

        tk.Label(cashier_window, text="الكمية").grid(row=3, column=0)
        quantity_entry = tk.Entry(cashier_window)
        quantity_entry.grid(row=3, column=1)

        tk.Button(cashier_window, text="إضافة للفاتورة", command=add_to_invoice).grid(row=4, column=0, columnspan=2)

        invoice_tree = ttk.Treeview(cashier_window, columns=("code", "name", "quantity", "price", "total"), show="headings")
        invoice_tree.grid(row=5, column=0, columnspan=2)
        invoice_tree.heading("code", text="كود المنتج")
        invoice_tree.heading("name", text="اسم المنتج")
        invoice_tree.heading("quantity", text="الكمية")
        invoice_tree.heading("price", text="السعر")
        invoice_tree.heading("total", text="الإجمالي")

        tk.Button(cashier_window, text="حفظ الفاتورة", command=save_invoice).grid(row=6, column=0, columnspan=2)

    def open_financials():
        def add_financial():
            financial_type = type_var.get()
            amount = float(amount_entry.get())
            description = description_entry.get()

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO financials (type, amount, description, date) 
                              VALUES (?, ?, ?, ?)''', (financial_type, amount, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()

            messagebox.showinfo("نجاح", "تم إضافة المعاملة المالية بنجاح.")
            load_financials()

        def load_financials():
            for row in financial_tree.get_children():
                financial_tree.delete(row)

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT type, amount, description, date FROM financials")
            financials = cursor.fetchall()
            for financial in financials:
                financial_tree.insert("", "end", values=financial)
            conn.close()

        financials_window = tk.Toplevel()
        financials_window.title("المصروفات والإيرادات")

        tk.Label(financials_window, text="النوع").grid(row=0, column=0)
        type_var = ttk.Combobox(financials_window, values=["إيراد", "مصروف"])
        type_var.grid(row=0, column=1)
        type_var.set("إيراد")

        tk.Label(financials_window, text="المبلغ").grid(row=1, column=0)
        amount_entry = tk.Entry(financials_window)
        amount_entry.grid(row=1, column=1)

        tk.Label(financials_window, text="الوصف").grid(row=2, column=0)
        description_entry = tk.Entry(financials_window)
        description_entry.grid(row=2, column=1)

        tk.Button(financials_window, text="إضافة", command=add_financial).grid(row=3, column=0, columnspan=2)

        financial_tree = ttk.Treeview(financials_window, columns=("type", "amount", "description", "date"), show="headings")
        financial_tree.grid(row=4, column=0, columnspan=2)
        financial_tree.heading("type", text="النوع")
        financial_tree.heading("amount", text="المبلغ")
        financial_tree.heading("description", text="الوصف")
        financial_tree.heading("date", text="التاريخ")

        load_financials()

    def open_profit_loss():
        def filter_data():
            period = period_var.get()
            current_date = datetime.now()
            start_date = None

            # تحديد تاريخ البداية بناءً على الفترة المحددة
            if period == "يومي":
                start_date = current_date - timedelta(days=1)
            elif period == "أسبوعي":
                start_date = current_date - timedelta(weeks=1)
            elif period == "شهري":
                start_date = current_date - timedelta(days=30)
            elif period == "نصف سنة":
                start_date = current_date - timedelta(days=182)  # تقريبا 6 أشهر
            elif period == "سنة":
                start_date = current_date - timedelta(days=365)  # تقريبا سنة

            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

            # فتح اتصال بالقاعدة
            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()

            # استعلامات الفلاتر على الإيرادات والمصروفات
            cursor.execute('''SELECT SUM(amount) FROM financials WHERE type = "إيراد" AND date >= ?''', (start_date_str,))
            revenue = cursor.fetchone()[0] or 0

            cursor.execute('''SELECT SUM(amount) FROM financials WHERE type = "مصروف" AND date >= ?''', (start_date_str,))
            expenses = cursor.fetchone()[0] or 0

            cursor.execute('''SELECT SUM(total_price) FROM transactions WHERE date >= ?''', (start_date_str,))
            total_sales = cursor.fetchone()[0] or 0

            profit = total_sales - expenses
            cursor.close()

            # تحديث واجهة المستخدم
            profit_loss_window = tk.Toplevel()
            profit_loss_window.title("الأرباح والخسائر")

            tk.Label(profit_loss_window, text=f"إجمالي الإيرادات: {revenue}").grid(row=0, column=0)
            tk.Label(profit_loss_window, text=f"إجمالي المصروفات: {expenses}").grid(row=1, column=0)
            tk.Label(profit_loss_window, text=f"إجمالي المبيعات: {total_sales}").grid(row=2, column=0)
            tk.Label(profit_loss_window, text=f"الربح أو الخسارة: {profit}").grid(row=3, column=0)

        profit_loss_window = tk.Toplevel()
        profit_loss_window.title("الأرباح والخسائر")

        tk.Label(profit_loss_window, text="اختر الفترة الزمنية:").grid(row=0, column=0)
        period_var = ttk.Combobox(profit_loss_window, values=["يومي", "أسبوعي", "شهري", "نصف سنة", "سنة"])
        period_var.grid(row=0, column=1)
        period_var.set("يومي")  # تعيين القيمة الافتراضية

        tk.Button(profit_loss_window, text="تصفية", command=filter_data).grid(row=1, columnspan=2)

    def open_users():
        def add_user():
            username = user_entry.get()
            password = password_entry.get()

            conn = sqlite3.connect("cashier_system.db")
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT INTO users (username, password) VALUES (?, ?)''', (username, password))
                conn.commit()
                messagebox.showinfo("نجاح", "تم إضافة المستخدم بنجاح.")
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل.")
            conn.close()

        users_window = tk.Toplevel()
        users_window.title("إدارة المستخدمين")

        tk.Label(users_window, text="اسم المستخدم").grid(row=0, column=0)
        user_entry = tk.Entry(users_window)
        user_entry.grid(row=0, column=1)

        tk.Label(users_window, text="كلمة المرور").grid(row=1, column=0)
        password_entry = tk.Entry(users_window, show="*")
        password_entry.grid(row=1, column=1)

        tk.Button(users_window, text="إضافة مستخدم", command=add_user).grid(row=2, columnspan=2)

    # واجهة المستخدم الرئيسية
    root = tk.Tk()
    root.title("نظام الكاشير")

    menu = tk.Menu(root)
    root.config(menu=menu)

    manage_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="إدارة", menu=manage_menu)
    manage_menu.add_command(label="إضافة منتج", command=open_add_product)
    manage_menu.add_command(label="الكاشير", command=open_cashier)
    manage_menu.add_command(label="المصروفات والإيرادات", command=open_financials)
    manage_menu.add_command(label="الأرباح والخسائر", command=open_profit_loss)
    manage_menu.add_command(label="إدارة المستخدمين", command=open_users)

    root.mainloop()

initialize_db()
login_screen()
