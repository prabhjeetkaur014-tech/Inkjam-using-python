"""
inkJam Python Web Backend.
Flask server providing static asset serving and RESTful API endpoints.
Powered by Python, Database layer, and Data Analytics engine.
"""
import os
import secrets
from flask import Flask, request, jsonify, send_from_directory, session, redirect

from database import db
from analytics import compute_analytics, generate_all_charts, export_data_to_csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
app.secret_key = secrets.token_hex(32)

# --- Static File Routes ---

@app.route("/")
def index_route():
    # If user is in session, redirect to home.html, otherwise index.html
    if "user_email" in session:
        return redirect("/home.html")
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    # Check root workspace first
    if os.path.exists(os.path.join(BASE_DIR, filename)):
        return send_from_directory(BASE_DIR, filename)
    # Check inkJam subdirectory fallback
    inkjam_sub = os.path.join(BASE_DIR, "inkJam", filename)
    if os.path.exists(inkjam_sub):
        return send_from_directory(os.path.join(BASE_DIR, "inkJam"), filename)
    return "File not found", 404

# --- API Endpoints ---

@app.route("/api/sync", methods=["GET"])
def api_sync():
    """
    Synchronizes initial state between Python backend and client.
    Returns posts, reviews, and current session user details.
    """
    db.publish_due()
    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    cur_user = db.get_user_by_email(user_email) if user_email else None

    # Sanitized user (no password)
    safe_user = None
    if cur_user:
        safe_user = {k: v for k, v in cur_user.items() if k != "password"}

    favs = db.get_favourites(user_email) if user_email else []
    mine_posts = db.get_user_posts(user_email) if user_email else []
    feed_posts = db.get_posts(only_published=True)
    reviews_list = db.get_reviews()

    return jsonify({
        "status": "success",
        "user": safe_user,
        "posts": feed_posts,
        "mine": mine_posts,
        "favourites": favs,
        "reviews": reviews_list
    })

# --- Authentication ---

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(force=True, silent=True) or request.form
    name = data.get("name", "").strip()
    try:
        age = int(data.get("age", 0))
    except (ValueError, TypeError):
        age = 0
    gender = data.get("gender", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    success, result = db.signup(name, age, gender, email, password)
    if not success:
        return jsonify({"status": "error", "message": result}), 400

    session["user_email"] = email
    safe_user = {k: v for k, v in result.items() if k != "password"}
    return jsonify({"status": "success", "user": safe_user})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True, silent=True) or request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    success, user = db.login(email, password)
    if not success:
        return jsonify({"status": "error", "message": "Invalid email or password."}), 401

    session["user_email"] = email
    safe_user = {k: v for k, v in user.items() if k != "password"}
    return jsonify({"status": "success", "user": safe_user})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user_email", None)
    return jsonify({"status": "success", "message": "Logged out successfully."})

@app.route("/api/user", methods=["GET"])
def api_get_user():
    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    user = db.get_user_by_email(user_email)
    if not user:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    safe_user = {k: v for k, v in user.items() if k != "password"}
    return jsonify({"status": "success", "user": safe_user})

@app.route("/api/plan", methods=["POST"])
def api_set_plan():
    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    if not user_email:
        return jsonify({"status": "error", "message": "Authentication required."}), 401

    data = request.get_json(force=True, silent=True) or request.form
    plan = data.get("plan", "Free")
    updated = db.set_plan(user_email, plan)
    if updated:
        return jsonify({"status": "success", "plan": plan})
    return jsonify({"status": "error", "message": "User not found"}), 404

# --- Posts ---

@app.route("/api/posts", methods=["GET"])
def api_get_posts():
    category = request.args.get("category")
    query = request.args.get("q")
    posts = db.get_posts(category=category, query=query, only_published=True)
    return jsonify({"status": "success", "posts": posts})

@app.route("/api/posts", methods=["POST"])
def api_create_post():
    data = request.get_json(force=True, silent=True) or request.form
    title = data.get("title", "").strip()
    category = data.get("category", "Other")
    body = data.get("body", "").strip()
    status = data.get("status", "published")
    publish_at = data.get("publishAt")

    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    user = db.get_user_by_email(user_email)
    author_name = user["name"] if user else data.get("authorName", "Writer")
    author_email = user["email"] if user else (user_email or "guest@inkjam.com")

    success, result = db.add_post(
        title=title,
        category=category,
        body=body,
        author_name=author_name,
        author_email=author_email,
        status=status,
        publish_at=publish_at
    )
    if not success:
        return jsonify({"status": "error", "message": result}), 400

    # Trigger async or instant chart update
    try:
        generate_all_charts()
    except Exception:
        pass

    return jsonify({"status": "success", "post": result}), 201

