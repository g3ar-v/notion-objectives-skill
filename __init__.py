import asyncio
import os
import json 
from datetime import datetime
from mycroft import MycroftSkill, intent_handler
from notion_client import Client, APIErrorCode, APIResponseError

__author__ = 'vnyoyoko'
NOTION_SETTINGS = {}
notion_fp = os.path.join(os.path.dirname('/home/richard/'), 'notion_settings.json')
class NotionRoutine(MycroftSkill):
    """ Notion skill to access notion database and run routine based on a notion database"""

    def __init__(self):
        MycroftSkill.__init__(self)
        global NOTION_SETTINGS

        with open(notion_fp, 'r') as f:
            NOTION_SETTINGS = json.load(f)

        self.log.info("notion routine skill starting...")
    
    def initialize(self):
        # TODO setup exception handling for no access token or database
        
        self.log.info("initializing connection to notion...")
        self.database_page = []
        self.routine_dictionary = {} #Dictionary of time as KEY and goal as VALUE
        self.time_list = []

        access_token = NOTION_SETTINGS['access_token']
        # access_token = self.settings.get('access_token')
        os.environ['NOTION_TOKEN'] = access_token
        self.notion = Client(auth=os.environ['NOTION_TOKEN']) 
        self.load_routine()
        self.map_routine()


        
    def load_routine(self):
        try:
            # database_id = self.settings.get('database_id')
            database_id = NOTION_SETTINGS['database_id']
            # self.log.info(database_id)
            self.database_page = self.notion.databases.query(
                **{
                "database_id": database_id,
                })
            # await asyncio.sleep(delay)

            # self.log.info(self.database_page)
            self.log.info("connected to notion database...")
            self.map_routine()
            self.key_to_datetime()
            self.log.info("loaded database content")
            # self.notification_manager()
            # self.log.info(type) 
            asyncio.run(self.notification_manager())
        except APIResponseError as error:
            if error.code == APIErrorCode.ObjectNotFound:
                self.log.exception("could not connnect to database")


    def map_routine(self):
        """ load database from notion into dictionary"""
        for database_index, database_value in enumerate(self.database_page['results']):
            key = self.database_page['results'][database_index]['properties']['Time']['formula']['string'].replace(
                " ", "")
            goal_items = self.database_page['results'][database_index]['properties']['GOAL']['rich_text'][0][
                'plain_text']

            # split up goals in the list
            goal = goal_items

            self.routine_dictionary[key] = goal
            # if key not in self.routine_dictionary:
            #     self.routine_dictionary[key] = []
            #     # self.routine_dictionary[key].extend(goal)
            # else:
            #     pass
            #     # TODO raise exception data not received from Notion


    def key_to_datetime(self):
            """ converts time key into datetime object"""
            for key in self.routine_dictionary.keys():
                self.time_list.append(str(datetime.strptime(key, "%I:%M%p").time()))

    def datetime_to_key(self, time):
        """ converts datetime object to string(time key) in routine_dict"""
        return datetime.strptime(time, "%H:%M:%S").time().strftime("%-I:%M%p")

    async def notification_manager(self):
        """ Handles the removal of time from time_list and notifying user of goal"""

        # self.log.info(type(self.timer()))
        while True:
            #optimise by popping from list while retreiving from database to make it pythonic
            time = await self.timer()
            goal = self.routine_dictionary[self.datetime_to_key(time)]
            self.log.info(time)
            self.log.info(goal)
            self.notify(time, goal)

            if time in self.time_list:
                self.time_list.remove(time)

  
    async def timer(self):
        """ Listener for any time in time_list that matches current_time"""
        self.log.info("timer started")
        while True:

            now = datetime.now()
            current_hour = now.strftime("%H")
            current_min = now.strftime("%M")

            for time in self.time_list:
                if current_hour == time[0:2]:  # gets 24 Hours value
                    if current_min == time[3:5]:  # gets minute value
                        return time

    def notify(self, time, goal):
        """ Notifies user of goal"""
        self.speak_dialog('notify', {'time': time}, {'goal': goal})

    @intent_handler('routine.notion.intent')
    def handle_routine_notion(self, message):
        """ Handles the routine.notion intent"""
        self.speak_dialog('routine.notion')


    def stop(self):
        pass

def create_skill():
    """ Create skill and return it to the loader"""
    return NotionRoutine()


if __name__ == '__main__':
    notion = NotionRoutine()
    notion.initialize()