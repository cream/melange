from cream.config import Configuration, fields

class Configuration(Configuration):
    widgets = fields.DictField(hidden=True)

    profiles = [{'name' : 'Some Profile name'}]
