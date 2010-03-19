var MooScroll = new Class({
    Implements: Options,
    options: {
        selector: '.scroll',
        increment:30,
        upBtnClass:'upBtn',
        downBtnClass:'downBtn',
        scrollBarClass:'scrollBar',
        scrollHandleClass:'scrollHandle',
        scrollHandleBGClass:'scrollHandleBG',	
        scrollHandleTopClass:'scrollHandleTop',
        scrollHandleMiddleClass:'scrollHandleMiddle',			
        scrollHandleBottomClass:'scrollHandleBottom',
        scrollControlsYClass: 'scrollControlsY',
        handleOpacity:1,
        handleActiveOpacity:0.85,
        disabledOpacity:0.5,
        fullWindowMode:false,
        smoothMooScroll:{
            toAnchor:true,
            toMooScrollArea:true
        },
        restrictedBrowsers:[Browser.Engine.presto925,Browser.Platform.ipod,Browser.Engine.webkit419]//Opera 9.25 or lower, Safari 2 or lower, iPhone/iPod Touch
    },
    
    initialize: function(options){
        //don't run in restricted browsers
        if(this.options.restrictedBrowsers.contains(true)){return;}
        
        this.setOptions(options);		
        this.mooScrollAreas = [];
        this.windowFxScroll = new Fx.Scroll(document.window,{wait: false});

        $(document.body).getElements(this.options.selector).each(function(item,index){
            var scrollArea = new MooScrollArea(this.options, item,this.windowFxScroll);
            this.mooScrollAreas.include(scrollArea);
            if(this.options.smoothMooScroll.toAnchor || this.options.smoothMooScroll.toMooScrollArea){				
                this.smoothMooScroll = new SmoothMooScroll({toAnchor:this.options.smoothMooScroll.toAnchor,toMooScrollArea:this.options.smoothMooScroll.toMooScrollArea},scrollArea.contentEl,this.windowFxScroll);
            }
        }.bind(this));
    },
    
    loadContent:function(content){
        this.mooScrollAreas.each(function(item,index){
            item.loadContent(content);
        });
    },
    
    refresh:function(){
        this.mooScrollAreas.each(function(item,index){
            item.refresh();
        });
    },
    
    setSlider:function(v){
        this.mooScrollAreas.each(function(item,index){
            item.setSlider(v);			
        });
    }
});

