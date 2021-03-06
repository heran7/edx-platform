"""
Tests for StaticContentServer
"""
import copy
import logging
from uuid import uuid4
from path import path
from pymongo import MongoClient

from django.contrib.auth.models import User
from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings

from student.models import CourseEnrollment

from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (studio_store_config,
    ModuleStoreTestCase)
from xmodule.modulestore.xml_importer import import_from_xml

log = logging.getLogger(__name__)

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['OPTIONS']['db'] = 'test_xcontent_%s' % uuid4().hex

TEST_MODULESTORE = studio_store_config(settings.TEST_ROOT / "data")


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class ContentStoreToyCourseTest(ModuleStoreTestCase):
    """
    Tests that use the toy course.
    """

    def setUp(self):
        """
        Create user and login.
        """

        settings.MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')
        settings.MODULESTORE['direct']['OPTIONS']['fs_root'] = path('common/test/data')

        self.client = Client()
        self.contentstore = contentstore()

        # A locked asset
        self.loc_locked = Location('c4x', 'edX', 'toy', 'asset', 'sample_static.txt')
        self.url_locked = StaticContent.get_url_path_from_location(self.loc_locked)

        # An unlocked asset
        self.loc_unlocked = Location('c4x', 'edX', 'toy', 'asset', 'another_static.txt')
        self.url_unlocked = StaticContent.get_url_path_from_location(self.loc_unlocked)

        import_from_xml(modulestore('direct'), 'common/test/data/', ['toy'],
                static_content_store=self.contentstore, verbose=True)

        self.contentstore.set_attr(self.loc_locked, 'locked', True)

        # Create user
        self.usr = 'testuser'
        self.pwd = 'foo'
        email = 'test+courses@edx.org'
        self.user = User.objects.create_user(self.usr, email, self.pwd)
        self.user.is_active = True
        self.user.save()

        # Create staff user
        self.staff_usr = 'stafftestuser'
        self.staff_pwd = 'foo'
        staff_email = 'stafftest+courses@edx.org'
        self.staff_user = User.objects.create_user(self.staff_usr, staff_email,
                self.staff_pwd)
        self.staff_user.is_active = True
        self.staff_user.is_staff = True
        self.staff_user.save()

    def tearDown(self):

        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['OPTIONS']['db'])
        _CONTENTSTORE.clear()

    def test_unlocked_asset(self):
        """
        Test that unlocked assets are being served.
        """
        self.client.logout()
        resp = self.client.get(self.url_unlocked)
        self.assertEqual(resp.status_code, 200) #pylint: disable=E1103

    def test_locked_asset_not_logged_in(self):
        """
        Test that locked assets behave appropriately in case the user is not
        logged in.
        """
        self.client.logout()
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 403) #pylint: disable=E1103

    def test_locked_asset_not_registered(self):
        """
        Test that locked assets behave appropriately in case user is logged in
        in but not registered for the course.
        """
        self.client.login(username=self.usr, password=self.pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 403) #pylint: disable=E1103

    def test_locked_asset_registered(self):
        """
        Test that locked assets behave appropriately in case user is logged in
        and registered for the course.
        """
        #pylint: disable=E1101
        course_id = "/".join([self.loc_locked.org, self.loc_locked.course, '2012_Fall'])
        CourseEnrollment.enroll(self.user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))

        self.client.login(username=self.usr, password=self.pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 200) #pylint: disable=E1103

    def test_locked_asset_staff(self):
        """
        Test that locked assets behave appropriately in case user is staff.
        """
        #pylint: disable=E1101
        course_id = "/".join([self.loc_locked.org, self.loc_locked.course, '2012_Fall'])

        self.client.login(username=self.staff_usr, password=self.staff_pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 200) #pylint: disable=E1103

