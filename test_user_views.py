"""View Function tests for User Routes."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import IntegrityError, DataError, request

from models import db, User, Message, Follows, LikedMessage

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False

USER_DATA = {
    "email": "minestrone@gmail.com",
    "username": "minestrone",
    "password": "password",
    "image_url": None,
}

USER_DATA2 = {
    "email": "bisque@gmail.com",
    "username": "bouillabaisse",
    "password": "password",
    "image_url": "www.image.com"

}

MESSAGE = {
    "text": "Have a SOUPER day",
    "timestamp":  None
}


class TestUserViewFunctions(TestCase):

    def setUp(self):
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup(**USER_DATA)
        db.session.add(user1)
        db.session.commit()
        self.client = app.test_client()
        self.user1 = user1

    def test_signup(self):
        with app.test_client() as client:
            resp = client.get("/signup")

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<button class="btn btn-primary btn-lg btn-block">Sign me up!</button>', html)
    
    def test_signup_form_submit(self):
        with app.test_client() as client:
            resp = client.post("/signup", data=USER_DATA2, follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('id="home-aside"', html)

    def test_invalid_signup_form_submit(self):
        with app.test_client() as client:
            resp = client.post("/signup", data=USER_DATA, follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", html)


    def test_login_page(self):
         with app.test_client() as client:
            resp = client.get("/login")

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
    
    
    def test_successful_login(self):
        with app.test_client() as client:
            resp = client.post("/login", data={"username": self.user1.username,
                                               "password": USER_DATA["password"]
                                                }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"Hello, {self.user1.username}!", html)


