from argparse import ArgumentParser

class GDBArgumentParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        self.short_description = kwargs.pop("short_description")
        if not self.short_description is None:
            self.short_description += "\nusage: "
        super().__init__(*args, **kwargs)

    def format_help(self):
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups, prefix=self.short_description)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()