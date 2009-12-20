/* 

	Easy Scroll v1.0
	written by Alen Grakalic, provided by Css Globe (cssglobe.com)
	please visit http://cssglobe.com/post/1495/easy-scroll-accessible-content-scroller
	
*/

this.easyscroll = function(){
	
	// id of the container element 
	var id = "myContent";
	
	// navigation buttons text
	var nav = ["Scroll Up", "Scroll Down", "Reset"];
	
	//	id for each navigation button (OPTIONAL)
	var navId = ["btnUp", "btnDown", "btnReset"];

	// movement speed
	var speed = 2;
	
	// desired height of the container element (in pixels)
	var height = 200;
	
	//
	// END CONFIG
	// do not edit below this line (unless you want to of course :) )
	//

	var obj = document.getElementById(id);
	
	obj.up = false;
	obj.down = false;
	obj.fast = false;

	var container = document.createElement("div");
	var parent = obj.parentNode;
	container.id="easyscroll";
	parent.insertBefore(container,obj);
	parent.removeChild(obj);	
	
	container.style.position = "relative";
	container.style.height = height + "px";
	container.style.overflow = "hidden";
	obj.style.position = "absolute";
	obj.style.top = "0";
	obj.style.left = "0";
	container.appendChild(obj);
	
	var btns = new Array();
	btns[0] = document.getElementById('up');
	btns[1] = document.getElementById('down');
	
	btns[0].onmousedown = function(){
		obj.up = true;
		this.className = "over";
	};
	btns[0].onmouseup = function(){
		obj.up = false;
		this.className = "";
	};		
	btns[1].onmousedown = function(){
		obj.down = true;
		this.className = "over";		
	};
	btns[1].onmouseup = function(){
		obj.down = false;
		this.className = "";
	};
		
	this.start = function(){				
		var newTop;
		var objHeight = obj.offsetHeight;
		var top = obj.offsetTop;
		var fast = (obj.fast) ? 2 : 1;
		if(obj.down){		 
			newTop = ((objHeight+top) > height) ? top-(speed*fast) : top;	
			obj.style.top = newTop + "px";
		};	
		if(obj.up){		 
			newTop = (top < 0) ? top+(speed*fast) : top;
			obj.style.top = newTop + "px";
		};
	};	
	obj.interval = setInterval("start()", 20);		
		
};


//
// script initiates on page load. 
//

this.addEvent = function(obj,type,fn){
	if(obj.attachEvent){
		obj['e'+type+fn] = fn;
		obj[type+fn] = function(){obj['e'+type+fn](window.event );}
		obj.attachEvent('on'+type, obj[type+fn]);
	} else {
		obj.addEventListener(type,fn,false);
	};
};
addEvent(window,"load", easyscroll);
