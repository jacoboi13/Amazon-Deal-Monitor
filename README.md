# Amazon-Deal-Monitor

The Amazon Deal Monitor fetches deals from a third-party source and posts them to Discord webhooks based on configurable filters and categories. This tool is designed for modularity with JSON file-based webhook configurations and advanced deal filtering capabilities.
<br><br>
![88n131Jkrh](https://github.com/user-attachments/assets/8e554ee2-ec89-41d5-b5bc-4b3983bf9c31)
![olgGOAh553](https://github.com/user-attachments/assets/7667d984-5079-4c6a-9977-bc4c985e6be5)
![XaHOKnsOA1](https://github.com/user-attachments/assets/b3a400a1-33a6-4e47-a4de-b9b38e7acf4e)
<br>
## Features

- Fully asynchronous for efficient processing.
- Fetches deals from Amazon based on defined categories and price discounts.
- Posts deals to Discord webhooks with customizable embed data.
- Supports multiple proxy configurations for handling requests.
- Validates and loads filter and data configurations from JSON files.
- Provides scheduled tasks for regular and priority deal fetching.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/ArshansGithub/Amazon-Deal-Monitor.git
    cd Amazon-Deal-Monitor
    ```

2. **Install dependencies:**

    ```bash
    pip install httpx aiofiles
    ```

3. **Create configuration files:**

    - `config.json`: Configure filters, webhook details, and embed data.
    - `data.json`: *DO NOT MODIFY!* -> Keeps track of already seen deals to prevent duplicate postings.

    *Placeholders for `config.json` and `data.json` are provided below.*

## Configuration

### `config.json`

```json
{
    "priority_category": ["Electronics"],
    "regular_category": [
        "Arts Crafts and Sewing",
        "Baby Products",
        "Beauty",
        "Collectibles and Fine Art",
        "Furniture",
        "Grocery and Gourmet Food",
        "Health and Personal Care",
        "Home and Kitchen",
        "Jewelry",
        "Kindle Store",
        "Luggage",
        "Movies and TV",
        "Music",
        "Musical Instruments",
        "Office Products",
        "Other",
        "Patio Lawn and Garden",
        "Pet Supplies",
        "Sports and Outdoors",
        "Toys and Games",
        "Video Games",
        "Automotive",
        "Cell Phones and Accessories",
        "Industrial and Scientific",
        "Tools and Home Improvement",
        "Appliances"
    ],
    "price_off": [10, 20, 30],
    "other_webhook": "https://discord.com/api/webhooks/your-webhook-url",
    "filters": [
        {
            "criteria": {
                "average_price_min": 10,
                "average_price_max": 100,
                "percent_off_min": 10,
                "percent_off_max": 50,
                "categories": ["category1", "all"]
            },
            "webhooks": [
                {
                    "webhook": ["https://discord.com/api/webhooks/your-webhook-url"],
                    "role": "your-role-id"
                }
            ],
            "isolated": true
        }
    ],
    "embed_data": {
        "username": "Amazon Deals Bot",
        "avatar_url": "https://example.com/avatar.png",
        "author_name": "Amazon Deals",
        "author_icon_url": "https://example.com/author-icon.png",
        "footer": "Happy Shopping!",
        "footer_icon": "https://example.com/footer-icon.png",
        "color": 16711680
    }
}
```

### `data.json`

```json
[]
```

## Usage

### Running the Scraper

To start the scraper, use the following command:

```bash
python3 main.py
```

### Customizing Filters and Webhooks

You can adjust filter criteria and webhook configurations in the `config.json` file. Ensure that your JSON structure is valid and includes all required fields.

- The `isolated` flag on each filter places priority on that filter, meaning it will be returned exclusively if matched. Place filters in the desired order to control the result output. For instance, if two filters with the `isolated` flag are next to each other, only the first matching filter will be returned. To prioritize a different filter, position it above the one you wish to override.

- Filters referencing 'average price' pertain to the product's price before any discounts are applied.

## Testing

The Amazon Deal Monitor includes unit tests to ensure the proper functionality of its components, particularly the `AmazonScraper` class and its filtering logic.

### Test Script

The provided test script uses Python's `unittest` framework to test various scenarios of the `AmazonScraper` class. Below is an explanation of how to use and understand the test script.

#### Test Script Overview

- **File Location**: `tests/test_scraper.py` (adjust based on actual location)
- **Test Class**: `TestAmazonScraper`
- **Test Framework**: `unittest` with `IsolatedAsyncioTestCase` for asynchronous testing

#### Test Script Code

```python
import unittest
from main import AmazonScraper
from unittest import IsolatedAsyncioTestCase

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
        self.scraper = AmazonScraper(self.config, self.data_file, [])
        self.scraper.filter_config = self.mock_filter_config

    async def test_match_filter_with_priority(self):
        data = {
            "offerPrice": 114.04,
            "average": 1186.76,
            "categories": "Electronics",
        }

        expected_webhooks = [
            "Some webhook"
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
            "Some webhook"
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
```

#### How to Run the Tests

1. **Navigate to the Test Directory:**

   Change to the directory where your test script is located.

   ```bash
   cd tests
   ```

2. **Execute the Tests:**

   Run the test script using Python:

   ```bash
   python3 -m unittest test_scraper.py
   ```

   This will run all test cases defined in the `TestAmazonScraper` class.

### Understanding the Tests

- **`setUp` Method**: Initializes the `AmazonScraper` instance with mock configurations for tests.
- **`test_match_filter_with_priority`**: Tests if the scraper correctly matches filters with priority.
- **`test_match_filter_without_priority`**: Tests if the scraper correctly matches filters when priority is disabled.
- **`test_match_filter_no_matching_webhooks`**: Tests if the scraper returns the fallback webhook when no filters match.

## Contributing

Contributions are welcome! To contribute to the project, please fork the repository and use feature branches. Submit pull requests for review and inclusion.

## License

This project is licensed under the GNU General Public License.

## Contact

For inquiries or support, please open a ticket on the [GitHub issues page](https://github.com/ArshansGithub/Amazon-Deal-Monitor/issues).

