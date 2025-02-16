import ssl
import httpcore
import httpx
import json
import aiofiles
import asyncio
from typing import Any, Dict, List, Optional
import random
import traceback
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonScraper:
    def __init__(self, filter_config_path: str, data_config_path: str, proxies: List[str] = None):
        self.load_configurations(filter_config_path, data_config_path)
        self.setup_clients(proxies)
        self.age = "false"  # "true" for old, "false" for new
        self.setup_mappings_and_headers()
        self.setup_validation()

    def load_configurations(self, filter_config_path: str, data_config_path: str):
        if not filter_config_path or not data_config_path:
            raise ValueError("Config files not found")
        
        if not filter_config_path.endswith(".json") or not data_config_path.endswith(".json"):
            raise ValueError("Config files must have a .json extension")
   
        try:
            with open(filter_config_path, 'r') as file:
                self.filter_config = json.load(file)
                
            with open(data_config_path, "r") as file:
                self.already_seen = json.load(file)
        except json.JSONDecodeError:
            raise ValueError("Failed to load config files. Make sure they contain valid JSON data.")

    def setup_clients(self, proxies: List[str]):
        pool_limits = httpx.Limits(max_connections=500)
        timeout = httpx.Timeout(10.0, connect=5.0)
        self.clients = [httpx.AsyncClient(proxies=proxy, limits=pool_limits, timeout=timeout) for proxy in proxies]

    def setup_mappings_and_headers(self):
        self.mappings = {
            "Contains All Details": "flex flex-row gap-[12px] flex-wrap justify-center items-center",
            "Price": "h-[28px] absolute top-[5px] left-[10px] w-[76px] px-4 text-white text-base flex flex-row items-center justify-center bg-black rounded-full",
            "Title": "text-black text-base text-center overflow-hidden h-[48px] whitespace-normal break-words",
            "Average Price": "flex border border-black/10 bg-white px-3 py-1 rounded-[6px] flex-row items-center gap-x-3",
            "Amazon Link": "bg-gradient-to-b from-[#EFDC9E] to-[#E5C762] font-semibold border border-black/30 text-[12px] w-[231px] h-[31px] rounded-[6px] flex flex-col items-center justify-center text-black mt-[14px] mb-[8px]",
        }

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "RSC": "1",
            "Next-Url": "/top",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Referer": "https://saving.deals/top",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    def setup_validation(self):
        self.validate_keys = {
            list: ["other_webhook", "price_off", "priority_category", "regular_category", "categories", "webhook", "filters", "webhooks"],
            int: ["average_price_min", "average_price_max", "percent_off_min", "percent_off_max", "color"],
            bool: ["priority", "isolated"],
            str: ["name", "role", "username", "avatar_url", "author_name", "author_icon_url", "footer", "footer_icon", "other_webhook"],
            dict: ["criteria", "embed_data"],
        }
        
        self.required_keys = ["other_webhook", "price_off", "priority_category", "regular_category", "filters"]
        self.found_keys = {key: False for value in self.validate_keys.values() for key in value}
        
        try:
            self.validate_config()
        except Exception as e:
            raise ValueError(f"You have a corrupt configuration: {e}")
        
        for key, value in self.found_keys.items():
            if not value and key in self.required_keys:
                raise ValueError(f"Required key '{key}' not found in config")
        
        logging.info("Config validated!")

    def validate_config(self) -> None:
        for key, value in self.filter_config.items():
            self.validate(key, value)
    
    def validate(self, key, value):
        if type(value) not in self.validate_keys:
            raise ValueError(f"Invalid key: {key} with value: {value}")
        
        if isinstance(value, dict):
            for k, v in value.items():
                self.validate(k, v)
                
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        self.validate(k, v)
            
        if key not in self.validate_keys[type(value)]:
            raise ValueError(f"Key '{key}' not found in {self.validate_keys[type(value)]}")
        
        if isinstance(value, dict) and "webhook" in value:
            if not value["webhook"].startswith("https://discord.com/api/webhooks/"):
                raise ValueError(f"Invalid webhook: {value['webhook']}")
            
            if "role" not in value:
                raise ValueError(f"Role not found in {value}")
        
        self.found_keys[key] = True

    async def make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        retries: int = 5,
    ) -> httpx.Response:
        try:
            someClient = random.choice(self.clients)
            response = await someClient.request(
                method=method, url=url, headers=headers, cookies=cookies, json=json_data
            )
            
            if response is None:
                return await self.make_request(
                    method, url, headers, json_data, cookies, retries - 1
                )
            
            return response
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpcore.ConnectError, httpx.ConnectError, httpx.RemoteProtocolError, httpx.ProxyError, ssl.SSLError, httpx.PoolTimeout) as e:
            if retries > 0:
                logging.warning(f"Retrying: {url} ({retries} attempts left)")
                return await self.make_request(
                    method, url, headers, json_data, cookies, retries - 1
                )
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
                
    async def match_filter(self, data: Dict[str, Any]) -> List[str]:
        matching_webhooks = []
        
        current_price = data["offerPrice"]
        avg_price = data["average"]
        percent_off = (avg_price - current_price) / avg_price * 100
        
        hasBeenIsolated = False
        isolated_webhooks = []
        
        for filter in self.filter_config["filters"]:
            criteria = filter["criteria"]
            match = True
            
            if hasBeenIsolated:
                match = False
            
            if "average_price_min" in criteria and avg_price < criteria["average_price_min"]:
                match = False
            if "average_price_max" in criteria and avg_price > criteria["average_price_max"]:
                match = False
            if "percent_off_min" in criteria and percent_off < criteria["percent_off_min"]:
                match = False
            if "percent_off_max" in criteria and percent_off > criteria["percent_off_max"]:
                match = False
                
            if "categories" in criteria and data["categories"] not in criteria["categories"]:
                if "all" not in criteria["categories"]:
                    match = False
                
            if "isolated" in filter and filter["isolated"]:
                if hasBeenIsolated:
                    match = False
                else:
                    hasBeenIsolated = True
            
            if match:
                if "isolated" in filter and filter["isolated"]:
                    isolated_webhooks.extend(filter["webhooks"])
                else:
                    matching_webhooks.extend(filter["webhooks"])
        
        if isolated_webhooks:
            return isolated_webhooks
        
        if not matching_webhooks:
            matching_webhooks = [{"webhook": self.filter_config["other_webhook"], "role": ""}]
        
        return matching_webhooks

    async def post_discord_webhook(self, data: Dict[str, Any]) -> None:
        try:
            current_price = f'${round(data["offerPrice"], 2)}'
            avg_price = f'${round(data["average"], 2)}'
            amt_off = float(data["average"]) - float(data["offerPrice"])
            percent_off = f"{round((amt_off / float(data['average'])) * 100, 3)}%"

            webhook_urls = await self.match_filter(data)
            
            payload = {
                "embeds": [
                    {
                        "title": data["title"],
                        "url": f"https://www.amazon.com/dp/{data['asin']}",
                        "color": self.filter_config["embed_data"]["color"],
                        "fields": [
                            {"name": "Old Price", "value": avg_price, "inline": True},
                            {
                                "name": "New Price",
                                "value": current_price,
                                "inline": True,
                            },
                            {"name": "Discount", "value": percent_off, "inline": True},
                            {
                                "name": "Link",
                                "value": f"https://www.amazon.com/dp/{data['asin']}",
                                "inline": True,
                            },
                        ],
                        "author": {
                            "name": self.filter_config["embed_data"]["author_name"],
                            "icon_url": self.filter_config["embed_data"]["author_icon_url"],
                        },
                        "footer": {
                            "text": self.filter_config["embed_data"]["footer"],
                            "icon_url": self.filter_config["embed_data"]["footer_icon"],
                        },
                        "image": {"url": data["image"]},
                    }
                ],
                "username": self.filter_config["embed_data"]["username"],
                "avatar_url": self.filter_config["embed_data"]["avatar_url"],
                "attachments": [],
            }
        except Exception as e:
            traceback.print_exc()
            logging.error(f"Failed to create payload: {e}")
            return

        for webhook in webhook_urls:
            for webhook2 in webhook["webhook"]:
                await asyncio.sleep(random.uniform(2.5, 3.5))
                
                if webhook["role"]:
                    payload["content"] = f"<@&{webhook['role']}>"
                else:
                    payload["content"] = ""
                    
                response = await self.make_request(
                    "post", webhook2, {"Content-Type": "application/json"}, payload
                )
                
                if response.status_code == 429 or response.status_code == 417:
                    if data["_id"] in self.already_seen:
                        self.already_seen.remove(data["_id"])
                    await asyncio.sleep(2)

                if response.status_code != 204:
                    logging.error(
                        f"Failed to send webhook: {response.status_code} - {response.text}"
                    )

    async def get_deals(self, category: str, price: str, age: str, page: int) -> Optional[str]:
        url = f"https://saving.deals/top?page={page}&age={age}&off={price}&categories={category}"
        logging.debug(f"Requesting: {url}")

        response = await self.make_request("get", url, self.headers)

        if response is None:
            logging.error(f"No response received from {url}")
            return None

        if not hasattr(response, 'status_code'):
            logging.error(f"Invalid response object from {url}")
            return None

        if response.status_code != 200:
            logging.warning(f"Request to {url} returned status: {response.status_code}")
            return None

        return response.text

    async def parse_deals(self, resp: str) -> List[Dict[str, Any]]:
        try:
            return json.loads(resp.split("]\n2:")[1])[3]["initialData"]
        except:
            # print("Failed to parse deals")
            # print(resp)
            logging.error(f"Failed to parse deals: {resp}")
            return []

    async def save_regularly(self, already_seen: List[str]) -> None:
        while True:
            async with aiofiles.open("data.json", "w") as file:
                await file.write(json.dumps(already_seen, indent=4))
            await asyncio.sleep(10)

    async def handle_task(self, category: str, price: str, age: str, priority: bool) -> None:
        if priority:
            await asyncio.sleep(random.uniform(0.5, 1))
        
        if not priority:
            await asyncio.sleep(random.uniform(1.0, 5))

        deals = await self.get_deals(category, price, age, 1)
        if not deals:
            #print(f"No deals found for category {category} with price off {price}%")
            logging.info(f"No deals found for category {category} with price off {price}%")
            return

        parsed_deals = await self.parse_deals(deals)
        for deal in parsed_deals:
            deal_id = deal["_id"]
            if deal_id in self.already_seen:
                continue

            self.already_seen.append(deal_id)
            
            deal["categories"] = [category]

            await self.post_discord_webhook(deal)

            # print(f"Added deal: {deal['title']}")

    async def priorityTasks(self) -> None:
        while True:
            tasks = [self.handle_task(category, price, self.age, True) for category in self.filter_config["priority_category"] for price in self.filter_config["price_off"]]
            
            await asyncio.gather(*tasks)
    
            await asyncio.sleep(5)
            
    async def regularTasks(self) -> None:
        await asyncio.sleep(10)
        while True:
            tasks = [self.handle_task(category, price, self.age, False) for category in self.filter_config["regular_category"] for price in self.filter_config["price_off"]]
            
            await asyncio.gather(*tasks)
            
            await asyncio.sleep(63)

    async def main(self) -> None:
        asyncio.create_task(self.save_regularly(self.already_seen))

        await asyncio.gather(
            self.priorityTasks(),
            self.regularTasks()
        )
        
        while True:
            try:
                await asyncio.sleep(60)
            except KeyboardInterrupt:
                logging.info("Stopping")
                break


if __name__ == "__main__":

    configJson = "config.json"
    dataJson = "data.json"
    proxies = ["http://username:password@ip:port", "http://username:password@ip:port"]
    
    scraper = AmazonScraper(configJson, dataJson, proxies)
    asyncio.run(scraper.main())