var MooScrollArea = new Class({
    Implements: Options,		

    initialize: function(options, parentEl, windowFxScroll){
        this.windowFxScroll = windowFxScroll;
        this.setOptions(options);
        this.parentEl = parentEl.setProperty('rel', 'MooScrollArea');
        aaa = this;
        this.parentEl.refresh = function(){aaa.refresh()};
        this.viewPort = {x:$(window).getSize().x,y:$(window).getSize().y};
        this.parentElPadding = this.parentEl.getStyles('padding-top','padding-right','padding-bottom','padding-left');
        this.paddingHeight = parseFloat(this.parentEl.getStyle('padding-top'))+parseFloat(this.parentEl.getStyle('padding-bottom'));
        this.paddingWidth = parseFloat(this.parentEl.getStyle('padding-left'))+parseFloat(this.parentEl.getStyle('padding-right'));
        
        this.contentEl = new Element('div',{'class':'contentEl'}).adopt(this.parentEl.getChildren()).inject(this.parentEl,'top');
        this.parentEl.setStyle('overflow', 'hidden').setStyles({
            'padding':0, 
            width:parseFloat(this.parentEl.getStyle('width')) + this.paddingWidth,	
            height:parseFloat(this.parentEl.getStyle('height')) +  this.paddingHeight	
        });
        
        this.borderHeight = parseFloat(this.parentEl.getStyle('border-top-width'))+parseFloat(this.parentEl.getStyle('border-bottom-width'));
        this.contentEl.setStyles({'height':this.parentEl.getSize().y-this.borderHeight, overflow:'hidden','padding':0});
        this.paddingEl = new Element('div',{'class':'paddingEl'}).adopt(this.contentEl.getChildren()).inject(this.contentEl,'top').setStyles(this.parentElPadding);
        
        if(this.options.fullWindowMode){
            //turn off overflow for html element here so non-javascript users can still scroll
            $(document).getElement('html').setStyle('overflow','hidden');
            this.parentEl.setStyles({ 'height':'100%', 'width':'100%', 'position':'absolute' });
            this.contentEl.setStyles({ 'height':'100%', 'width':'100%', 'position':'absolute'});		
        }
        
        //Add Control Elements
        this.scrollControlsYWrapper = new Element('div', {	'class': this.options.scrollControlsYClass	}).inject(this.parentEl,'bottom');
        this.upBtn = new Element('div', {	'class': this.options.upBtnClass	}).inject(this.scrollControlsYWrapper,'bottom');
        this.downBtn = new Element('div', {	'class': this.options.downBtnClass	}).inject(this.scrollControlsYWrapper,'bottom');
        this.scrollBar = new Element('div', {	'class': this.options.scrollBarClass	}).inject(this.scrollControlsYWrapper,'bottom');
        this.scrollHandle = new Element('div', {	'class': this.options.scrollHandleClass	}).inject(this.scrollBar,'inside');
        this.scrollHandle.fade('hide');
        this.scrollHandleTop = new Element('div', {	'class': this.options.scrollHandleTopClass }).inject(this.scrollHandle,'inside');
        this.scrollHandleBG = new Element('div', {	'class': this.options.scrollHandleBGClass }).inject(this.scrollHandle,'inside');
        this.scrollHandleMiddle = new Element('div', {	'class': this.options.scrollHandleMiddleClass }).inject(this.scrollHandle,'inside');
        this.scrollHandleBottom = new Element('div', {	'class': this.options.scrollHandleBottomClass }).inject(this.scrollHandle,'inside');
        this.coverUp = new Element('div').inject(this.scrollControlsYWrapper,'bottom');
        
        this.overHang = this.paddingEl.getSize().y - this.parentEl.getSize().y   ;
        
        this.setHandleHeight();
        
        if(this.overHang <=0){this.greyOut();}

        this.initSlider();		
        
        this.parentEl.addEvents({
            'mousewheel': function(e){
                e = new Event(e).stop();							
                // Mousewheel UP 
                if (e.wheel > 0) { this.scrollUp(true); }				
                // Mousewheel DOWN
                else if (e.wheel < 0) { this.scrollDown(true); }			
            }.bind(this),
            'keydown': function(e){	
                if (e.key === 'up') { 
                    e = new Event(e).stop();
                    this.scrollUp(true); 					
                } 						
                else if (e.key === 'down' || e.key === 'space') { 
                    e = new Event(e).stop();
                    this.scrollDown(true);
                }			
            }.bind(this),			
            
            'click':function(e){				
                this.hasFocus = true;				
                this.hasFocusTimeout = (function(){
                    $clear(this.hasFocusTimeout);
                    this.hasFocus = true;
                }.bind(this)).delay(50);				
            }.bind(this),

            'mouseover': function(e) {
                this.refresh();
                this.scrollHandle.fade(1);
            }.bind(this),

            'mouseout': function(e) {
                this.scrollHandle.fade(0);
            }.bind(this)
        });
        
        this.contentEl.addEvents({
            'scroll': function(e){
                this.slider.set(this.contentEl.getScroll().y);			
            }.bind(this)
        })
        
        this.scrollHandle.addEvents({
                'mousedown': function(e){					
                    this.scrollHandle.addClass(this.options.scrollHandleClass +'-Active').setStyle('opacity',this.options.handleActiveOpacity);
                }.bind(this)
        });
        
        document.addEvents({
            'mouseup': function(e){					
                this.scrollHandle.removeClass(this.options.scrollHandleClass +'-Active').setStyle('opacity',this.options.handleOpacity);
                this.upBtn.removeClass(this.options.upBtnClass +'-Active');
                this.downBtn.removeClass(this.options.downBtnClass +'-Active');
            }.bind(this),
            
            'keydown':function(e){				
                if( (this.hasFocus ||this.options.fullWindowMode) && (e.key === 'down' || e.key === 'space' ||e.key === 'up') ){	this.parentEl.fireEvent('keydown',e);		}
            }.bind(this),
            
            'click':function(e){				
                this.hasFocus = false;									
            }.bind(this)			
        });
        
        window.addEvent('resize', function() {			

        $clear(this.refreshTimeout);
            if (this.options.fullWindowMode) {
                this.refreshTimeout = (function(){
                    $clear(this.refreshTimeout);
                    if (this.viewPort.x != $(window).getSize().x || this.viewPort.y != $(window).getSize().y) {
                        this.refresh();
                        this.viewPort.x = $(window).getSize().x;
                        this.viewPort.y = $(window).getSize().y;
                    }
                }.bind(this)).delay(250);
            }	
        }.bind(this));
        
        this.upBtn.addEvents({
                'mousedown': function(e){					
                    $clear(this.upInterval);
                    $clear(this.downInterval);
                    this.upInterval = this.scrollUp.periodical(10,this);
                    this.upBtn.addClass(this.options.upBtnClass +'-Active');					
                }.bind(this),
                
                'mouseup': function(e){
                    $clear(this.upInterval);
                    $clear(this.downInterval);					
                }.bind(this),
                
                'mouseout': function(e){
                    $clear(this.upInterval);
                    $clear(this.downInterval);
                }.bind(this)
        });
            
        this.downBtn.addEvents({
                'mousedown': function(e){
                    $clear(this.upInterval);
                    $clear(this.downInterval);
                    this.downInterval = this.scrollDown.periodical(10,this);
                    this.downBtn.addClass(this.options.downBtnClass +'-Active');
                }.bind(this),
                
                'mouseup': function(e){
                    $clear(this.upInterval);
                    $clear(this.downInterval);
                }.bind(this),
                
                'mouseout': function(e){
                    $clear(this.upInterval);
                    $clear(this.downInterval);
                }.bind(this)
        });
        
        
    },
    
    initSlider:function(){
        this.slider = new Slider(this.scrollBar, this.scrollHandle, {	
            range:[0, Math.round(this.overHang )],	
            mode: 'vertical',	
            onChange: function(step,e){
                this.contentEl.scrollTo(0, step);
            }.bind(this)
        });
    },

    scrollUp:function(scrollPageWhenDone){		
        var target = this.contentEl.getScroll().y - 30;// this.options.increment;
        this.slider.set(target);
        if(this.contentEl.getScroll().y <= 0 && scrollPageWhenDone){
            document.window.scrollTo(0 ,document.window.getScroll().y - this.options.increment );
        }
    },
    
    scrollDown:function(scrollPageWhenDone){		
        var target = this.contentEl.getScroll().y + this.options.increment;
        this.slider.set(target);
        var onePercent = (1*this.paddingEl.getSize().y)/100;
        var atBottom = 	(this.paddingEl.getSize().y - this.parentEl.getSize().y)<= (this.contentEl.getScroll().y + onePercent);	
        if(atBottom && scrollPageWhenDone){
            document.window.scrollTo(0 ,document.window.getScroll().y + this.options.increment );
        }
    },
    
    setHandleHeight:function(){		
        var handleHeightPercent = (100 - ((this.overHang*100)/this.paddingEl.getSize().y));		
        this.handleHeight = ((handleHeightPercent*this.parentEl.getSize().y)/100) - (this.scrollHandleTop.getSize().y + this.scrollHandleBottom.getSize().y );
        if((this.handleHeight + this.scrollHandleTop.getSize().y + this.scrollHandleBottom.getSize().y ) >= this.scrollBar.getSize().y){
            this.handleHeight-=( this.scrollHandleTop.getSize().y + this.scrollHandleBottom.getSize().y )*2;
        }
        if(this.scrollHandle.getStyle('min-height') && this.handleHeight < parseFloat(this.scrollHandle.getStyle('min-height'))){
            this.handleHeight = parseFloat(this.scrollHandle.getStyle('min-height')) + this.scrollHandleBottom.getSize().y + this.scrollHandleTop.getSize().y;
        }	
        this.scrollHandle.setStyles({'height':this.handleHeight});
    },
    
    greyOut:function(){
        this.scrollHandle.setStyles({'display':'none'});
        this.upBtn.setStyles({'opacity':this.options.disabledOpacity});
        this.scrollControlsYWrapper.setStyles({opacity:this.options.disabledOpacity});
        this.downBtn.setStyles({'opacity':this.options.disabledOpacity});
        this.scrollBar.setStyles({'opacity':this.options.disabledOpacity});				
        this.coverUp.setStyles({'display':'block','position':'absolute','background':'white','opacity':0.01,'right':'0','top':'0','width':'100%','height':this.scrollControlsYWrapper.getSize().y});
    },
    
    unGrey:function(){
        this.scrollHandle.setStyles({'display':'block','height':'auto'});
        this.scrollControlsYWrapper.setStyles({opacity:1});
        this.upBtn.setStyles({'opacity':1});
        this.downBtn.setStyles({'opacity':1});
        this.scrollBar.setStyles({'opacity':1});		
        this.coverUp.setStyles({'display':'none','width':0,	'height':0	});
        this.setHandleHeight();
    },
    
    loadContent:function(content){
        this.slider.set(0);
        this.paddingEl.empty().set('html',content);	
        this.refresh();
    },
    
    refresh:function(){
        var scrollPercent = Math.round(((100* this.step)/this.overHang));
        if(this.options.fullWindowMode){
            var windowSize = $(window).getSize();
            this.parentEl.setStyles({ width:'100%',height:'100%'});
        }
        this.overHang = this.paddingEl.getSize().y - this.parentEl.getSize().y   ;
        this.setHandleHeight();
        if(this.overHang <= 0){
            this.greyOut();
            return;
        }else{
            this.unGrey();
        }

        this.scrollHandle.removeEvents();		
        var newStep = Math.round((scrollPercent*this.overHang)/100);
        this.initSlider();
        this.slider.set(this.contentEl.getScroll().y);
        //this.slider.set(newStep);

        /*
        if(this.options.smoothMooScroll.toAnchor || this.options.smoothMooScroll.toMooScrollArea){				
            this.smoothMooScroll = new SmoothMooScroll({toAnchor:this.options.smoothMooScroll.toAnchor,toMooScrollArea:this.options.smoothMooScroll.toMooScrollArea},this.contentEl,this.windowFxScroll);
        }*/
    },
    
    setSlider:function(v){
        if(v =='top'){
            this.slider.set(0);
        }else if(v=='bottom'){
            this.slider.set('100%');
        }else{
            this.slider.set(v);
        }			
    }
 
 
});


