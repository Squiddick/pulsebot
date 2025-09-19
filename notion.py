import os
from http.client import responses
from ssl import get_protocol_name
from notion_client import Client
import notion_client
import logging
import json
import re
from Logger import Logger
import os
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv('NOTION_TOKEN')

class Config:
    token = NOTION_TOKEN
    database_url = "https://www.notion.so/26b83b27813680cc9d18fa7f9e7cda69?v=26b83b27813680e89d78000cdef4b861"


class Connection:
    def __init__(self):
        self.notion = notion_client.Client(auth=Config.token)
        self.response = self.__query(self.notion)
        self.logger = Logger()

    @staticmethod
    def __extract_db_id():
        import re
        match_key = re.search(r'([a-f0-9]{32})', Config.database_url)
        if match_key:
            return match_key.group(1)

    def __query(self, connection, filter_params=None):
        db_id = self.__extract_db_id()
        try:
            response = connection.databases.query(database_id=db_id, filters=filter_params)
        except Exception as e:
            self.logger.logger.warning(f"Response error: {e}", exc_info=True)

        #json dump
        with open("data.json", "w", encoding="utf-8") as json_f:
            json.dump(response,json_f, ensure_ascii=False, indent=4)
        return response

    def __findBreaks(self, string):
        pattern = r"^(?:[^}]*}){3}[^}]*(})"
        match = re.search(pattern, string)
        if match:
            return match.start(1)
        return None
    def __add_multiselect_tag(self, page, tag):
        page["properties"]["Tags"] = {
            "type": "multi_select",
            "multi_select": [
                {
                    "name": f"{tag}",
                }
            ]
        }
    def get_properties(self):
        db_id = self.__extract_db_id()
        database = self.notion.databases.retrieve(database_id=db_id)
        props = database.get("properties", {})
        tags = None
        for prop_name, prop_details in props.items():
            multi_select = prop_details.get("multi_select", {}).get("options",[])
            tags = [option["name"] for option in multi_select]
        return tags

    def addPage(self, content, tag=None):
        new_page = { #можно вписывать и вручную в .create(new_page["parent"], new_page["properties"]...
            "parent": {"database_id": str(self.__extract_db_id())},
            "properties": {
                "Name": {
                "title": [
                    {
                        "type": "text",
                        "text":  {
                            "content": f"{content}",
                        }

                }
                ]
                }
            },
        }
        if tag is not None:
            self.__add_multiselect_tag(new_page, tag)
        try:
            created_page = self.notion.pages.create(**new_page)
        except Exception as e:
            self.logger.logger.warning(f"Could not create page: {e}", exc_info=True)
        finally:
            self.logger.logger.warning("The page was created!")
