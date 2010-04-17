from cream.contrib.melange import api

class Proxy(object):

    def __init__(self, path=[]):

        self.path = path


    def __call__(self, *args, **kwargs):

        print "'{0}' has been called:"
        print "  " + args
        print "  " + kwargs


# This will register the API-class as `widget.example`
# accessable from your JavaScript code.
@api.register('example')
class Example(api.API):

    def doit(self, arg):

        print "Got '{0}'...".format(arg)
        return arg.capitalize()
