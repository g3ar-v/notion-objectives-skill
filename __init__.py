from mycroft import MycroftSkill, intent_handler


class NotionRoutine(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_handler('routine.notion.intent')
    def handle_routine_notion(self, message):
        self.speak_dialog('routine.notion')


def create_skill():
    return NotionRoutine()

