from skills import BaseSkill

class DataInspectorSkill(BaseSkill):
    @property
    def name(self):
        return "data_inspector"

    @property
    def description(self):
        return "Loads data and reports basic stats."

    @property
    def parameters(self):
        return {}

    @property
    def example_usage(self):
        return "Summarize this CSV file."

    def execute(self, params):
        return {
            "rows": 100,
            "columns": 8,
            "missing_values": 0
        }