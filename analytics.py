"""
inkJam Analytics & Data Science Engine.
Powered by NumPy, Pandas, Matplotlib, and Seaborn.
Provides summary metrics, distribution calculations, and
publication-quality visualizations.
"""
import os
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Headless backend for web server and background generation
import matplotlib.pyplot as plt
import seaborn as sns

from database import db

# inkJam Brand Color Palette
BRAND_PRIMARY = "#3858e9"
BRAND_SECONDARY = "#2a45c4"
BRAND_ACCENTS = ["#3858e9", "#e0245e", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4"]
BG_LIGHT = "#f8f9fa"
TEXT_COLOR = "#161a2e"

CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "charts")

def ensure_charts_dir():
    os.makedirs(CHARTS_DIR, exist_ok=True)
    alt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inkJam", "img", "charts")
    os.makedirs(alt_dir, exist_ok=True)

def compute_analytics():
    """
    Computes comprehensive analytics using NumPy and Pandas DataFrames.
    Returns a rich metrics dictionary.
    """
    state = db.get_full_state()
    posts = state.get("posts", [])
    users = state.get("users", [])
    reviews = state.get("reviews", [])
    messages = state.get("messages", [])

    # Default empty structures
    posts_df = pd.DataFrame(posts)
    users_df = pd.DataFrame(users)
    reviews_df = pd.DataFrame(reviews)

    # 1. Post Analytics with NumPy & Pandas
    if not posts_df.empty:
        # Calculate word counts for each post
        posts_df["word_count"] = posts_df["body"].apply(lambda b: len(str(b).split()))
        # Estimated reading time in minutes (200 words per minute rule, min 1)
        posts_df["read_time"] = np.maximum(1, np.round(posts_df["word_count"] / 200).astype(int))

        word_counts = posts_df["word_count"].to_numpy()
        read_times = posts_df["read_time"].to_numpy()

        post_stats = {
            "total_posts": int(len(posts_df)),
            "published_posts": int((posts_df["status"] == "published").sum()),
            "scheduled_posts": int((posts_df["status"] == "scheduled").sum()),
            "category_counts": posts_df["category"].value_counts().to_dict(),
            "avg_word_count": float(np.mean(word_counts)) if len(word_counts) > 0 else 0.0,
            "median_word_count": float(np.median(word_counts)) if len(word_counts) > 0 else 0.0,
            "max_word_count": int(np.max(word_counts)) if len(word_counts) > 0 else 0,
            "min_word_count": int(np.min(word_counts)) if len(word_counts) > 0 else 0,
            "std_word_count": float(np.std(word_counts)) if len(word_counts) > 0 else 0.0,
            "avg_read_time": float(np.mean(read_times)) if len(read_times) > 0 else 1.0,
            "total_words_written": int(np.sum(word_counts)) if len(word_counts) > 0 else 0
        }
    else:
        post_stats = {
            "total_posts": 0, "published_posts": 0, "scheduled_posts": 0,
            "category_counts": {}, "avg_word_count": 0.0, "median_word_count": 0.0,
            "max_word_count": 0, "min_word_count": 0, "std_word_count": 0.0,
            "avg_read_time": 0.0, "total_words_written": 0
        }

    # 2. User Analytics with Pandas & NumPy
    if not users_df.empty:
        plan_counts = users_df["plan"].value_counts().to_dict()
        gender_counts = users_df["gender"].value_counts().to_dict() if "gender" in users_df.columns else {}
        ages = users_df["age"].dropna().to_numpy() if "age" in users_df.columns else np.array([])

        user_stats = {
            "total_users": int(len(users_df)),
            "plan_counts": plan_counts,
            "gender_counts": gender_counts,
            "avg_age": float(np.mean(ages)) if len(ages) > 0 else 0.0,
            "median_age": float(np.median(ages)) if len(ages) > 0 else 0.0,
            "min_age": int(np.min(ages)) if len(ages) > 0 else 0,
            "max_age": int(np.max(ages)) if len(ages) > 0 else 0
        }
    else:
        user_stats = {
            "total_users": 0, "plan_counts": {}, "gender_counts": {},
            "avg_age": 0.0, "median_age": 0.0, "min_age": 0, "max_age": 0
        }

    # 3. Reviews Analytics with Pandas & NumPy
    if not reviews_df.empty and "rating" in reviews_df.columns:
        ratings = reviews_df["rating"].to_numpy()
        rating_counts = reviews_df["rating"].value_counts().to_dict()
        # Ensure all 1-5 stars are represented
        for r in range(1, 6):
            if r not in rating_counts:
                rating_counts[r] = 0

        review_stats = {
            "total_reviews": int(len(reviews_df)),
            "avg_rating": round(float(np.mean(ratings)), 2),
            "median_rating": float(np.median(ratings)),
            "std_rating": round(float(np.std(ratings)), 2),
            "rating_counts": rating_counts
        }
    else:
        review_stats = {
            "total_reviews": 0, "avg_rating": 0.0, "median_rating": 0.0,
            "std_rating": 0.0, "rating_counts": {r: 0 for r in range(1, 6)}
        }

    return {
        "posts": post_stats,
        "users": user_stats,
        "reviews": review_stats,
        "messages_count": len(messages)
    }

