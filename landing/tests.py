from django.test import TestCase

from .models import LandingPage


# Create your tests here.
class LandingPageTests(TestCase):
    def setUp(self):
        landing_fields = {
            "artist_name": "------",
            "occupation": "------",
            "instagram": "------",
            "twitter": "------",
            "youtube": "------",
            "tiktok": "------",
            "slots": 0,
            "comms_status": False,
            "bio": "------"
        }
        self.landing_page = LandingPage.objects.create(**landing_fields)

    def test_status_closed_if_zero_slots_on_save(self):
        self.landing_page.slots = 0
        self.landing_page.comms_status = True
        self.landing_page.save()
        self.landing_page.refresh_from_db()
        self.assertEqual(False, self.landing_page.comms_status)

    def test_status_closed_if_decreased_to_zero(self):
        self.landing_page.slots = 1
        self.landing_page.comms_status = True
        self.landing_page.save()
        self.landing_page.refresh_from_db()
        self.assertEqual(True, self.landing_page.comms_status)

        self.landing_page.slots -= 1
        self.landing_page.save()
        self.landing_page.refresh_from_db()
        self.assertEqual(False, self.landing_page.comms_status)

    def test_zero_slots_if_status_closed(self):
        self.landing_page.slots = 1
        self.landing_page.comms_status = True
        self.landing_page.save()
        self.landing_page.refresh_from_db()
        self.assertEqual(True, self.landing_page.comms_status)

        self.landing_page.comms_status = False
        self.landing_page.save()
        self.landing_page.refresh_from_db()
        self.assertEqual(0, self.landing_page.slots)
