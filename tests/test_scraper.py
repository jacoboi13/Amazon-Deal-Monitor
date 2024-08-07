import unittest
from unittest import IsolatedAsyncioTestCase
import sys
import os

# Add the parent directory (your_project) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main

class TestAmazonScraper(IsolatedAsyncioTestCase):
    
    def setUp(self):
        # Mock initialization
        self.maxDiff = None
        self.config = "config.json"
        self.data_file = "data.json"
        self.mock_filter_config = {
            "filters": [
                # Define your mock filter configurations here
            ],
            "other_webhook": "other_webhook",
        }
        self.scraper = main.AmazonScraper(self.config, self.data_file, [])
        self.scraper.filter_config = self.mock_filter_config

    async def test_match_filter_with_priority(self):
        data = {
            "offerPrice": 114.04,
            "average": 1186.76,
            "categories": "Electronics",
        }

        expected_webhooks = [
            "somewebhook"
        ]
        
        matching_webhooks = await self.scraper.match_filter(data)
        self.assertEqual(matching_webhooks, expected_webhooks)

    async def test_match_filter_without_priority(self):
        data = {
            "offerPrice": 50.0,
            "average": 100.0,
            "categories": "Electronics",
        }

        expected_webhooks = [
            "somewebhook"
        ]
        
        # Disable the 'isolated' flag for this test
        self.scraper.filter_config['filters'][1]['isolated'] = False
        self.scraper.filter_config['filters'][2]['isolated'] = False

        matching_webhooks = await self.scraper.match_filter(data)
        self.assertCountEqual(matching_webhooks, expected_webhooks)

    async def test_match_filter_no_matching_webhooks(self):
        data = {
            "offerPrice": 50.0,
            "average": 100.0,
            "categories": "Electronics",
        }

        expected_webhooks = [{"webhook": "other_webhook", "role": ""}]
        
        self.scraper.filter_config = {
            "filters": [
                {
                    "criteria": {
                        "average_price_min": 200,
                        "average_price_max": 300,
                        "categories": ["Books"],
                        "priority": True,
                    },
                    "webhooks": ["webhook1", "webhook2"],
                }
            ],
            "other_webhook": "other_webhook",
        }

        matching_webhooks = await self.scraper.match_filter(data)
        self.assertEqual(matching_webhooks, expected_webhooks)

if __name__ == "__main__":
    unittest.main()
