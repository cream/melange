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
	var speed = 5;
	
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
	var ul = document.createElement("ul");
	ul.id="easyscrollnav";
	for (var i=0;i<nav.length;i++){
		var li = document.createElement("li");
		li.innerHTML = nav[i];
		li.id = navId[i];
		btns.push(li);
		ul.appendChild(li);
	};
	parent.insertBefore(ul,container);
	
	btns[0].onmouseover = function(){
		obj.up = true;
		this.className = "over";
	};
	btns[0].onmouseout = function(){
		obj.up = false;
		this.className = "";
	};		
	btns[1].onmouseover = function(){
		obj.down = true;
		this.className = "over";		
	};
	btns[1].onmouseout = function(){
		obj.down = false;
		this.className = "";
	};		
	btns[0].onmousedown = btns[1].onmousedown = function(){
		obj.fast = true;
	};	
	btns[0].onmouseup = btns[1].onmouseup = function(){
		obj.fast = false;
	};		
	btns[2].onmouseover = function(){ 		
		this.className = "over";
	};	
	btns[2].onmouseout = function(){ 		
		this.className = "";
	};		
	btns[2].onclick = function(){ 		
		obj.style.top = "0px";
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
	obj.interval = setInterval("start()",50);		
		
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
addEvent(window,"load",easyscroll);