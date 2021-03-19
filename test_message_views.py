"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, LikedMessage
from test_seed import TEST_GEN_USER

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
app.config["TESTING"] = True


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser2 = User.signup(**TEST_GEN_USER)
        self.msg2 = Message(text="this is message for user2")
        self.msg = Message(text="testing the msg")
        self.testuser.messages.append(self.msg)
        self.testuser2.messages.append(self.msg2)

        db.session.commit()
        self.testuser = User.query.filter_by(username="testuser").first()
        self.testuser2 = User.query.filter_by(username=TEST_GEN_USER["username"]).first()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            Message.query.delete()
            db.session.commit()

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
           
            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    
    def test_delete_message(self):
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            self.testuser = User.query.filter_by(username="testuser").first()
            msg = self.testuser.messages[0]

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.testuser = User.query.filter_by(username="testuser").first()

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.testuser.messages), 0)
            self.assertNotIn(msg.text, html)

    def test_like_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            self.testuser2 = User.query.filter_by(username=self.testuser2.username).first()
            msg = self.testuser2.messages[0]

            resp = c.post(f"/messages/{msg.id}/like")

            self.testuser = User.query.filter_by(username=self.testuser.username).first()
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(self.testuser.likes), 1)

    def test_invalid_like_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        self.testuser = User.query.filter_by(username=self.testuser.username).first()
        msg = self.testuser.messages[0]
        resp = c.post(f"/messages/{msg.id}/like")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 302)
        # self.assertIn("You can't like your own messages!", html)






