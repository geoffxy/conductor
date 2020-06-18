

class InvalidRuleArguments(RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvalidTargetName(RuntimeError):
    def __init__(self, target_name):
        super().__init__("Invalid target name '{}'.".format(target_name))
