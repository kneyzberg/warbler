"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import IntegrityError

from models import db, User, Message, Follows, LikedMessage

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config["TESTING"] = True

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


class UserModelTestCase(TestCase):
    """Test model instances."""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup(**USER_DATA)
        user2 = User.signup(**USER_DATA2)
        db.session.add(user1)
        db.session.add(user2)

        message = Message(**MESSAGE)

        user1.messages.append(message)

        db.session.commit()    

        self.client = app.test_client()
        self.user1 = user1
        self.user2 = user2
        self.message = message


    def test_add_new_message(self):
        """ Test post new message """
        new_msg = Message(text="HELLO", timestamp=None,user_id=self.user2.id)

        db.session.add(new_msg)
        db.session.commit()
        # user2 should have 1 message and message should have 0 likes
        self.assertEqual(len(self.user2.messages), 1)
        self.assertEqual(len(new_msg.users_liked), 0)

    def test_repr(self):
        """ Test repr returns correct string """

        repr_string = repr(Message(user_id=self.message.user_id,
                                timestamp=self.message.timestamp))
        self.assertIn(f"{self.message.timestamp}, {self.message.user_id}", repr_string)

    def test_does_not_like_messsage(self):
        """ Test that user2 does not like user1's message """

        self.assertNotIn(self.user2, self.message.users_liked)
        self.assertEqual(len(self.message.users_liked), 0)

    def test_liked_message(self):
        """ Test that user2 does like user1's message """

        self.message.users_liked.append(self.user2)
        db.session.commit()

        self.assertIn(self.user2, self.message.users_liked)
        self.assertEqual(len(self.message.users_liked), 1)
    
    def test_cannot_like_own_message(self):
        """ Test that user cannot like own message """

        user1_msg = self.message.check_valid_like(self.user1)

        self.assertFalse(user1_msg)
