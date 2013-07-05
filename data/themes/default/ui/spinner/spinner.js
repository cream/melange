var Spinner = new Class({
    initialize: function(elm, size) {
        this.spokes = 9;
        if(size)
            this.size = size
        else
            this.size = 30
        this.interval_id = null;

        elm.innerHTML = '';

        this.canvas = new Element('canvas', {
            'width': this.size,
            'height': this.size,
            'style': 'display: inline;'
        });

        this.container = new Element('div', {
            })
        this.container.grab(this.canvas, 'top')

        elm.grab(this.container, 'top');

        this.ctx = this.canvas.getContext('2d');
        this.ctx.translate(this.size/2, this.size/2);	// Center the origin
        this.ctx.lineWidth = this.size/10;
        this.ctx.lineCap = "round";
    },
    start: function() {
        this.interval_id = this.draw.periodical(100, this);
    },
    stop: function() {
        this.interval_id = clearTimeout(this.interval_id);
    },
    draw: function() {
        this.ctx.clearRect(-this.size/2, -this.size/2, this.size, this.size);		// Clear the image
        this.ctx.rotate(Math.PI*2/this.spokes);	// Rotate the origin
        for (var i=0; i<this.spokes; i++) {
            this.ctx.rotate(Math.PI*2/this.spokes);	// Rotate the origin
            this.ctx.strokeStyle = "rgba(0,0,0,"+ i/this.spokes +")";	// Set transparency
            this.ctx.beginPath();
            this.ctx.moveTo(0, this.size/5);
            this.ctx.lineTo(0, this.size/2.5);
            this.ctx.stroke();
        }
    }
    })
