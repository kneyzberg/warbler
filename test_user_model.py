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
        db.session.commit()    

        self.client = app.test_client()
        self.user1 = user1
        self.user2 = user2

    # def tearDown(self):
    #     db.session.rollback()


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
    
    def test_repr(self):
        """Test Repr returns correct username and email """
        repr_string = repr(User(email=self.user1.email,
                                username=self.user1.username))
        self.assertIn(f"{self.user1.username}, {self.user1.email}", repr_string)

    def test_user_following(self):
        """ Test that user following inlcludes user2 """
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertIn(self.user2, self.user1.following)
    
    def test_user_not_following(self):
        """Test that user1 is not folllowing user2"""
        self.assertNotIn(self.user2, self.user1.following)
    
    def test_user_followers(self):
        """Test user being followed by user2"""
        self.user1.followers.append(self.user2)
        db.session.commit()
        self.assertIn(self.user2, self.user1.followers)

    def test_user_not_follower(self):
        """Test that user2 is not following user1"""
        self.assertNotIn(self.user2, self.user1.followers)
    
    def test_successful_user_signup(self):
        """Test user signup with valid credentials"""

        new_user = User.signup(username="testname", 
                               email="testing@gmail.com", 
                               password="HASHED PASSWORD",
                               image_url=None)
        db.session.add(new_user)
        db.session.commit()

        user_query = User.query.filter_by(username="testname").first()
        self.assertEqual(new_user.username, user_query.username)
        self.assertEqual(new_user.email, user_query.email)
        self.assertEqual(new_user.password, user_query.password)

    def test_invalid_user_signup(self):
        """Test User signup method fails with invalid credentials"""
        try:
            bad_user = User.signup(username="badtest", password="HASHED PASSWORD")
        except TypeError:
            signupError = "failure to assign user"
    
        self.assertEqual(signupError, "failure to assign user")
    
    def test_not_unique_user_signup(self):
        """Test User signup method fails with invalid credentials"""
        with self.assertRaises(IntegrityError):
            duplicate_user = User.signup(username="minestrone",
                                         email="minestrone@gmail.com",
                                         password="HASHED PASSWORD",
                                         image_url=None)
            db.session.commit()
    
    def test_authenticate_valid(self):
        """Test for valid authentication """

        valid_user = User.authenticate(self.user1.username, USER_DATA["password"])

        self.assertEqual(self.user1, valid_user)

    def test_authenticate_invalid_password(self):
        """Test for invalid password authentication """

        invalid_user = User.authenticate(self.user1.username, "badpassword")

        self.assertFalse(invalid_user)

    def test_authenticate_invalid_password(self):
        """Test for invalid password authentication """

        invalid_user = User.authenticate("pasta e fagioli", USER_DATA["password"])

        self.assertFalse(invalid_user)