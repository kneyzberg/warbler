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
        message2 = Message(**TEST_GEN_MSG2)
        message1 = Message(**TEST_GEN_MSG)
        
        db.session.add(user1)
        db.session.add(user2)
        user1.messages.append(message1)
        user2.messages.append(message2)
        
        db.session.commit()
        self.client = app.test_client()

        self.user1 = User.query.filter_by(username=TEST_GEN_USER["username"]).first()
        self.user2 = User.query.filter_by(username=TEST_GEN_USER2["username"]).first()


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

    def test_users_follower_page(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            self.user1 = User.query.filter_by(username=self.user1.username).first()
            self.user1.followers.append(self.user2)
            db.session.commit()

            resp = c.get(f"/users/{self.user1.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.user1.followers), 1)
            self.assertIn(f"<p>@{self.user2.username}</p>", html)
    
    def test_follow_user(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.post(f"/users/follow/{self.user2.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.user1 = User.query.filter_by(username=self.user1.username).first()

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.user1.following), 1)
            self.assertIn(f"<p>@{self.user2.username}</p>", html)
    
    def test_stop_following(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            username = self.user2.username
            self.user1 = User.query.filter_by(username=self.user1.username).first()
            self.user2 = User.query.filter_by(username=self.user2.username).first()
            self.user1.following.append(self.user2)
            db.session.commit()
            
            resp = c.post(f"/users/stop-following/{self.user2.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(username, html)


    def test_show_liked_messages(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            self.user1 = User.query.filter_by(username=self.user1.username).first()
            new_msg = Message.query.filter_by(user_id=self.user2.id).first()
            
            self.user1.likes.append(new_msg)
            db.session.commit()

            self.user1 = User.query.filter_by(username=self.user1.username).first()
            msg = Message.query.filter_by(user_id=self.user2.id).first()

            resp = c.get(f"/users/{self.user1.id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"<p>{ msg.text }</p>", html)

    def test_edit_profile(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.get(f"/users/profile")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', html)

    def test_edit_profile_form(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.post("/users/profile", data={
                        "email": "avocado@gmail.com",
                        "username": "avocado_toasties",
                        "password": "password",
                        "image_url": "www.image.com"
                    }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("avocado_toasties", html)

    def test_edit_profile_form_fail(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.post("/users/profile", data={
                        "email": "avocado@gmail.com",
                        "username": "avocado_toasties",
                        "password": "passWORD",
                        "image_url": "www.image.com"
                    }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid password", html)
    
    def test_delete_user(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.post("/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
    

class GenUserFunctionLoggedOutTest(TestCase):

    def setUp(self):
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup(**TEST_GEN_USER)
        user2 = User.signup(**TEST_GEN_USER2)
        message2 = Message(**TEST_GEN_MSG2)
        message1 = Message(**TEST_GEN_MSG)
        
        db.session.add(user1)
        db.session.add(user2)
        user1.messages.append(message1)
        user2.messages.append(message2)
        
        db.session.commit()
        self.client = app.test_client()

        self.user1 = User.query.filter_by(username=TEST_GEN_USER["username"]).first()
        self.user2 = User.query.filter_by(username=TEST_GEN_USER2["username"]).first()

    def test_user_following_logged_out(self):
        with app.test_client() as c:
            resp = c.get(f"/users/{self.user1.id}/following", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn("<h1>What's Happening?</h1>", html)
    
    def test_user_follower_logged_out(self):
        with app.test_client() as c:
            resp = c.get(f"/users/{self.user1.id}/followers", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn("<h1>What's Happening?</h1>", html)

    
    def test_user_likes_logged_out(self):
        with app.test_client() as c:
            resp = c.get(f"/users/{self.user1.id}/likes", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn("<h1>What's Happening?</h1>", html)
    
    def test_user_profile_logged_out(self):
        with app.test_client() as c:
            resp = c.get("/users/profile", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn("<h1>What's Happening?</h1>", html)
    
    def test_user_delete_logged_out(self):
        with app.test_client() as c:
            resp = c.post("/users/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            self.assertIn("<h1>What's Happening?</h1>", html)
    
    











