from collections import defaultdict

class Memory:
    def __init__(self):
        self.user_departments = {}
        self.bot_messages = defaultdict(list)
        self.admin_sessions = set()
        self.user_contexts = defaultdict(list)
        self.temp_files = {}

    def get_dept(self, user_id):
        return self.user_departments.get(user_id, "general")

    def set_dept(self, user_id, dept):
        self.user_departments[user_id] = dept

    def add_bot_msg(self, user_id, dept, msg_id):
        self.bot_messages[(user_id, dept)].append(msg_id)

    def get_bot_msgs(self, user_id, dept):
        return self.bot_messages.get((user_id, dept), [])

    def clear_bot_msgs(self, user_id, dept):
        self.bot_messages[(user_id, dept)] = []

    def add_context(self, user_id, role, content):
        self.user_contexts[user_id].append({"role": role, "content": content})
        if len(self.user_contexts[user_id]) > 20:
            self.user_contexts[user_id] = self.user_contexts[user_id][-20:]

    def get_context(self, user_id):
        return self.user_contexts.get(user_id, [])

    def clear_context(self, user_id):
        self.user_contexts[user_id] = []

    def add_admin_session(self, user_id):
        self.admin_sessions.add(user_id)

    def is_admin_session(self, user_id):
        return user_id in self.admin_sessions

    def set_temp_file(self, user_id, file_info):
        self.temp_files[user_id] = file_info

    def get_temp_file(self, user_id):
        return self.temp_files.get(user_id)

memory = Memory()
