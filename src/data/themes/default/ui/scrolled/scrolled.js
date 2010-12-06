window.addEvent('domready', function() {
    $$('.scrolled').each(function(obj){
        var speed = 3;

        var parent = obj.parentNode;

        var content = document.createElement("div");
        content.style.position = 'relative';
        content.style.top = '0px';
        content.innerHTML = obj.innerHTML;
        obj.innerHTML = '';

        var container = document.createElement("div");
        container.className = 'container';
        height = document.defaultView.getComputedStyle(obj, null).getPropertyValue('height');
        height = height.replace('px', '');
        container.style.height = height - 30 + "px";
        container.style.overflow = 'hidden';
        container.appendChild(content);

        var control_up = document.createElement("div");
        control_up.innerHTML = '<img src="/common/ui/scrolled/images/up.png" />';
        control_up.id = 'control_up';
        control_up.className = 'control_up';

        var control_down = document.createElement("div");
        control_down.innerHTML = '<img src="/common/ui/scrolled/images/down.png" />';
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
