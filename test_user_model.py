"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

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
    "bio": "I love is soup",
    "location": "BAYYY AREAAAA"
    "password": "password"
}

USER_DATA2 = {
    "email": "bisque@gmail.com",
    "username": "bouillabaisse",
    "bio": "soup or bust",
    "location": "Soup Cove"
    "password": "password"
}


class UserModelTestCase(TestCase):
    """Test model instances."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup(**USER_DATA)
        user2 = User.signup(**USER_DATA2)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
