from cream.config import Configuration, fields

class Configuration(Configuration):
    widgets = fields.ListField(hidden=True)
