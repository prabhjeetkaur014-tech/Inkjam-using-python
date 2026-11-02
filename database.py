"""
Database layer for inkJam.
Handles data persistence in JSON, seed data initialization,
filtering, and content moderation.
"""
import os
import json
import re
from datetime import datetime, timezone, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "inkjam_db.json")

# Blocked profanity list matching frontend
BLOCKED_WORDS = ['fuck', 'shit', 'bitch', 'asshole', 'stupid', 'idiot']

def is_clean(text: str) -> bool:
    """Checks if text contains any blocked words."""
    if not text:
        return True
    for word in BLOCKED_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True

def get_iso_now():
    return datetime.now(timezone.utc).isoformat()

def get_iso_day(offset_days: int):
    dt = datetime.now(timezone.utc) - timedelta(days=offset_days)
    return dt.isoformat()

# Default seed posts
SEED_POSTS = [
    {
        "id": "s1",
        "title": "Campus life, one chai at a time",
        "category": "Food",
        "body": "A walk through the canteen spots every first-year should know.",
        "authorName": "Harleen",
        "authorEmail": "harleen@example.com",
        "date": get_iso_day(1),
        "status": "published"
    },
    {
        "id": "s2",
        "title": "SQL joins, explained with samosas",
        "category": "Other",
        "body": "INNER, LEFT and RIGHT joins, but make it a snack platter. Once you visualize tables like snack stalls at the food street, queries start clicking instantly.",
        "authorName": "Aman",
        "authorEmail": "aman@example.com",
        "date": get_iso_day(2),
        "status": "published"
    },
    {
        "id": "s3",
        "title": "Three books for a long train ride",
        "category": "Books",
        "body": "Light, gripping and easy to read when the window seat is taken. Keep a paperback ready so you don't drain your battery before the journey ends.",
        "authorName": "Simran",
        "authorEmail": "simran@example.com",
        "date": get_iso_day(3),
        "status": "published"
    },
    {
        "id": "s4",
        "title": "A very ambitious weekend in Kasol",
        "category": "Travel",
        "body": "What to pack, what to skip and where the best maggi is. Trekking through the pines in Himachal is all about packing light and keeping your layers handy.",
        "authorName": "Rohan",
        "authorEmail": "rohan@example.com",
        "date": get_iso_day(4),
        "status": "published"
    },
    {
        "id": "s5",
        "title": "Playlist for debugging at 2 a.m.",
        "category": "Music",
        "body": "Lo-fi, a little indie and one song you will pretend you do not know. Perfect ambient background beats to keep your focus locked in when solving nasty edge cases.",
        "authorName": "Meher",
        "authorEmail": "meher@example.com",
        "date": get_iso_day(5),
        "status": "published"
    }
]

# Default seed reviews
SEED_REVIEWS = [
    {
        "id": "r1",
        "name": "Harleen",
        "rating": 5,
        "subject": "Lovely and simple",
        "msg": "Finally a blogging site that does not get in the way of writing.",
        "date": get_iso_day(3)
    },
    {
        "id": "r2",
        "name": "Aman",
        "rating": 4,
        "subject": "Great for students",
        "msg": "The student plan is a nice touch. Would love dark mode.",
        "date": get_iso_day(5)
    },
    {
        "id": "r3",
        "name": "Simran",
        "rating": 3,
        "subject": "Needs more themes",
        "msg": "Works well, but I would like more ways to style my posts.",
        "date": get_iso_day(7)
    }
]

# Default sample users
SEED_USERS = [
    {
        "id": "u1",
        "name": "Harleen Kaur",
        "age": 21,
        "gender": "Female",
        "email": "harleen@example.com",
        "password": "password123",
        "plan": "Standard",
        "date": get_iso_day(10)
    },
    {
        "id": "u2",
        "name": "Aman Sharma",
        "age": 22,
        "gender": "Male",
        "email": "aman@example.com",
        "password": "password123",
        "plan": "Student",
        "date": get_iso_day(9)
    },
    {
        "id": "u3",
        "name": "Simran Sandhu",
        "age": 20,
        "gender": "Female",
        "email": "simran@example.com",
        "password": "password123",
        "plan": "Free",
        "date": get_iso_day(8)
    }
]

