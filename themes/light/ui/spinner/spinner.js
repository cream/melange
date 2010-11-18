var Spinner = new Class({
    initialize: function(elm) {
        this.spokes = 9;
        this.interval_id = null;

        elm.innerHTML = '';

        this.canvas = new Element('canvas', {
            'width': '30',
            'height': '30',
            'style': 'display: inline;'
        });

        this.container = new Element('div', {
            })
        this.container.grab(this.canvas, 'top')
    
        elm.grab(this.container, 'top');

        this.ctx = this.canvas.getContext('2d');
        this.ctx.translate(15, 15);	// Center the origin
        this.ctx.lineWidth = 3;
        this.ctx.lineCap = "round"
    },
    start: function() {
        this.interval_id = this.draw.periodical(100, this);
    },
    stop: function() {
        $clear(this.interval_id);
    },
    draw: function() {
        this.ctx.clearRect(-15, -15, 30, 30);		// Clear the image
        this.ctx.rotate(Math.PI*2/this.spokes);	// Rotate the origin
        for (var i=0; i<this.spokes; i++) {
            this.ctx.rotate(Math.PI*2/this.spokes);	// Rotate the origin
            this.ctx.strokeStyle = "rgba(0,0,0,"+ i/this.spokes +")";	// Set transparency
            this.ctx.beginPath();
            this.ctx.moveTo(0, 6);
            this.ctx.lineTo(0, 14);
            this.ctx.stroke();
        }
    }
    })
