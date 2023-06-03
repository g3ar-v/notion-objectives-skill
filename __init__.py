import os
import time
import datetime
from datetime import datetime as dt
from dotenv import load_dotenv
from notion_client import Client, APIErrorCode, APIResponseError
from core import Skill, intent_handler
from adapt.intent import IntentBuilder


class NotionObjectivesSkill(Skill):
    """
    Notion skill to access notion database and run routine based on a notion database
    """

    def __init__(self):
        super(NotionObjectivesSkill, self).__init__()
        self.notion_token = None
        self.database_id = None

    def initialize(self):
        # TODO setup exception handling for no access token or database
        load_dotenv()
        self.obj = []
        self.obj_color = []
        self.number = 0
        self.database_page = []
        self.notion_token = os.getenv("ACCESS_TOKEN")
        self.database_id = os.getenv("DATABASE_ID")
        self.notion = Client(auth=self.notion_token)
        # self.get_today_schedules(dt.now())

    @intent_handler(IntentBuilder('CreateObjectiveIntent').require('set').require(
        'objectives'))
    def _create_new_objectives(self):
        """ Create a notion objective with voice"""
        objective_name = self.get_response('what.is.objective.name')
        objective_type = self.get_response('what.is.objective.type')
        self.speak_dialog('confirm.create.objective', {'name': objective_name,
                                                       'type': objective_type})

    # Seperate load and notify and use decorator on notify
    @intent_handler(IntentBuilder('PriorityObjectivesIntent').require('query').require(
        'objectives'))
    def _load_priority_objectives(self):
        """ Loads priority 1 objectives from notion"""
        try:
            database_id = self.database_id
            self.database_page = self.notion.databases.query(
                    database_id=database_id,
                    filter={
                        "and": [
                            {
                                "property": "Status",
                                "status": {
                                    "does_not_equal": "Complete 🙌"
                                }
                            },
                            {
                                "property": "priority",
                                "select": {
                                    "equals": "1"
                                }
                            },
                            {
                                "or": [
                                    {
                                        "property": "Type",
                                        "select": {
                                            "equals": "Task 🔨"
                                        }
                                    },
                                    {
                                        "property": "Type",
                                        "select": {
                                            "equals": "Bug 🐞",
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                )
        except APIResponseError as error:
            if error.code == APIErrorCode.ObjectNotFound:
                self.log.exception(error)
                self.speak(error)
        else:
            self.log.info(self.database_page['results'])
            for index, objects in enumerate(self.database_page['results']):
                self.obj.append(objects['properties'].get('objective', {}).get(
                    'title', {})[0]['plain_text'])
                self.obj_color.append(objects['properties'].get('Type', {}).get(
                    'select', {}).get('color', {}))
                self.num_obj = index + 1

            self.notify(self.num_obj, self.obj, self.obj_color)

    def get_today_schedules(self, time_now: datetime):
        noon = datetime.time(12, 30, 0)
        noon_today = dt.combine(time_now.date(), noon)

        self.schedule_repeating_event(self._load_priority_objectives, noon_today,
                                      5 * 3600, name="objective_schedule")

    def __save_reminder_local(self, obj, obj_type):
        if 'objectives' in self.settings:
            self.settings['objectives'].append((obj, obj_type))
        else:
            self.settings['objectives'] = [(obj, obj_type)]

    def notify(self, number, obj, color):
        """ Notifies user of goal"""
        self.speak_dialog('Notify', {'number': number, 'obj': obj})
        for objectives in zip(range(1, number+1), color, obj):
            self.speak("{}, A {}: {}".format(
                objectives[0], 'task' if objectives[1] == 'yellow' else 'bug',
                objectives[2]))
            time.sleep(2)

    def stop(self):
        pass

    def shutdown(self):
        """ Stop the skill"""
        self.running = False


def create_skill():
    """ Create skill and return it to the loader """
    return NotionObjectivesSkill()


if __name__ == "__main__":
    notion = NotionObjectivesSkill()
    notion.initialize()
    notion._load_priority_objectives()