@app.route("/api/posts/<post_id>", methods=["PUT", "PATCH"])
def api_update_post(post_id):
    patch = request.get_json(force=True, silent=True) or request.form
    success, result = db.update_post(post_id, patch)
    if not success:
        return jsonify({"status": "error", "message": result}), 400
    return jsonify({"status": "success", "message": result})

@app.route("/api/posts/<post_id>", methods=["DELETE"])
def api_delete_post(post_id):
    db.delete_post(post_id)
    try:
        generate_all_charts()
    except Exception:
        pass
    return jsonify({"status": "success", "message": "Post deleted."})

@app.route("/api/posts/mine", methods=["GET"])
def api_get_my_posts():
    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    if not user_email:
        return jsonify({"status": "error", "message": "Authentication required."}), 401
    posts = db.get_user_posts(user_email)
    return jsonify({"status": "success", "posts": posts})

# --- Favourites ---

@app.route("/api/favourites", methods=["GET"])
def api_get_favourites():
    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    if not user_email:
        return jsonify({"status": "error", "message": "Authentication required."}), 401
    fav_ids = db.get_favourites(user_email)
    all_posts = {p["id"]: p for p in db.get_posts(only_published=True)}
    fav_posts = [all_posts[pid] for pid in fav_ids if pid in all_posts]
    return jsonify({"status": "success", "favIds": fav_ids, "posts": fav_posts})

@app.route("/api/favourites/toggle", methods=["POST"])
def api_toggle_favourite():
    user_email = session.get("user_email") or request.headers.get("X-User-Email")
    if not user_email:
        return jsonify({"status": "error", "message": "Authentication required."}), 401

    data = request.get_json(force=True, silent=True) or request.form
    post_id = data.get("id")
    if not post_id:
        return jsonify({"status": "error", "message": "Post ID required."}), 400

    is_fav, fav_list = db.toggle_favourite(user_email, post_id)
    return jsonify({"status": "success", "isFav": is_fav, "favIds": fav_list})

# --- Reviews ---

@app.route("/api/reviews", methods=["GET"])
def api_get_reviews():
    reviews = db.get_reviews()
    avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else 0.0
    return jsonify({"status": "success", "reviews": reviews, "avgRating": avg_rating})

@app.route("/api/reviews", methods=["POST"])
def api_add_review():
    data = request.get_json(force=True, silent=True) or request.form
    name = data.get("name", "").strip()
    rating = data.get("rating", 5)
    subject = data.get("subject", "").strip()
    msg = data.get("msg", "").strip()

    success, result = db.add_review(name, rating, subject, msg)
    if not success:
        return jsonify({"status": "error", "message": result}), 400

    try:
        generate_all_charts()
    except Exception:
        pass

    return jsonify({"status": "success", "review": result}), 201

# --- Contact Messages ---

@app.route("/api/contact", methods=["POST"])
def api_add_contact():
    data = request.get_json(force=True, silent=True) or request.form
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip().lower()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()

    success, result = db.add_message(name, phone, email, subject, message)
    if not success:
        return jsonify({"status": "error", "message": result}), 400
    return jsonify({"status": "success", "message": "Message sent successfully."}), 201

# --- Data Science & Analytics Endpoints ---

@app.route("/api/analytics", methods=["GET"])
def api_get_analytics():
    """Returns analytics computed using NumPy and Pandas."""
    summary = compute_analytics()
    return jsonify({"status": "success", "analytics": summary})

@app.route("/api/analytics/regenerate", methods=["POST"])
def api_regenerate_charts():
    """Regenerates all Seaborn and Matplotlib visualization figures."""
    charts = generate_all_charts()
    return jsonify({"status": "success", "charts": [os.path.basename(c) for c in charts]})

@app.route("/api/analytics/export", methods=["GET"])
def api_export_csv():
    """Exports data into CSV files using Pandas."""
    export_dir = export_data_to_csv()
    return jsonify({
        "status": "success",
        "exportDirectory": export_dir,
        "files": ["posts_export.csv", "users_export.csv", "reviews_export.csv", "messages_export.csv"]
    })

if __name__ == "__main__":
    generate_all_charts()
    port = int(os.environ.get("PORT", 5000))
    print(f" inkJam Python Backend running at: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
