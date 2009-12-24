var Constants = new Class({
    define: function(name, value) {
        // TODO: check wether we have the `const` statement and use it if given
        this[name] = value;
    }
});

var cream = {
    constants: new Constants()
};

cream.implement = function(obj) {
    for(var k in obj) { cream[k] = obj[k]; }
}

Element.implement_in_namespace = function(namespace, objects) {Element.implement(objects);}
// throw away namespace thing for now
