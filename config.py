from cream.config import Configuration, fields

class Configuration(Configuration):
    widgets = fields.DictField(hidden=True)
