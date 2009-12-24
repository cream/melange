cream.constants.define('BIND_BEFAULT_INTERVAL', 1000);
cream.constants.define('API_REQUEST_BASE_URL', '/ipc/call');
// We may not use locahost:port here because that ends in an OPTIONS request
// rather than a GET or POST request (at least in firefox/gecko which many
// developers will use to develop widgets for now)

function popkey(obj, key, _default) {
    if(!$defined(obj[key])) return _default;
    var v = obj[key];
    delete obj[key];
    return v;
};

cream.implement({
    APIRequest: new Class({
        Extends: Request.JSON,

        initialize: function(options, request_options) {
            // TODO: if(!path) throw new ..
            var callback = popkey(options, 'callback', function() {});
            if($type(options.data) == 'function') {
                options.data = options.data();
            }
            options.arguments = '["' + popkey(options, 'params').join('","') + '"]';

            this.parent($merge(request_options || {}, {
                url: cream.constants.API_REQUEST_BASE_URL,
                method: 'POST',
                onSuccess: callback
            }));

            this.post_data = options;
        }
    }),

    call: function(options) {
        var request = new cream.APIRequest(options);
        request.POST(request.post_data);
    },

    call_periodically: function(options) {
        // TODO: if(!interval) throw new ...
        var request = new cream.APIRequest(options, {
            limit: options.interval,
            delay: popkey(options, 'interval'),
            initialDelay: 0
        });
        request.startTimer(request.post_data);
    }
});

Element.implement_in_namespace('cream', {
    bind: function(options) {
        conversion_callback = options.convert || function(a) {return a;}
        var elem = this;
        if(!$defined(options.interval))
            options.interval = cream.constants.BIND_DEFAULT_INTERVAL;
        cream.call_periodically($merge(options, {
            callback: function(response) {
                elem.set('text', conversion_callback(response.return_value));
            }
        }));
    }
});