def generate_all_charts():
    """
    Renders high quality Seaborn & Matplotlib data visualizations
    and saves them to the charts folder for web & desktop display.
    """
    ensure_charts_dir()
    state = db.get_full_state()
    posts = state.get("posts", [])
    users = state.get("users", [])
    reviews = state.get("reviews", [])

    posts_df = pd.DataFrame(posts) if posts else pd.DataFrame(columns=["category", "body", "status"])
    users_df = pd.DataFrame(users) if users else pd.DataFrame(columns=["plan", "gender", "age"])
    reviews_df = pd.DataFrame(reviews) if reviews else pd.DataFrame(columns=["rating", "name"])

    # Setup theme
    sns.set_theme(style="whitegrid")
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

    generated_files = []

    # --- Chart 1: Category Distribution (Seaborn Countplot) ---
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    if not posts_df.empty and "category" in posts_df.columns:
        order = ["Food", "Books", "Music", "Travel", "Other"]
        cat_counts = posts_df["category"].value_counts().reindex(order).fillna(0)
        sns.barplot(x=cat_counts.index, y=cat_counts.values, palette="Blues_r", ax=ax, hue=cat_counts.index, legend=False)
        ax.set_title("Stories by Category", fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=12)
        ax.set_xlabel("Category", fontsize=11, fontweight="600")
        ax.set_ylabel("Number of Posts", fontsize=11, fontweight="600")
        for p in ax.patches:
            height = p.get_height()
            if height > 0:
                ax.annotate(f"{int(height)}", (p.get_x() + p.get_width() / 2., height),
                            ha="center", va="bottom", fontsize=10, fontweight="bold", xytext=(0, 2),
                            textcoords="offset points")
    else:
        ax.text(0.5, 0.5, "No post data available", ha="center", va="center")
    
    plt.tight_layout()
    cat_path = os.path.join(CHARTS_DIR, "category_distribution.png")
    fig.savefig(cat_path, bbox_inches="tight")
    # Also copy to inkJam subdir if present
    alt_cat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inkJam", "img", "charts", "category_distribution.png")
    fig.savefig(alt_cat_path, bbox_inches="tight")
    plt.close(fig)
    generated_files.append(cat_path)

    # --- Chart 2: Ratings Breakdown (Seaborn / Matplotlib Bar & Donut) ---
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    if not reviews_df.empty and "rating" in reviews_df.columns:
        ratings_series = reviews_df["rating"].value_counts().reindex([5, 4, 3, 2, 1]).fillna(0)
        colors = ["#10b981", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"]
        bars = ax.barh([f"{r} Stars" for r in ratings_series.index], ratings_series.values, color=colors, height=0.6)
        ax.set_title("User Ratings & Feedback Breakdown", fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=12)
        ax.set_xlabel("Review Count", fontsize=11, fontweight="600")
        for bar in bars:
            width = bar.get_width()
            if width > 0:
                ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2, f"{int(width)}",
                        va="center", ha="left", fontsize=10, fontweight="bold")
    else:
        ax.text(0.5, 0.5, "No review ratings yet", ha="center", va="center")
    plt.tight_layout()
    rat_path = os.path.join(CHARTS_DIR, "ratings_breakdown.png")
    fig.savefig(rat_path, bbox_inches="tight")
    alt_rat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inkJam", "img", "charts", "ratings_breakdown.png")
    fig.savefig(alt_rat_path, bbox_inches="tight")
    plt.close(fig)
    generated_files.append(rat_path)

    # --- Chart 3: Read Time & Word Length Analysis (Seaborn Histplot) ---
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    if not posts_df.empty and "body" in posts_df.columns:
        words = posts_df["body"].apply(lambda b: len(str(b).split())).to_numpy()
        sns.histplot(words, kde=True, color=BRAND_PRIMARY, ax=ax, bins=min(10, max(3, len(words))))
        mean_words = np.mean(words)
        ax.axvline(mean_words, color="#e0245e", linestyle="--", linewidth=2, label=f"Mean: {mean_words:.1f} words")
        ax.set_title("Post Word Count Distribution", fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=12)
        ax.set_xlabel("Words per Post", fontsize=11, fontweight="600")
        ax.set_ylabel("Count", fontsize=11, fontweight="600")
        ax.legend(frameon=True)
    else:
        ax.text(0.5, 0.5, "No story text to analyze", ha="center", va="center")
    plt.tight_layout()
    word_path = os.path.join(CHARTS_DIR, "reading_time_dist.png")
    fig.savefig(word_path, bbox_inches="tight")
    alt_word_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inkJam", "img", "charts", "reading_time_dist.png")
    fig.savefig(alt_word_path, bbox_inches="tight")
    plt.close(fig)
    generated_files.append(word_path)

    # --- Chart 4: Multi-Panel Executive Analytics Dashboard ---
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 7), dpi=140)
    fig.suptitle("inkJam Platform Analytics Overview", fontsize=16, fontweight="bold", color=BRAND_PRIMARY)

    # Panel 1: Categories
    if not posts_df.empty:
        cat_counts = posts_df["category"].value_counts()
        ax1.pie(cat_counts.values, labels=cat_counts.index, autopct='%1.0f%%',
                colors=sns.color_palette("tab10", len(cat_counts)), startangle=140)
        ax1.set_title("Category Share", fontsize=12, fontweight="bold")
    else:
        ax1.text(0.5, 0.5, "No posts", ha="center")

    # Panel 2: Subscription Plans
    if not users_df.empty and "plan" in users_df.columns:
        plan_counts = users_df["plan"].value_counts()
        ax2.bar(plan_counts.index, plan_counts.values, color=BRAND_PRIMARY, width=0.5)
        ax2.set_title("Subscribed Plans", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Users")
    else:
        ax2.text(0.5, 0.5, "No user plans", ha="center")

    # Panel 3: Ratings
    if not reviews_df.empty and "rating" in reviews_df.columns:
        rat_counts = reviews_df["rating"].value_counts().sort_index(ascending=False)
        ax3.bar([f"{r}★" for r in rat_counts.index], rat_counts.values, color="#f59e0b", width=0.5)
        ax3.set_title("Review Ratings", fontsize=12, fontweight="bold")
        ax3.set_ylabel("Reviews")
    else:
        ax3.text(0.5, 0.5, "No reviews", ha="center")

    # Panel 4: Reading Times vs Word Count
    if not posts_df.empty:
        words = posts_df["body"].apply(lambda b: len(str(b).split())).to_numpy()
        ax4.boxplot(words, orientation='horizontal', patch_artist=True,
                    boxprops=dict(facecolor="#dbeafe", color=BRAND_PRIMARY),
                    medianprops=dict(color="#e0245e", linewidth=2))
        ax4.set_title("Word Count Dispersion", fontsize=12, fontweight="bold")
        ax4.set_xlabel("Words")
    else:
        ax4.text(0.5, 0.5, "No story data", ha="center")

    plt.tight_layout()
    dash_path = os.path.join(CHARTS_DIR, "overview_dashboard.png")
    fig.savefig(dash_path, bbox_inches="tight")
    alt_dash_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inkJam", "img", "charts", "overview_dashboard.png")
    fig.savefig(alt_dash_path, bbox_inches="tight")
    plt.close(fig)
    generated_files.append(dash_path)

    return generated_files

def export_data_to_csv():
    """
    Exports posts, users, and reviews to CSV files using Pandas.
    """
    state = db.get_full_state()
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exports")
    os.makedirs(export_dir, exist_ok=True)

    posts_df = pd.DataFrame(state.get("posts", []))
    users_df = pd.DataFrame(state.get("users", []))
    reviews_df = pd.DataFrame(state.get("reviews", []))
    messages_df = pd.DataFrame(state.get("messages", []))

    posts_df.to_csv(os.path.join(export_dir, "posts_export.csv"), index=False)
    users_df.to_csv(os.path.join(export_dir, "users_export.csv"), index=False)
    reviews_df.to_csv(os.path.join(export_dir, "reviews_export.csv"), index=False)
    messages_df.to_csv(os.path.join(export_dir, "messages_export.csv"), index=False)

    return export_dir

if __name__ == "__main__":
    print("Computing inkJam analytics...")
    summary = compute_analytics()
    print("Analytics summary:", summary)
    print("Generating Matplotlib and Seaborn charts...")
    charts = generate_all_charts()
    print("Generated charts:", charts)
