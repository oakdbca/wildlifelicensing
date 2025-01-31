import datetime
import os

from django.test import TestCase
from django.urls import reverse

from wildlifelicensing.apps.main.models import Profile
from wildlifelicensing.apps.main.tests.helpers import (
    BasePermissionViewTestCase,
    SocialClient,
    TestData,
    add_to_group,
    get_or_create_default_customer,
    get_or_create_default_officer,
    get_or_create_user,
    upload_id,
)

TEST_ID_PATH = TestData.TEST_ID_PATH


class AccountsTestCase(TestCase):
    def setUp(self):
        self.customer = get_or_create_default_customer()

        self.officer = get_or_create_default_officer()

        self.client = SocialClient()

    def tearDown(self):
        self.client.logout()
        # clean id file
        if self.customer.identification2:
            os.remove(self.customer.identification2.upload.path)

    def test_profile_list(self):
        """Testing that a user can display the profile list if they are a customer"""
        self.client.login(self.customer.email)

        # check that client can access the profile list
        response = self.client.get(reverse("wl_main:list_profiles"))
        self.assertEqual(200, response.status_code)

    def test_profile_list_non_customer(self):
        """Testing that a user cannot display the profile list if they are not a customer"""
        self.client.login(self.officer.email)

        # check that client gets redirected if they try to access the profile list
        response = self.client.get(reverse("wl_main:list_profiles"))
        self.assertEqual(403, response.status_code)

    def test_create_profile(self):
        """Testing that a user can create a profile"""
        self.client.login(self.customer.email)

        original_profile_count = Profile.objects.filter(user=self.customer).count()

        # check that client can access the create profile page
        response = self.client.get(reverse("wl_main:create_profile"))
        self.assertEqual(200, response.status_code)

        post_params = {
            "user": self.customer.pk,
            "name": "Test Profile",
            "email": "test@testplace.net.au",
            "institution": "Test Institution",
            "line1": "1 Test Street",
            "locality": "Test Suburb",
            "state": "WA",
            "country": "AU",
            "postcode": "0001",
        }

        response = self.client.post(reverse("wl_main:create_profile"), post_params)
        self.assertEqual(302, response.status_code)

        # check that a new profile has been created
        self.assertEqual(
            Profile.objects.filter(user=self.customer).count(),
            original_profile_count + 1,
        )

    def test_edit_profile(self):
        """Testing that a user can edit an existing profile"""
        self.client.login(self.customer.email)

        # check no profile
        self.assertEqual(0, Profile.objects.filter(user=self.customer).count())

        post_params = {
            "user": self.customer.pk,
            "name": "Test Profile",
            "email": "test@testplace.net.au",
            "institution": "Test Institution",
            "line1": "1 Test Street",
            "locality": "Test Suburb",
            "state": "WA",
            "country": "AU",
            "postcode": "0001",
        }
        response = self.client.post(reverse("wl_main:create_profile"), post_params)
        self.assertEqual(302, response.status_code)

        # check that one profile has been created
        self.assertEqual(1, Profile.objects.filter(user=self.customer).count())

        profile = Profile.objects.filter(user=self.customer).first()
        # check that client can access the edit profile page
        response = self.client.get(reverse("wl_main:edit_profile", args=(profile.pk,)))
        self.assertEqual(200, response.status_code)

        # updated profile
        post_params["name"] = "Updated Profile"
        post_params["line1"] = "New Line 1"
        response = self.client.post(
            reverse("wl_main:edit_profile", args=(profile.pk,)), post_params
        )
        self.assertEqual(302, response.status_code)

        # get updated profile
        self.assertEqual(1, Profile.objects.filter(user=self.customer).count())

        profile = Profile.objects.filter(user=self.customer).first()

        # check that the profile has been edited
        self.assertEqual(profile.name, "Updated Profile")
        self.assertEqual(profile.postal_address.line1, "New Line 1")

    def test_manage_id(self):
        """Testing that a user can access the manage identification page"""
        self.client.login(self.customer.email)

        # check that client can access the manage identification page
        response = self.client.get(reverse("wl_main:identification"))
        self.assertEqual(200, response.status_code)

    def test_upload_id(self):
        """Testing that a user can upload an ID image"""
        self.client.login(self.customer.email)
        self.assertIsNone(self.customer.identification2)
        response = self.client.get(reverse("wl_main:identification"))
        self.assertEqual(200, response.status_code)
        response = upload_id(self.customer)
        self.assertEqual(200, response.status_code)

        # update customer
        self.customer.refresh_from_db()

        self.assertIsNotNone(self.customer.identification2)


class SearchCustomerTestCase(BasePermissionViewTestCase):
    view_url = reverse("wl_main:search_customers")

    @property
    def permissions(self):
        return {
            "get": {
                "allowed": [self.officer],
                "forbidden": [self.customer, self.assessor],
            },
        }

    def test_search_customers(self):
        """Testing that searching customers will return the right customer(s) and only customers"""
        self.client.login(self.officer.email)

        user_1, _ = get_or_create_user(
            {
                "first_name": "Some",
                "last_name": "Guy",
                "email": "some_email@test.net",
                "dob": datetime.date(1989, 8, 12),
            }
        )

        user_2, _ = get_or_create_user(
            {
                "first_name": "Some Other",
                "last_name": "Guy",
                "email": "some_other_email@test.net",
                "dob": datetime.date(1998, 8, 12),
            }
        )

        # search for users by common part of first name - both users should be found
        response = self.client.get("{}?q={}".format(self.view_url, "some"))
        self.assertEqual(200, response.status_code)

        json_response = response.json()

        self.assertEqual(len(json_response), 2)

        # make user_2 an officer and check that only user_1 is found by search for common part of first name
        add_to_group(user_2, "officers")

        response = self.client.get("{}?q={}".format(self.view_url, "some"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response["content-type"], "application/json")

        json_response = response.json()

        self.assertEqual(len(json_response), 1)

        self.assertEqual(json_response[0]["id"], user_1.id)
        self.assertEqual(json_response[0]["text"], user_1.get_full_name_dob())
