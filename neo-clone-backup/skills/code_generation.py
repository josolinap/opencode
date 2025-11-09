from skills import BaseSkill

class CodeGenerationSkill(BaseSkill):
    @property
    def name(self):
        return "code_generation"

    @property
    def description(self):
        return "Generates/explains Python ML code snippets."

    @property
    def parameters(self):
        return {}

    @property
    def example_usage(self):
        return "Generate a scikit-learn classifier code."

    def execute(self, params):
        return {
            "code": "from sklearn.ensemble import RandomForestClassifier\nclf = RandomForestClassifier().fit(X, y)"
        }