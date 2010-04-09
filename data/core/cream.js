var API = new Class({
    Implements: Events
    });

var Widget = new Class({
    init: function() {
        _python.init()
        },
    api: new API()
    });

var widget = new Widget();
