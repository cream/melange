function getWidgetInstanceId() {
    return window.location.search.replace('?id=', '');
}

var Widget = new Class({

    initialize: function(main) {
        this.id = getWidgetInstanceId();
        this.main = main;
        this.callbacks = {};

        this.socket = new WebSocket('ws://127.0.0.1:8085/ws/' + this.id);

        this.socket.onopen = function(){
            var msg = {type: 'init', id: this.id};
            this.socket.send(JSON.encode(msg));
        }.bind(this);

        this.socket.onmessage = function(e){
            var data = JSON.decode(e.data);

            if(data.type == 'init'){

                Array.each(data.methods, function(method) {
                    this[method] = function() {
                        var args = [];
                        var cb = function() {};

                        Array.each(arguments, function(arg) {
                            if(typeof arg == 'function')
                                cb = arg;
                            else
                                args.push(arg);
                        });

                        this.callRemote(method, args, cb);
                    }
                }, this);


                this.main();

            } else if(data.type == 'call') {
                this.callbacks[data.callback_id](data.arguments);
            }

        }.bind(this);
    },

    callRemote: function(methodName, arguments, cb){
        var callback_id = '' + new Date().getTime();
        this.callbacks[callback_id] = cb;
        var msg = {type: 'call',
                   id: this.id,
                   method: methodName,
                   callback_id: callback_id,
                   arguments: arguments
        };
        this.socket.send(JSON.encode(msg));
    }

});