class Database:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            initial_data = {
                "users": SEED_USERS,
                "posts": SEED_POSTS,
                "favourites": {
                    "harleen@example.com": ["s2", "s3"],
                    "aman@example.com": ["s1"]
                },
                "reviews": SEED_REVIEWS,
                "messages": [
                    {
                        "id": "m1",
                        "name": "Rohan Gupta",
                        "phone": "9876543210",
                        "email": "rohan@example.com",
                        "subject": "Collaboration query",
                        "message": "Hi, I love the platform. How can college writers submit feature requests?",
                        "date": get_iso_day(2)
                    }
                ]
            }
            self._save(initial_data)

    def _load(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self._ensure_storage()
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _save(self, data):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def publish_due(self):
        """Auto-publish scheduled posts whose publishAt time has arrived."""
        data = self._load()
        now = datetime.now(timezone.utc)
        changed = False
        for post in data.get("posts", []):
            if post.get("status") == "scheduled" and post.get("publishAt"):
                try:
                    pub_dt = datetime.fromisoformat(post["publishAt"].replace("Z", "+00:00"))
                    if pub_dt <= now:
                        post["status"] = "published"
                        post["date"] = post["publishAt"]
                        post.pop("publishAt", None)
                        changed = True
                except Exception:
                    pass
        if changed:
            self._save(data)

    # --- Users & Auth ---
    def get_users(self):
        return self._load().get("users", [])

    def get_user_by_email(self, email):
        if not email:
            return None
        email_clean = email.strip().lower()
        for u in self.get_users():
            if u.get("email", "").strip().lower() == email_clean:
                return u
        return None

    def signup(self, name, age, gender, email, password):
        email_clean = email.strip().lower()
        if not is_clean(name):
            return False, "Name contains unacceptable words."
        if len(name.strip()) < 2:
            return False, "Name is too short."
        if not (5 <= age <= 120):
            return False, "Age must be between 5 and 120."
        if not gender:
            return False, "Please select a gender."
        if not re.match(r'^\S+@\S+\.\S+$', email_clean):
            return False, "Invalid email address format."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."

        data = self._load()
        if any(u.get("email", "").strip().lower() == email_clean for u in data["users"]):
            return False, "An account with this email already exists. Please log in."

        new_user = {
            "id": f"u{int(datetime.now().timestamp() * 1000)}",
            "name": name.strip(),
            "age": age,
            "gender": gender,
            "email": email_clean,
            "password": password,
            "plan": "Free",
            "date": get_iso_now()
        }
        data["users"].append(new_user)
        self._save(data)
        return True, new_user

    def login(self, email, password):
        email_clean = email.strip().lower()
        user = self.get_user_by_email(email_clean)
        if user and user.get("password") == password:
            return True, user
        return False, None

    def set_plan(self, email, plan):
        data = self._load()
        email_clean = email.strip().lower()
        updated = False
        for u in data.get("users", []):
            if u.get("email", "").strip().lower() == email_clean:
                u["plan"] = plan
                updated = True
                break
        if updated:
            self._save(data)
        return updated

    # --- Posts ---
    def get_posts(self, category=None, query=None, only_published=True):
        self.publish_due()
        data = self._load()
        posts = data.get("posts", [])
        if only_published:
            posts = [p for p in posts if p.get("status") == "published"]

        if category and category != "Default":
            posts = [p for p in posts if p.get("category") == category]

        if query:
            q = query.strip().lower()
            posts = [
                p for p in posts
                if q in p.get("title", "").lower()
                or q in p.get("body", "").lower()
                or q in p.get("category", "").lower()
                or q in p.get("authorName", "").lower()
            ]

        # Sort newest first
        posts.sort(key=lambda x: x.get("date", ""), reverse=True)
        return posts

    def get_user_posts(self, email):
        self.publish_due()
        data = self._load()
        email_clean = email.strip().lower()
        posts = [p for p in data.get("posts", []) if p.get("authorEmail", "").strip().lower() == email_clean]
        posts.sort(key=lambda x: x.get("date", ""), reverse=True)
        return posts

    def add_post(self, title, category, body, author_name, author_email, status="published", publish_at=None):
        if not is_clean(title) or not is_clean(body):
            return False, "Title or story content contains unacceptable language."
        if not title.strip() or not body.strip():
            return False, "Title and content cannot be empty."

        data = self._load()
        post_id = f"p{int(datetime.now().timestamp() * 1000)}"
        new_post = {
            "id": post_id,
            "title": title.strip(),
            "category": category,
            "body": body.strip(),
            "authorName": author_name,
            "authorEmail": author_email.strip().lower(),
            "date": get_iso_now(),
            "status": status
        }
        if status == "scheduled" and publish_at:
            new_post["publishAt"] = publish_at

        data["posts"].append(new_post)
        self._save(data)
        return True, new_post

    def update_post(self, post_id, patch):
        data = self._load()
        found = False
        for p in data.get("posts", []):
            if p.get("id") == post_id:
                if "title" in patch and not is_clean(patch["title"]):
                    return False, "Title contains unacceptable words."
                if "body" in patch and not is_clean(patch["body"]):
                    return False, "Body contains unacceptable words."
                
                for k, v in patch.items():
                    if v is None and k in p:
                        del p[k]
                    elif v is not None:
                        p[k] = v
                found = True
                break
        if found:
            self._save(data)
            return True, "Post updated successfully."
        return False, "Post not found."

    def delete_post(self, post_id):
        data = self._load()
        data["posts"] = [p for p in data.get("posts", []) if p.get("id") != post_id]
        
        # Remove from favourites
        favs = data.get("favourites", {})
        for u_email in favs:
            favs[u_email] = [pid for pid in favs[u_email] if pid != post_id]
        data["favourites"] = favs

        self._save(data)
        return True

    # --- Favourites ---
    def get_favourites(self, email):
        data = self._load()
        return data.get("favourites", {}).get(email.strip().lower(), [])

    def toggle_favourite(self, email, post_id):
        data = self._load()
        favs = data.setdefault("favourites", {})
        u_favs = favs.setdefault(email.strip().lower(), [])
        if post_id in u_favs:
            u_favs.remove(post_id)
            is_fav = False
        else:
            u_favs.append(post_id)
            is_fav = True
        self._save(data)
        return is_fav, u_favs

    # --- Reviews ---
    def get_reviews(self):
        data = self._load()
        return data.get("reviews", [])

    def add_review(self, name, rating, subject, msg):
        if not is_clean(subject) or not is_clean(msg) or not is_clean(name):
            return False, "Review contains unacceptable language."
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                return False, "Rating must be between 1 and 5."
        except ValueError:
            return False, "Invalid rating."

        data = self._load()
        rev_id = f"r{int(datetime.now().timestamp() * 1000)}"
        new_rev = {
            "id": rev_id,
            "name": name.strip(),
            "rating": rating,
            "subject": subject.strip(),
            "msg": msg.strip(),
            "date": get_iso_now()
        }
        data["reviews"].append(new_rev)
        self._save(data)
        return True, new_rev

    # --- Messages (Contact) ---
    def get_messages(self):
        data = self._load()
        return data.get("messages", [])

    def add_message(self, name, phone, email, subject, message):
        if not is_clean(name) or not is_clean(subject) or not is_clean(message):
            return False, "Message contains unacceptable words."
        data = self._load()
        msg_id = f"m{int(datetime.now().timestamp() * 1000)}"
        new_msg = {
            "id": msg_id,
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip().lower(),
            "subject": subject.strip(),
            "message": message.strip(),
            "date": get_iso_now()
        }
        data["messages"].append(new_msg)
        self._save(data)
        return True, new_msg

    def get_full_state(self):
        self.publish_due()
        return self._load()

db = Database()
