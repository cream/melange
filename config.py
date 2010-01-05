from cream.config import Configuration, fields

class Configuration(Configuration):
    widgets = fields.DictField(static=True, hidden=True)
