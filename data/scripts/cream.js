var Constants = new Class({
    define: function(name, value) {
        // TODO: check wether we have the `const` statement and use it if given
        this[name] = value;
    }
});

function popkey(obj, key, _default) {
    if(!$defined(obj[key])) return _default;
    var v = obj[key];
    delete obj[key];
    return v;
};

var cream = {
    constants: new Constants(),

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
};

cream.constants.define('BIND_BEFAULT_INTERVAL', 1000);
cream.constants.define('API_REQUEST_BASE_URL', '/ipc/call');
// We may not use locahost:port here because that ends in an OPTIONS request
// rather than a GET or POST request (at least in firefox/gecko which many
// developers will use to develop widgets for now)

Element.implement_in_namespace = function(namespace, objects) {Element.implement(objects);}
// throw away namespace thing for now

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


$(document).ready(function() {
    $('.scrolled').each(function(){
        var speed = 2;

        var obj = this;
        var parent = obj.parentNode;
    
        var content = document.createElement("div");
        content.style.position = 'relative';
        content.style.top = '0px';
        content.innerHTML = obj.innerHTML;
        obj.innerHTML = '';
    
        var container = document.createElement("div");
        container.id = 'container';
        container.className = 'container';
        container.style.height = obj.offsetHeight - 28 + "px";
        container.style.overflow = 'hidden';
        container.appendChild(content);
    
        var control_up = document.createElement("div");
        control_up.innerHTML = '<img src="images/up.png" />';
        control_up.id = 'control_up';
        control_up.className = 'control_up';
    
        var control_down = document.createElement("div");
        control_down.innerHTML = '<img src="images/down.png" />';
        control_down.id = 'control_down';
        control_down.className = 'control_down';
    
        obj.appendChild(container);
        obj.insertBefore(control_up, container);
        obj.appendChild(control_down);

        obj.up = false;
        obj.down = false;
        obj.fast = false;
    
        control_up.onmousedown = function(){
            obj.up = true;
            obj.interval = setInterval(obj.scroll, 20);
        };
        control_up.onmouseup = function(){
            obj.up = false;
            clearInterval(obj.interval);
        };
        control_down.onmousedown = function(){
            obj.down = true;
            obj.interval = setInterval(obj.scroll, 20);
        };
        control_down.onmouseup = function(){
            obj.down = false;
            clearInterval(obj.interval);
        };
            
        obj.scroll = function(){
            var h = content.offsetHeight;
            var t = content.offsetTop - container.offsetTop;
            if(obj.down & (t > -(h-container.offsetHeight))){
                content.style.top = t - speed + "px";
            };
            if(obj.up & (t < 0)){
                newTop = (t < 0) ? t+speed : t;
                content.style.top = newTop + "px";
            };
        };
    });
});