var SmoothMooScroll = new Class({
    Extends: Fx.Scroll,
    initialize: function(options, context, windowFxScroll){
        this.setOptions(options);
        this.windowFxScroll = windowFxScroll;
        this.context = context;
        context = context || document;
        this.context = context;
        var doc = context.getDocument(), win = context.getWindow();		
        this.parent(context, options);
        
        this.links = (this.options.links) ? $$(this.options.links) : $$(doc.links);
        var location = win.location.href.match(/^[^#]*/)[0] + '#';
        this.links.each(function(link){
            if (link.href.indexOf(location) != 0) {	return;	}
            var anchor = link.href.substr(location.length);
            if (anchor && $(anchor) && $(anchor).getParents().contains($(this.context))) {
                this.useLink(link,anchor, true);
            }else if(anchor && $(anchor) && !this.inMooScrollArea($(anchor))){
                this.useLink(link,anchor, false);
            }
        }, this);
        if (!Browser.Engine.webkit419) this.addEvent('complete', function(){
            win.location.hash = this.anchor;
        }, true);
    },
    
    inMooScrollArea:function(el){
        return el.getParents().filter(function(item, index){return item.match('[rel=MooScrollArea]');}).length > 0;
    },
    
    putAnchorInAddressBar:function(anchor){
        window.location.href = "#" + anchor;      
    },

    useLink: function(link, anchor, inThisMooScrollArea){		
        link.removeEvents('click');
        link.addEvent('click', function(event){			
            if(!anchor || !$(anchor)){return;}			
            this.anchor = anchor;
            if (inThisMooScrollArea) {
                if(this.options.toMooScrollArea && this.options.toAnchor){
                    this.windowFxScroll.toElement(this.context.getParent()).chain(function(item, index){				
                        this.toElement(anchor).chain(function(){	this.putAnchorInAddressBar(anchor);	}.bind(this));				
                    }.bind(this));
                }else if(this.options.toMooScrollArea){
                    this.windowFxScroll.toElement(this.context.getParent()).chain(function(){	this.putAnchorInAddressBar(anchor);	}.bind(this));
                }else if(this.options.toAnchor){
                    this.toElement(anchor).chain(function(){	this.putAnchorInAddressBar(anchor);	}.bind(this));	
                }				
            }else{
                this.windowFxScroll.toElement(anchor).chain(function(){	this.putAnchorInAddressBar(anchor);	}.bind(this));     
            }
            event.stop();		
        }.bind(this));
    }

});

window.addEvent('domready', function() {

    $$('.scroll').each(function(obj) {        
        var container = document.createElement("div");
        container.style.overflow = 'hidden';
        container.style.marginRight = '12px';
        container.className = 'container';
        container.innerHTML = obj.innerHTML;

        obj.innerHTML = '';
        obj.appendChild(container);
    });
    
    var scroll_elements = new MooScroll();
});
