var REMOTECALLDELTA = 50;


// prevent calls to get invoked short after another
// as one will get lost because melange won't pickup the fast
// window.location.href change
var Remote = new Class({
    initialize: function() {
        this.lastRemoteCallTime = 0;
    },

    call: function(url) {
        var now = new Date().getTime();
        if(this.lastRemoteCallTime + REMOTECALLDELTA > now) {
            setTimeout(function() {
                remote.call(url);
            }, 50);
        } else {
            this.lastRemoteCallTime = now;
            this._call(url);
        }
    },

    _call: function(url) {
        window.location.href = url;
    }
});


var Widget = new Class({
    initialize: function(main) {
        this.api = {};
        this.main = main || function() {};
        this.callbacks = {};
        this.callbackId = 0;

        remote.call('melange://init');
    },

    main: function() {
        this.main();
    },

    registerMethod: function(method) {
        this.api[method] = function() {
            var args = [];
            var cb = null;

            Array.each(arguments, function(arg) {
                if(typeof arg == 'function')
                    cb = arg;
                else
                    args.push(arg);
            });

            widget.callRemote(method, args, cb);
        }
    },

    callRemote: function(method, args, cb) {

        var data = {};
        if(cb !== null) {
            var callbackId = this.callbackId++;
            this.callbacks[callbackId] = cb;
            data['callback_id'] = callbackId;
        }

        var i = 0;
        Array.each(args, function(v) {
            data['argument_' + i.toString()] = v
            i++;
        });

        var qs = Object.toQueryString(data);

        remote.call('melange://call/' + method + '?' + qs);
    },

    invokeCallback: function(callbackId, data) {
        var callback = this.callbacks[callbackId];
        callback(data);
        delete this.callbacks[callbackId];
    }
});



var ConfigurationWrapper = new Class({
    Implements: Events,

    get: function(option) {
        //return this._python_config[option];
    },

    set: function(option, value) {
        if(value === undefined) {
            // Javascript allows this, but I don't want that.
            throw new TypeError("`config.set` expects two arguments");
        }
        //this._python_config[option] = value;
    },

     //
     // Invoked on every gpyconf event.
     // Uses MooTools' Events for dispatching.
     //
    on_config_event: function() {
        // `arguments` object to real `Array`: 
        var args = Array.prototype.slice.apply(arguments);
        // First argument is the event name. 
        var event_name = args.shift();
        this.fireEvent(event_name, args);
    }
});


var remote = new Remote();
var widget = null;

window.addEvent('domready', function() {
    widget = new Widget(window.main);
});
