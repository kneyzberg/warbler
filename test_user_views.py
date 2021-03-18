"""View Function tests for User Routes."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import IntegrityError, DataError, request

from models import db, User, Message, Follows, LikedMessage
from test_seed import USER_DATA, USER_DATA2, MESSAGE, TEST_GEN_USER, TEST_GEN_USER2, TEST_GEN_MSG, TEST_GEN_MSG2

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False



class SignupLoginLogoutViewFunctions(TestCase):

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

    def test_user_logout(self):
        with app.test_client() as client:
            client.post("/login", data={"username": self.user1.username,
                                               "password": USER_DATA["password"]
                                                }, follow_redirects=True)

            resp = client.get("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)
    
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You have successfully logged out!", html)


class GeneralUserRouteViewFunctions(TestCase):

    def setUp(self):
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup(**TEST_GEN_USER)
        user2 = User.signup(**TEST_GEN_USER2)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        self.client = app.test_client()

        self.user1 = User.query.filter_by(username=user1.username).first()
        self.user2 = User.query.filter_by(username=user2.username).first()


    def test_users_page(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"<p>@{self.user2.username}</p>", html)
    
    def test_users_profile(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            resp = c.get(f"/users/{self.user2.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'alt="Image for {self.user2.username}"', html)

    def test_users_following_page(self):

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            self.user1 = User.query.filter_by(username=self.user1.username).first()
            self.user1.following.append(self.user2)
            db.session.commit()

            resp = c.get(f"/users/{self.user1.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.user1.following), 1)
            self.assertIn(f"<p>@{self.user2.username}</p>", html)
            

                        
