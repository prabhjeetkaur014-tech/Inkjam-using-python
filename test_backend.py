"""
Automated Backend Verification Test Suite for inkJam.
Tests Database, Analytics (NumPy, Pandas, Matplotlib, Seaborn),
and Flask API Endpoints.
"""
import unittest
import json
import os
import numpy as np
import pandas as pd

from database import db
from analytics import compute_analytics, generate_all_charts, export_data_to_csv
from app import app

class TestInkJamBackend(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_database_initialization(self):
        posts = db.get_posts()
        self.assertGreaterEqual(len(posts), 5)
        users = db.get_users()
        self.assertGreaterEqual(len(users), 1)
        reviews = db.get_reviews()
        self.assertGreaterEqual(len(reviews), 3)

    def test_analytics_computation(self):
        summary = compute_analytics()
        self.assertIn("posts", summary)
        self.assertIn("users", summary)
        self.assertIn("reviews", summary)
        self.assertGreater(summary["posts"]["total_words_written"], 50)
        self.assertGreaterEqual(summary["reviews"]["avg_rating"], 1.0)

    def test_chart_generation(self):
        charts = generate_all_charts()
        self.assertEqual(len(charts), 4)
        for c in charts:
            self.assertTrue(os.path.exists(c), f"Chart missing: {c}")

    def test_export_data(self):
        export_dir = export_data_to_csv()
        self.assertTrue(os.path.exists(os.path.join(export_dir, "posts_export.csv")))
        self.assertTrue(os.path.exists(os.path.join(export_dir, "users_export.csv")))

    def test_api_sync(self):
        resp = self.client.get("/api/sync")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["posts"], list)

    def test_api_posts_filter(self):
        resp = self.client.get("/api/posts?category=Food")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        for p in data["posts"]:
            self.assertEqual(p["category"], "Food")

    def test_api_signup_and_login(self):
        # Signup
        email = "testwriter@example.com"
        resp = self.client.post("/api/signup", json={
            "name": "Test Writer",
            "age": 22,
            "gender": "Female",
            "email": email,
            "password": "password123"
        })
        self.assertIn(resp.status_code, [200, 400]) # 400 if already exists

        # Login
        resp_login = self.client.post("/api/login", json={
            "email": email,
            "password": "password123"
        })
        self.assertEqual(resp_login.status_code, 200)
        self.assertEqual(resp_login.get_json()["status"], "success")

    def test_api_create_post(self):
        resp = self.client.post("/api/posts", json={
            "title": "Automated Test Story",
            "category": "Travel",
            "body": "Exploring the serene beauty of the mountain tops in early spring morning.",
            "authorName": "Test Writer",
            "authorEmail": "testwriter@example.com"
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")

    def test_profanity_filter(self):
        resp = self.client.post("/api/posts", json={
            "title": "Bad word idiot",
            "category": "Travel",
            "body": "Clean body",
            "authorName": "Test",
            "authorEmail": "test@test.com"
        })
        self.assertEqual(resp.status_code, 400)

    def test_api_analytics(self):
        resp = self.client.get("/api/analytics")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("analytics", data)

if __name__ == "__main__":
    unittest.main()
