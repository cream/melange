function ipc_call(bus, object, method, arguments, callback) {
    data = {
        "bus": bus,
        "object": object,
        "method": method,
        "arguments": '["' + arguments.join('","') + '"]'
        };
    $.post("http://localhost:8080/ipc/call", data, callback, "json");
    }
