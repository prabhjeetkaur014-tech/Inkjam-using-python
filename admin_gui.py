"""
inkJam Desktop Admin & Analytics Console.
Built with Tkinter, PhotoImage, Pillow (PIL), NumPy, Pandas, Matplotlib, and Seaborn.
Provides full platform management and visual data science dashboards.
"""
import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from database import db
from analytics import compute_analytics, generate_all_charts, export_data_to_csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "img", "logo.png")
CHARTS_DIR = os.path.join(BASE_DIR, "img", "charts")

# Color Theme
COLOR_PRIMARY = "#3858e9"
COLOR_SECONDARY = "#2a45c4"
COLOR_BG = "#f4f2ee"
COLOR_CARD = "#ffffff"
COLOR_TEXT = "#161a2e"
COLOR_MUTED = "#6b7280"
COLOR_ACCENT = "#e0245e"

class InkJamAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("inkJam – Python Admin & Analytics Console")
        self.root.geometry("1100x720")
        self.root.minsize(950, 600)
        self.root.configure(bg=COLOR_BG)

        # Pre-load charts
        generate_all_charts()
        self.chart_files = [
            ("Category Breakdown (Seaborn)", os.path.join(CHARTS_DIR, "category_distribution.png")),
            ("Ratings Analysis (Matplotlib)", os.path.join(CHARTS_DIR, "ratings_breakdown.png")),
            ("Word Length & Read Time (Seaborn)", os.path.join(CHARTS_DIR, "reading_time_dist.png")),
            ("Executive Summary Dashboard", os.path.join(CHARTS_DIR, "overview_dashboard.png"))
        ]
        self.current_chart_idx = 3  # Start with multi-panel overview

        self._init_styles()
        self._build_header()
        self._build_tabs()
        self._build_statusbar()

        self.refresh_all_data()

    def _init_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Notebook styling
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#e2e8f0", foreground=COLOR_TEXT,
                        padding=[16, 8], font=("Helvetica", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_PRIMARY)],
                  foreground=[("selected", "#ffffff")])

        # Treeview styling
        style.configure("Treeview", background="#ffffff", foreground=COLOR_TEXT,
                        rowheight=26, fieldbackground="#ffffff", font=("Helvetica", 9))
        style.configure("Treeview.Heading", font=("Helvetica", 9, "bold"),
                        background="#eef1ff", foreground=COLOR_PRIMARY)
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", COLOR_TEXT)])

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg=COLOR_PRIMARY, height=72)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        # Brand / Logo using Pillow and ImageTk
        logo_box = tk.Frame(header_frame, bg=COLOR_PRIMARY)
        logo_box.pack(side=tk.LEFT, padx=20, pady=8)

        if os.path.exists(LOGO_PATH):
            try:
                pil_logo = Image.open(LOGO_PATH).resize((44, 44), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(pil_logo)
                logo_lbl = tk.Label(logo_box, image=self.logo_img, bg=COLOR_PRIMARY)
                logo_lbl.pack(side=tk.LEFT, padx=(0, 10))
            except Exception:
                pass

        title_lbl = tk.Label(logo_box, text="inkJam", font=("Georgia", 22, "bold"), fg="#ffffff", bg=COLOR_PRIMARY)
        title_lbl.pack(side=tk.LEFT)
        sub_lbl = tk.Label(logo_box, text=" | Python Control & Data Analytics", font=("Helvetica", 11), fg="#cbd5e1", bg=COLOR_PRIMARY)
        sub_lbl.pack(side=tk.LEFT, padx=(6, 0), pady=(4, 0))

        # Quick action buttons on header
        btn_box = tk.Frame(header_frame, bg=COLOR_PRIMARY)
        btn_box.pack(side=tk.RIGHT, padx=20, pady=12)

        web_btn = tk.Button(btn_box, text=" Open Web App", font=("Helvetica", 9, "bold"),
                            bg="#ffffff", fg=COLOR_PRIMARY, relief=tk.FLAT, padx=12, pady=5,
                            cursor="hand2", command=self.open_web_app)
        web_btn.pack(side=tk.RIGHT, padx=6)

        export_btn = tk.Button(btn_box, text=" Export CSV (Pandas)", font=("Helvetica", 9, "bold"),
                               bg=COLOR_SECONDARY, fg="#ffffff", relief=tk.FLAT, padx=12, pady=5,
                               cursor="hand2", command=self.export_csv)
        export_btn.pack(side=tk.RIGHT, padx=6)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # 1. Analytics & Visualizations Tab
        self.tab_analytics = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_analytics, text="  Analytics & Charts (Seaborn/Matplotlib) ")
        self._setup_analytics_tab()

        # 2. Posts Manager Tab
        self.tab_posts = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_posts, text="  Manage Posts  ")
        self._setup_posts_tab()

        # 3. User Directory Tab
        self.tab_users = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_users, text="  User Accounts  ")
        self._setup_users_tab()

        # 4. Feedback & Reviews Tab
        self.tab_reviews = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_reviews, text="  Reviews & Ratings  ")
        self._setup_reviews_tab()

        # 5. Contact Inquiries Tab
        self.tab_messages = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_messages, text="  Contact Messages  ")
        self._setup_messages_tab()

    def _setup_analytics_tab(self):
        # Top KPI Cards
        kpi_frame = tk.Frame(self.tab_analytics, bg=COLOR_BG)
        kpi_frame.pack(fill=tk.X, pady=(10, 8))

        self.kpi_posts = self._create_kpi_card(kpi_frame, "Total Posts", "0", "#3858e9", 0)
        self.kpi_users = self._create_kpi_card(kpi_frame, "Registered Users", "0", "#10b981", 1)
        self.kpi_rating = self._create_kpi_card(kpi_frame, "Average Rating", "0.0★", "#f59e0b", 2)
        self.kpi_words = self._create_kpi_card(kpi_frame, "Words Analyzed", "0", "#8b5cf6", 3)

        # Chart Display Card
        chart_card = tk.Frame(self.tab_analytics, bg=COLOR_CARD, bd=1, relief=tk.SOLID)
        chart_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Chart navigation toolbar
        chart_bar = tk.Frame(chart_card, bg="#f8fafc", height=38)
        chart_bar.pack(fill=tk.X, side=tk.TOP, padx=6, pady=6)

        self.chart_title_var = tk.StringVar(value=self.chart_files[self.current_chart_idx][0])
        chart_title_lbl = tk.Label(chart_bar, textvariable=self.chart_title_var,
                                   font=("Helvetica", 11, "bold"), fg=COLOR_TEXT, bg="#f8fafc")
        chart_title_lbl.pack(side=tk.LEFT, padx=10)

        prev_btn = tk.Button(chart_bar, text="◀ Previous Chart", bg="#e2e8f0", fg=COLOR_TEXT,
                             font=("Helvetica", 8, "bold"), relief=tk.FLAT, padx=8, pady=3,
                             command=self.prev_chart)
        prev_btn.pack(side=tk.RIGHT, padx=4)

        next_btn = tk.Button(chart_bar, text="Next Chart ▶", bg="#e2e8f0", fg=COLOR_TEXT,
                             font=("Helvetica", 8, "bold"), relief=tk.FLAT, padx=8, pady=3,
                             command=self.next_chart)
        next_btn.pack(side=tk.RIGHT, padx=4)

        regen_btn = tk.Button(chart_bar, text="⟳ Regenerate Plots", bg=COLOR_PRIMARY, fg="#ffffff",
                              font=("Helvetica", 8, "bold"), relief=tk.FLAT, padx=8, pady=3,
                              command=self.regenerate_charts)
        regen_btn.pack(side=tk.RIGHT, padx=6)

        # Image Canvas / Label for Pillow rendering
        self.chart_img_label = tk.Label(chart_card, bg=COLOR_CARD)
        self.chart_img_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

    def _create_kpi_card(self, parent, title, value, accent_color, col):
        card = tk.Frame(parent, bg=COLOR_CARD, bd=1, relief=tk.SOLID, padx=12, pady=8)
        card.grid(row=0, column=col, padx=6, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)

        t_lbl = tk.Label(card, text=title, font=("Helvetica", 9), fg=COLOR_MUTED, bg=COLOR_CARD)
        t_lbl.pack(anchor="w")

        v_lbl = tk.Label(card, text=value, font=("Helvetica", 18, "bold"), fg=accent_color, bg=COLOR_CARD)
        v_lbl.pack(anchor="w", pady=(2, 0))
        return v_lbl

    def _display_current_chart(self):
        title, path = self.chart_files[self.current_chart_idx]
        self.chart_title_var.set(f"Plot {self.current_chart_idx + 1}/4: {title}")
        if os.path.exists(path):
            try:
                # Open with Pillow, fit to frame nicely
                pil_img = Image.open(path)
                width, height = pil_img.size
                # Scale down proportionally to fit window
                target_w = 780
                scale = target_w / width
                target_h = int(height * scale)
                if target_h > 420:
                    scale = 420 / height
                    target_h = 420
                    target_w = int(width * scale)

                resized = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                self.chart_photo = ImageTk.PhotoImage(resized)
                self.chart_img_label.configure(image=self.chart_photo, text="")
            except Exception as e:
                self.chart_img_label.configure(image="", text=f"Error loading plot: {e}")
        else:
            self.chart_img_label.configure(image="", text="Chart not yet generated.")

    def next_chart(self):
        self.current_chart_idx = (self.current_chart_idx + 1) % len(self.chart_files)
        self._display_current_chart()

    def prev_chart(self):
        self.current_chart_idx = (self.current_chart_idx - 1) % len(self.chart_files)
        self._display_current_chart()

    def regenerate_charts(self):
        try:
            generate_all_charts()
            self._display_current_chart()
            self.refresh_all_data()
            messagebox.showinfo("Success", "Matplotlib & Seaborn charts regenerated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed generating charts: {e}")

    # --- Posts Tab ---
    def _setup_posts_tab(self):
        top_bar = tk.Frame(self.tab_posts, bg=COLOR_BG)
        top_bar.pack(fill=tk.X, pady=(6, 6))

        tk.Label(top_bar, text="Filter Category:", font=("Helvetica", 9, "bold"), bg=COLOR_BG).pack(side=tk.LEFT, padx=4)
        self.post_cat_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(top_bar, textvariable=self.post_cat_var,
                                 values=["All", "Food", "Books", "Music", "Travel", "Other"],
                                 state="readonly", width=12)
        cat_combo.pack(side=tk.LEFT, padx=6)
        cat_combo.bind("<<ComboboxSelected>>", lambda e: self.load_posts_table())

        del_btn = tk.Button(top_bar, text="Delete Post", bg="#ef4444", fg="#ffffff",
                            font=("Helvetica", 8, "bold"), relief=tk.FLAT, padx=10, pady=3,
                            command=self.delete_selected_post)
        del_btn.pack(side=tk.RIGHT, padx=4)

        view_btn = tk.Button(top_bar, text="View Post Details", bg=COLOR_PRIMARY, fg="#ffffff",
                             font=("Helvetica", 8, "bold"), relief=tk.FLAT, padx=10, pady=3,
                             command=self.view_selected_post)
        view_btn.pack(side=tk.RIGHT, padx=4)

        # Posts Treeview
        cols = ("id", "title", "category", "author", "words", "status", "date")
        self.posts_tree = ttk.Treeview(self.tab_posts, columns=cols, show="headings", selectmode="browse")
        self.posts_tree.heading("id", text="ID")
        self.posts_tree.heading("title", text="Title")
        self.posts_tree.heading("category", text="Category")
        self.posts_tree.heading("author", text="Author")
        self.posts_tree.heading("words", text="Words")
        self.posts_tree.heading("status", text="Status")
        self.posts_tree.heading("date", text="Date")

        self.posts_tree.column("id", width=60, anchor="center")
        self.posts_tree.column("title", width=260)
        self.posts_tree.column("category", width=90, anchor="center")
        self.posts_tree.column("author", width=120)
        self.posts_tree.column("words", width=70, anchor="center")
        self.posts_tree.column("status", width=90, anchor="center")
        self.posts_tree.column("date", width=150)

        posts_scroll = ttk.Scrollbar(self.tab_posts, orient=tk.VERTICAL, command=self.posts_tree.yview)
        self.posts_tree.configure(yscroll=posts_scroll.set)

        self.posts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        posts_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def load_posts_table(self):
        for item in self.posts_tree.get_children():
            self.posts_tree.delete(item)

        filter_cat = self.post_cat_var.get()
        posts = db.get_posts(category=None if filter_cat == "All" else filter_cat, only_published=False)
        for p in posts:
            words = len(p.get("body", "").split())
            self.posts_tree.insert("", tk.END, values=(
                p.get("id"),
                p.get("title"),
                p.get("category"),
                p.get("authorName"),
                words,
                p.get("status"),
                p.get("date", "")[:16]
            ))

    def delete_selected_post(self):
        sel = self.posts_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a post to delete.")
            return
        post_id = self.posts_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete post {post_id}?"):
            db.delete_post(str(post_id))
            generate_all_charts()
            self.refresh_all_data()

    def view_selected_post(self):
        sel = self.posts_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a post to inspect.")
            return
        post_id = str(self.posts_tree.item(sel[0])["values"][0])
        post = next((p for p in db.get_posts(only_published=False) if str(p.get("id")) == post_id), None)
        if not post:
            return

        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"Post Details – {post.get('title')}")
        detail_win.geometry("550x420")
        detail_win.configure(bg=COLOR_BG)

        tk.Label(detail_win, text=post.get("title"), font=("Georgia", 14, "bold"),
                 wraplength=500, justify="left", bg=COLOR_BG, fg=COLOR_PRIMARY).pack(anchor="w", padx=16, pady=(16, 4))
        meta_text = f"By {post.get('authorName')} ({post.get('authorEmail')}) · Category: {post.get('category')} · Status: {post.get('status')}"
        tk.Label(detail_win, text=meta_text, font=("Helvetica", 9), fg=COLOR_MUTED, bg=COLOR_BG).pack(anchor="w", padx=16, pady=(0, 10))

        body_box = tk.Text(detail_win, wrap=tk.WORD, font=("Helvetica", 10), padx=10, pady=10)
        body_box.insert("1.0", post.get("body", ""))
        body_box.configure(state="disabled")
        body_box.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

    # --- Users Tab ---
    def _setup_users_tab(self):
        top_bar = tk.Frame(self.tab_users, bg=COLOR_BG)
        top_bar.pack(fill=tk.X, pady=(6, 6))

        tk.Label(top_bar, text="Change Selected User's Plan to:", font=("Helvetica", 9, "bold"), bg=COLOR_BG).pack(side=tk.LEFT, padx=4)
        self.new_plan_var = tk.StringVar(value="Premium")
        plan_combo = ttk.Combobox(top_bar, textvariable=self.new_plan_var,
                                  values=["Free", "Standard", "Premium", "Student"],
                                  state="readonly", width=12)
        plan_combo.pack(side=tk.LEFT, padx=6)

        update_plan_btn = tk.Button(top_bar, text="Update Plan", bg=COLOR_PRIMARY, fg="#ffffff",
                                    font=("Helvetica", 8, "bold"), relief=tk.FLAT, padx=10, pady=3,
                                    command=self.update_user_plan)
        update_plan_btn.pack(side=tk.LEFT, padx=6)

        cols = ("id", "name", "email", "age", "gender", "plan", "date")
        self.users_tree = ttk.Treeview(self.tab_users, columns=cols, show="headings", selectmode="browse")
        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("name", text="Name")
        self.users_tree.heading("email", text="Email")
        self.users_tree.heading("age", text="Age")
        self.users_tree.heading("gender", text="Gender")
        self.users_tree.heading("plan", text="Plan")
        self.users_tree.heading("date", text="Joined")

        self.users_tree.column("id", width=60, anchor="center")
        self.users_tree.column("name", width=160)
        self.users_tree.column("email", width=200)
        self.users_tree.column("age", width=60, anchor="center")
        self.users_tree.column("gender", width=80, anchor="center")
        self.users_tree.column("plan", width=90, anchor="center")
        self.users_tree.column("date", width=140)

        users_scroll = ttk.Scrollbar(self.tab_users, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscroll=users_scroll.set)

        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        users_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def load_users_table(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for u in db.get_users():
            self.users_tree.insert("", tk.END, values=(
                u.get("id"),
                u.get("name"),
                u.get("email"),
                u.get("age"),
                u.get("gender"),
                u.get("plan", "Free"),
                u.get("date", "")[:16]
            ))

    def update_user_plan(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a user first.")
            return
        user_email = self.users_tree.item(sel[0])["values"][2]
        new_plan = self.new_plan_var.get()
        db.set_plan(user_email, new_plan)
        generate_all_charts()
        self.refresh_all_data()
        messagebox.showinfo("Success", f"User {user_email} plan updated to {new_plan}.")

    # --- Reviews Tab ---
    def _setup_reviews_tab(self):
        cols = ("id", "name", "rating", "subject", "message", "date")
        self.rev_tree = ttk.Treeview(self.tab_reviews, columns=cols, show="headings", selectmode="browse")
        self.rev_tree.heading("id", text="ID")
        self.rev_tree.heading("name", text="User")
        self.rev_tree.heading("rating", text="Rating")
        self.rev_tree.heading("subject", text="Subject")
        self.rev_tree.heading("message", text="Review Content")
        self.rev_tree.heading("date", text="Date")

        self.rev_tree.column("id", width=60, anchor="center")
        self.rev_tree.column("name", width=120)
        self.rev_tree.column("rating", width=90, anchor="center")
        self.rev_tree.column("subject", width=180)
        self.rev_tree.column("message", width=300)
        self.rev_tree.column("date", width=130)

        rev_scroll = ttk.Scrollbar(self.tab_reviews, orient=tk.VERTICAL, command=self.rev_tree.yview)
        self.rev_tree.configure(yscroll=rev_scroll.set)

        self.rev_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        rev_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def load_reviews_table(self):
        for item in self.rev_tree.get_children():
            self.rev_tree.delete(item)
        for r in db.get_reviews():
            stars = "★" * int(r.get("rating", 5)) + "☆" * (5 - int(r.get("rating", 5)))
            self.rev_tree.insert("", tk.END, values=(
                r.get("id"),
                r.get("name"),
                stars,
                r.get("subject"),
                r.get("msg"),
                r.get("date", "")[:16]
            ))

    # --- Contact Messages Tab ---
    def _setup_messages_tab(self):
        cols = ("id", "name", "phone", "email", "subject", "message", "date")
        self.msg_tree = ttk.Treeview(self.tab_messages, columns=cols, show="headings", selectmode="browse")
        self.msg_tree.heading("id", text="ID")
        self.msg_tree.heading("name", text="Sender")
        self.msg_tree.heading("phone", text="Phone")
        self.msg_tree.heading("email", text="Email")
        self.msg_tree.heading("subject", text="Subject")
        self.msg_tree.heading("message", text="Message")
        self.msg_tree.heading("date", text="Received")

        self.msg_tree.column("id", width=60, anchor="center")
        self.msg_tree.column("name", width=120)
        self.msg_tree.column("phone", width=110)
        self.msg_tree.column("email", width=160)
        self.msg_tree.column("subject", width=160)
        self.msg_tree.column("message", width=250)
        self.msg_tree.column("date", width=130)

        msg_scroll = ttk.Scrollbar(self.tab_messages, orient=tk.VERTICAL, command=self.msg_tree.yview)
        self.msg_tree.configure(yscroll=msg_scroll.set)

        self.msg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        msg_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def load_messages_table(self):
        for item in self.msg_tree.get_children():
            self.msg_tree.delete(item)
        for m in db.get_messages():
            self.msg_tree.insert("", tk.END, values=(
                m.get("id"),
                m.get("name"),
                m.get("phone"),
                m.get("email"),
                m.get("subject"),
                m.get("message"),
                m.get("date", "")[:16]
            ))

    def _build_statusbar(self):
        status_frame = tk.Frame(self.root, bg="#e2e8f0", height=26)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_var = tk.StringVar(value="Python Backend Database: Ready | NumPy, Pandas, Matplotlib, Seaborn Active")
        status_lbl = tk.Label(status_frame, textvariable=self.status_var, font=("Helvetica", 8),
                              bg="#e2e8f0", fg=COLOR_TEXT)
        status_lbl.pack(side=tk.LEFT, padx=12)

    def refresh_all_data(self):
        stats = compute_analytics()
        self.kpi_posts.config(text=str(stats["posts"]["total_posts"]))
        self.kpi_users.config(text=str(stats["users"]["total_users"]))
        self.kpi_rating.config(text=f"{stats['reviews']['avg_rating']}★")
        self.kpi_words.config(text=f"{stats['posts']['total_words_written']:,}")

        self._display_current_chart()
        self.load_posts_table()
        self.load_users_table()
        self.load_reviews_table()
        self.load_messages_table()

    def open_web_app(self):
        webbrowser.open("http://localhost:5000")

    def export_csv(self):
        try:
            folder = export_data_to_csv()
            messagebox.showinfo("Export Complete", f"Data exported to CSV files successfully in:\n{folder}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

def launch_admin_gui():
    root = tk.Tk()
    app = InkJamAdminApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_admin_gui()
