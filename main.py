import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json

class JsonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Editor")

        # Create a text area for JSON input
        self.text_area = tk.Text(root, height=20, width=50)
        self.text_area.grid(row=0, column=0, padx=10, pady=10)

        # Create a tree view for displaying JSON objects
        self.tree_view = ttk.Treeview(root, columns=("凭证日期", "凭证编号", "借方汇总", "贷方汇总"), show="headings")
        self.tree_view.heading("凭证日期", text="凭证日期")
        self.tree_view.heading("凭证编号", text="凭证编号")
        self.tree_view.heading("借方汇总", text="借方汇总")
        self.tree_view.heading("贷方汇总", text="贷方汇总")
        self.tree_view.grid(row=0, column=1, padx=10, pady=10)

        # Create buttons
        self.save_button = tk.Button(root, text="Save", command=self.save_json)
        self.save_button.grid(row=1, column=0, padx=10, pady=10)

        self.load_button = tk.Button(root, text="Load", command=self.load_json)
        self.load_button.grid(row=1, column=1, padx=10, pady=10)

        self.quit_button = tk.Button(root, text="Quit", command=self.quit_app)
        self.quit_button.grid(row=2, column=0, padx=10, pady=10)

        # Initialize database
        self.conn = sqlite3.connect('json_database.db')
        self.create_table()

        # Initialize totals
        self.借方总计 = 0.0
        self.贷方总计 = 0.0

        # Bind the tree view selection event
        self.tree_view.bind("<<TreeviewSelect>>", self.on_tree_select)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS json_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                凭证日期 TEXT,
                凭证编号 TEXT,
                借方汇总 REAL,
                贷方汇总 REAL,
                json_text TEXT
            )
        ''')
        self.conn.commit()

    def save_json(self):
        json_text = self.text_area.get("1.0", tk.END).strip()
        try:
            json_obj = json.loads(json_text)
            借方汇总 = round(sum(item["借方金额"] for item in json_obj["科目明细"]), 2)
            贷方汇总 = round(sum(item["贷方金额"] for item in json_obj["科目明细"]), 2)
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO json_data (凭证日期, 凭证编号, 借方汇总, 贷方汇总, json_text) VALUES (?, ?, ?, ?, ?)',
                           (json_obj.get("凭证日期"), json_obj.get("凭证编号"), 借方汇总, 贷方汇总, json_text))
            self.conn.commit()
            messagebox.showinfo("Success", "JSON data saved successfully.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format.")
        except KeyError as e:
            messagebox.showerror("Error", f"Missing key in JSON: {e}")

    def load_json(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT 凭证日期, 凭证编号, 借方汇总, 贷方汇总 FROM json_data')
        rows = cursor.fetchall()
        self.tree_view.delete(*self.tree_view.get_children())
        for row in rows:
            self.tree_view.insert("", "end", values=(row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}"))

        # Calculate and append the totals
        self.借方总计 = round(sum(row[2] for row in rows), 2)
        self.贷方总计 = round(sum(row[3] for row in rows), 2)
        self.tree_view.insert("", "end", values=("", "", f"{self.借方总计:.2f}", f"{self.贷方总计:.2f}"), tags=("total",))

        # Configure the tags for styling the total row
        self.tree_view.tag_configure("total", background="lightgrey")

    def on_tree_select(self, event):
        selected_item = self.tree_view.selection()[0]
        values = self.tree_view.item(selected_item, 'values')
        # Check if the selected item is the total row
        if values == ("", "", f"{self.借方总计:.2f}", f"{self.贷方总计:.2f}"):
            return
        cursor = self.conn.cursor()
        cursor.execute('SELECT json_text FROM json_data WHERE 凭证日期=? AND 凭证编号=?', (values[0], values[1]))
        row = cursor.fetchone()
        if row:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, row[0])

    def quit_app(self):
        self.conn.close()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonApp(root)
    root.mainloop()
