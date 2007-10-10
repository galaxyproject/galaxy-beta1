(function($) {
	
	//If the UI scope is not availalable, add it
	$.ui = $.ui || {};
	
	//Add methods that are vital for all mouse interaction stuff (plugin registering)
	$.extend($.ui, {
		plugin: {
			add: function(w, c, o, p) {
				var a = $.ui[w].prototype; if(!a.plugins[c]) a.plugins[c] = [];
				a.plugins[c].push([o,p]);
			},
			call: function(instance, name, arguments) {
				var c = instance.plugins[name]; if(!c) return;
				var o = instance.interaction ? instance.interaction.options : instance.options;
				var e = instance.interaction ? instance.interaction.element : instance.element;
				
				for (var i = 0; i < c.length; i++) {
					if (o[c[i][0]]) c[i][1].apply(e, arguments);
				}	
			}	
		}
	});
	
	$.fn.mouseInteractionDestroy = function() {
		this.each(function() {
			if($.data(this, "ui-mouse")) $.data(this, "ui-mouse").destroy(); 	
		});
	};
	
	$.ui.mouseInteraction = function(el,o) {
	
		if(!o) var o = {};
		this.element = el;
		$.data(this.element, "ui-mouse", this);
		
		this.options = {};
		$.extend(this.options, o);
		$.extend(this.options, {
			handle : o.handle ? ($(o.handle, el)[0] ? $(o.handle, el) : $(el)) : $(el),
			helper: o.helper || 'original',
			preventionDistance: o.preventionDistance || 0,
			dragPrevention: o.dragPrevention ? o.dragPrevention.toLowerCase().split(',') : ['input','textarea','button','select','option'],
			cursorAt: { top: ((o.cursorAt && o.cursorAt.top) ? o.cursorAt.top : 0), left: ((o.cursorAt && o.cursorAt.left) ? o.cursorAt.left : 0), bottom: ((o.cursorAt && o.cursorAt.bottom) ? o.cursorAt.bottom : 0), right: ((o.cursorAt && o.cursorAt.right) ? o.cursorAt.right : 0) },
			cursorAtIgnore: (!o.cursorAt) ? true : false, //Internal property
			appendTo: o.appendTo || 'parent'			
		});
		o = this.options; //Just Lazyness
		
		if(!this.options.nonDestructive && (o.helper == 'clone' || o.helper == 'original')) {

			// Let's save the margins for better reference
			o.margins = {
				top: parseInt($(el).css('marginTop')) || 0,
				left: parseInt($(el).css('marginLeft')) || 0,
				bottom: parseInt($(el).css('marginBottom')) || 0,
				right: parseInt($(el).css('marginRight')) || 0
			};

			// We have to add margins to our cursorAt
			if(o.cursorAt.top != 0) o.cursorAt.top = o.margins.top;
			if(o.cursorAt.left != 0) o.cursorAt.left += o.margins.left;
			if(o.cursorAt.bottom != 0) o.cursorAt.bottom += o.margins.bottom;
			if(o.cursorAt.right != 0) o.cursorAt.right += o.margins.right;
			
			
			if(o.helper == 'original')
				o.wasPositioned = $(el).css('position');
			
		} else {
			o.margins = { top: 0, left: 0, right: 0, bottom: 0 };
		}
		
		var self = this;
		this.mousedownfunc = function(e) { // Bind the mousedown event
			return self.click.apply(self, [e]);	
		};
		o.handle.bind('mousedown', this.mousedownfunc);
		
		//Prevent selection of text when starting the drag in IE
		if($.browser.msie) $(this.element).attr('unselectable', 'on');
		
	};
	
	$.extend($.ui.mouseInteraction.prototype, {
		plugins: {},
		currentTarget: null,
		lastTarget: null,
		timer: null,
		slowMode: false,
		init: false,
		destroy: function() {
			this.options.handle.unbind('mousedown', this.mousedownfunc);
		},
		trigger: function(e) {
			return this.click.apply(this, arguments);
		},
		click: function(e) {

			var o = this.options;
			
			window.focus();
			if(e.which != 1) return true; //only left click starts dragging
		
			// Prevent execution on defined elements
			var targetName = (e.target) ? e.target.nodeName.toLowerCase() : e.srcElement.nodeName.toLowerCase();
			for(var i=0;i<o.dragPrevention.length;i++) {
				if(targetName == o.dragPrevention[i]) return true;
			}

			//Prevent execution on condition
			if(o.startCondition && !o.startCondition.apply(this, [e])) return true;

			var self = this;
			this.mouseup = function(e) { return self.stop.apply(self, [e]); };
			this.mousemove = function(e) { return self.drag.apply(self, [e]); };

			var initFunc = function() { //This function get's called at bottom or after timeout
				$(document).bind('mouseup', self.mouseup);
				$(document).bind('mousemove', self.mousemove);
				self.opos = [e.pageX,e.pageY]; // Get the original mouse position
			};
			
			if(o.preventionTimeout) { //use prevention timeout
				if(this.timer) clearInterval(this.timer);
				this.timer = setTimeout(function() { initFunc(); }, o.preventionTimeout);
				return false;
			}
		
			initFunc();
			return false;
			
		},
		start: function(e) {
			
			var o = this.options; var a = this.element;
			o.co = $(a).offset(); //get the current offset
				
			this.helper = typeof o.helper == 'function' ? $(o.helper.apply(a, [e,this]))[0] : (o.helper == 'clone' ? $(a).clone()[0] : a);

			if(o.appendTo == 'parent') { // Let's see if we have a positioned parent
				var cp = a.parentNode;
				while (cp) {
					if(cp.style && ($(cp).css('position') == 'relative' || $(cp).css('position') == 'absolute')) {
						o.pp = cp;
						o.po = $(cp).offset();
						o.ppOverflow = !!($(o.pp).css('overflow') == 'auto' || $(o.pp).css('overflow') == 'scroll'); //TODO!
						break;	
					}
					cp = cp.parentNode ? cp.parentNode : null;
				};
				
				if(!o.pp) o.po = { top: 0, left: 0 };
			}
			
			this.pos = [this.opos[0],this.opos[1]]; //Use the relative position
			this.rpos = [this.pos[0],this.pos[1]]; //Save the absolute position
			
			if(o.cursorAtIgnore) { // If we want to pick the element where we clicked, we borrow cursorAt and add margins
				o.cursorAt.left = this.pos[0] - o.co.left + o.margins.left;
				o.cursorAt.top = this.pos[1] - o.co.top + o.margins.top;
			}



			if(o.pp) { // If we have a positioned parent, we pick the draggable relative to it
				this.pos[0] -= o.po.left;
				this.pos[1] -= o.po.top;
			}
			
			this.slowMode = (o.cursorAt && (o.cursorAt.top-o.margins.top > 0 || o.cursorAt.bottom-o.margins.bottom > 0) && (o.cursorAt.left-o.margins.left > 0 || o.cursorAt.right-o.margins.right > 0)) ? true : false; //If cursorAt is within the helper, set slowMode to true
			
			if(!o.nonDestructive) $(this.helper).css('position', 'absolute');
			if(o.helper != 'original') $(this.helper).appendTo((o.appendTo == 'parent' ? a.parentNode : o.appendTo)).show();

			// Remap right/bottom properties for cursorAt to left/top
			if(o.cursorAt.right && !o.cursorAt.left) o.cursorAt.left = this.helper.offsetWidth+o.margins.right+o.margins.left - o.cursorAt.right;
			if(o.cursorAt.bottom && !o.cursorAt.top) o.cursorAt.top = this.helper.offsetHeight+o.margins.top+o.margins.bottom - o.cursorAt.bottom;
		
			this.init = true;	

			if(o._start) o._start.apply(a, [this.helper, this.pos, o.cursorAt, this, e]); // Trigger the start callback
			this.helperSize = { width: outerWidth(this.helper), height: outerHeight(this.helper) }; //Set helper size property
			return false;
						
		},
		stop: function(e) {			
			
			var o = this.options; var a = this.element; var self = this;

			$(document).unbind('mouseup', self.mouseup);
			$(document).unbind('mousemove', self.mousemove);

			if(this.init == false) {
                // james@bx.psu.edu
                if ( o.click ) o.click.apply(); 
                this.opos = this.pos = null;
				return null;
			}
			if(o._beforeStop) o._beforeStop.apply(a, [this.helper, this.pos, o.cursorAt, this, e]);

			if(this.helper != a && !o.beQuietAtEnd) { // Remove helper, if it's not the original node
				$(this.helper).remove(); this.helper = null;
			}
			
			if(!o.beQuietAtEnd) {
				//if(o.wasPositioned)	$(a).css('position', o.wasPositioned);
				if(o._stop) o._stop.apply(a, [this.helper, this.pos, o.cursorAt, this, e]);
			}

			this.init = false;
			this.opos = this.pos = null;
			return false;
			
		},
		drag: function(e) {

			if (!this.opos || ($.browser.msie && !e.button)) return this.stop.apply(this, [e]); // check for IE mouseup when moving into the document again
			var o = this.options;
			
			this.pos = [e.pageX,e.pageY]; //relative mouse position
			if(this.rpos && this.rpos[0] == this.pos[0] && this.rpos[1] == this.pos[1]) return false;
			this.rpos = [this.pos[0],this.pos[1]]; //absolute mouse position
			
			if(o.pp) { //If we have a positioned parent, use a relative position
				this.pos[0] -= o.po.left;
				this.pos[1] -= o.po.top;	
			}
			
			if( (Math.abs(this.rpos[0]-this.opos[0]) > o.preventionDistance || Math.abs(this.rpos[1]-this.opos[1]) > o.preventionDistance) && this.init == false) //If position is more than x pixels from original position, start dragging
				this.start.apply(this,[e]);			
			else {
				if(this.init == false) return false;
			}
		
			if(o._drag) o._drag.apply(this.element, [this.helper, this.pos, o.cursorAt, this, e]);
			return false;
			
		}
	});

	var num = function(el, prop) {
		return parseInt($.css(el.jquery?el[0]:el,prop))||0;
	};
	function outerWidth(el) {
		var $el = $(el), ow = $el.width();
		for (var i = 0, props = ['borderLeftWidth', 'paddingLeft', 'paddingRight', 'borderRightWidth']; i < props.length; i++)
			ow += num($el, props[i]);
		return ow;
	};
	function outerHeight(el) {
		var $el = $(el), oh = $el.width();
		for (var i = 0, props = ['borderTopWidth', 'paddingTop', 'paddingBottom', 'borderBottomWidth']; i < props.length; i++)
			oh += num($el, props[i]);
		return oh;
	};

	//Make nodes selectable by expression
	$.extend($.expr[':'], { draggable: "(' '+a.className+' ').indexOf(' ui-draggable ')" });


	//Macros for external methods that support chaining
	var methods = "destroy,enable,disable".split(",");
	for(var i=0;i<methods.length;i++) {
		var cur = methods[i], f;
		eval('f = function() { var a = arguments; return this.each(function() { if(jQuery(this).is(".ui-draggable")) jQuery.data(this, "ui-draggable")["'+cur+'"](a); }); }');
		$.fn["draggable"+cur.substr(0,1).toUpperCase()+cur.substr(1)] = f;
	};
	
	//get instance method
	$.fn.draggableInstance = function() {
		if($(this[0]).is(".ui-draggable")) return $.data(this[0], "ui-draggable");
		return false;
	};

	$.fn.draggable = function(o) {
		return this.each(function() {
			if(!$(this).is(".ui-draggable")) new $.ui.draggable(this, o);
		});
	};
	
	$.ui.ddmanager = {
		current: null,
		droppables: [],
		prepareOffsets: function(t, e) {
			var dropTop = $.ui.ddmanager.dropTop = [];
			var dropLeft = $.ui.ddmanager.dropLeft;
			var m = $.ui.ddmanager.droppables;
			for (var i = 0; i < m.length; i++) {
				if(m[i].item.disabled) continue;
				m[i].offset = $(m[i].item.element).offset();
				if (t && m[i].item.options.accept(t.element)) //Activate the droppable if used directly from draggables
					m[i].item.activate.call(m[i].item, e);
			}
		},
		fire: function(oDrag, e) {
			
			var oDrops = $.ui.ddmanager.droppables;
			var oOvers = $.grep(oDrops, function(oDrop) {
				
				if (!oDrop.item.disabled && $.ui.intersect(oDrag, oDrop, oDrop.item.options.tolerance))
					oDrop.item.drop.call(oDrop.item, e);
			});
			$.each(oDrops, function(i, oDrop) {
				if (!oDrop.item.disabled && oDrop.item.options.accept(oDrag.element)) {
					oDrop.out = 1; oDrop.over = 0;
					oDrop.item.deactivate.call(oDrop.item, e);
				}
			});
		},
		update: function(oDrag, e) {
			
			if(oDrag.options.refreshPositions) $.ui.ddmanager.prepareOffsets();
			
			var oDrops = $.ui.ddmanager.droppables;
			var oOvers = $.grep(oDrops, function(oDrop) {
				if(oDrop.item.disabled) return false; 
				var isOver = $.ui.intersect(oDrag, oDrop, oDrop.item.options.tolerance);
				if (!isOver && oDrop.over == 1) {
					oDrop.out = 1; oDrop.over = 0;
					oDrop.item.out.call(oDrop.item, e);
				}
				return isOver;
			});
			$.each(oOvers, function(i, oOver) {
				if (oOver.over == 0) {
					oOver.out = 0; oOver.over = 1;
					oOver.item.over.call(oOver.item, e);
				}
			});
		}
	};
	
	$.ui.draggable = function(el, o) {
		
		var options = {};
		$.extend(options, o);
		var self = this;
		$.extend(options, {
			_start: function(h, p, c, t, e) {
				self.start.apply(t, [self, e]); // Trigger the start callback				
			},
			_beforeStop: function(h, p, c, t, e) {
				self.stop.apply(t, [self, e]); // Trigger the start callback
			},
			_drag: function(h, p, c, t, e) {
				self.drag.apply(t, [self, e]); // Trigger the start callback
			},
			startCondition: function(e) {
				return !(e.target.className.indexOf("ui-resizable-handle") != -1 || self.disabled);	
			}			
		});
		
		$.data(el, "ui-draggable", this);
		
		if (options.ghosting == true) options.helper = 'clone'; //legacy option check
		$(el).addClass("ui-draggable");
		this.interaction = new $.ui.mouseInteraction(el, options);
		
	};
	
	$.extend($.ui.draggable.prototype, {
		plugins: {},
		currentTarget: null,
		lastTarget: null,
		destroy: function() {
			$(this.interaction.element).removeClass("ui-draggable").removeClass("ui-draggable-disabled");
			this.interaction.destroy();
		},
		enable: function() {
			$(this.interaction.element).removeClass("ui-draggable-disabled");
			this.disabled = false;
		},
		disable: function() {
			$(this.interaction.element).addClass("ui-draggable-disabled");
			this.disabled = true;
		},
		prepareCallbackObj: function(self) {
			return {
				helper: self.helper,
				position: { left: self.pos[0], top: self.pos[1] },
				offset: self.options.cursorAt,
				draggable: self,
				options: self.options	
			}			
		},
		start: function(that, e) {
			
			var o = this.options;
			$.ui.ddmanager.current = this;
			
			$.ui.plugin.call(that, 'start', [e, that.prepareCallbackObj(this)]);
			$(this.element).triggerHandler("dragstart", [e, that.prepareCallbackObj(this)], o.start);
			
			if (this.slowMode && $.ui.droppable && !o.dropBehaviour)
				$.ui.ddmanager.prepareOffsets(this, e);
			
			return false;
						
		},
		stop: function(that, e) {			
			
			var o = this.options;
			
			$.ui.plugin.call(that, 'stop', [e, that.prepareCallbackObj(this)]);
			$(this.element).triggerHandler("dragstop", [e, that.prepareCallbackObj(this)], o.stop);

			if (this.slowMode && $.ui.droppable && !o.dropBehaviour) //If cursorAt is within the helper, we must use our drop manager
				$.ui.ddmanager.fire(this, e);

			$.ui.ddmanager.current = null;
			$.ui.ddmanager.last = this;

			return false;
			
		},
		drag: function(that, e) {

			var o = this.options;

			$.ui.ddmanager.update(this, e);

			this.pos = [this.pos[0]-o.cursorAt.left, this.pos[1]-o.cursorAt.top];

			$.ui.plugin.call(that, 'drag', [e, that.prepareCallbackObj(this)]);
			var nv = $(this.element).triggerHandler("drag", [e, that.prepareCallbackObj(this)], o.drag);

			var nl = (nv && nv.left) ? nv.left : this.pos[0];
			var nt = (nv && nv.top) ? nv.top : this.pos[1];
			
			$(this.helper).css('left', nl+'px').css('top', nt+'px'); // Stick the helper to the cursor
			return false;
			
		}
	});

	$.ui.plugin.add("draggable", "stop", "effect", function(e,ui) {
		var t = ui.helper;
		if(ui.options.effect[1]) {
			if(t != this) {
				ui.options.beQuietAtEnd = true;
				switch(ui.options.effect[1]) {
					case 'fade':
						$(t).fadeOut(300, function() { $(this).remove(); });
						break;
					default:
						$(t).remove();
						break;	
				}
			}
		}
	});
	
	$.ui.plugin.add("draggable", "start", "effect", function(e,ui) {
		if(ui.options.effect[0]) {
			switch(ui.options.effect[0]) {
				case 'fade':
					$(ui.helper).hide().fadeIn(300);
					break;
			}
		}
	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "start", "cursor", function(e,ui) {
		var t = $('body');
		if (t.css("cursor")) ui.options.ocursor = t.css("cursor");
		t.css("cursor", ui.options.cursor);
	});

	$.ui.plugin.add("draggable", "stop", "cursor", function(e,ui) {
		if (ui.options.ocursor) $('body').css("cursor", ui.options.ocursor);
	});

//----------------------------------------------------------------
	
	$.ui.plugin.add("draggable", "start", "zIndex", function(e,ui) {
		var t = $(ui.helper);
		if(t.css("zIndex")) ui.options.ozIndex = t.css("zIndex");
		t.css('zIndex', ui.options.zIndex);
	});
	
	$.ui.plugin.add("draggable", "stop", "zIndex", function(e,ui) {
		if(ui.options.ozIndex) $(ui.helper).css('zIndex', ui.options.ozIndex);
	});


//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "start", "opacity", function(e,ui) {
		var t = $(ui.helper);
		if(t.css("opacity")) ui.options.oopacity = t.css("opacity");
		t.css('opacity', ui.options.opacity);
	});
	
	$.ui.plugin.add("draggable", "stop", "opacity", function(e,ui) {
		if(ui.options.oopacity) $(ui.helper).css('opacity', ui.options.oopacity);
	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "stop", "revert", function(e,ui) {
	
		var o = ui.options;
		var rpos = { left: 0, top: 0 };
		o.beQuietAtEnd = true;

		if(ui.helper != this) {

			rpos = $(ui.draggable.sorthelper || this).offset({ border: false });

			var nl = rpos.left-o.po.left-o.margins.left;
			var nt = rpos.top-o.po.top-o.margins.top;

		} else {
			var nl = o.co.left - (o.po ? o.po.left : 0);
			var nt = o.co.top - (o.po ? o.po.top : 0);
		}
		
		var self = ui.draggable;

		$(ui.helper).animate({
			left: nl,
			top: nt
		}, 500, function() {
			
			if(o.wasPositioned) $(self.element).css('position', o.wasPositioned);
			if(o.stop) o.stop.apply(self.element, [self.helper, self.pos, [o.co.left - o.po.left,o.co.top - o.po.top],self]);
			
			if(self.helper != self.element) window.setTimeout(function() { $(self.helper).remove(); }, 0); //Using setTimeout because of strange flickering in Firefox
			
		});
		
	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "start", "iframeFix", function(e,ui) {

		var o = ui.options;
		if(!ui.draggable.slowMode) { // Make clones on top of iframes (only if we are not in slowMode)
			if(o.iframeFix.constructor == Array) {
				for(var i=0;i<o.iframeFix.length;i++) {
					var co = $(o.iframeFix[i]).offset({ border: false });
					$("<div class='DragDropIframeFix' style='background: #fff;'></div>").css("width", $(o.iframeFix[i])[0].offsetWidth+"px").css("height", $(o.iframeFix[i])[0].offsetHeight+"px").css("position", "absolute").css("opacity", "0.001").css("z-index", "1000").css("top", co.top+"px").css("left", co.left+"px").appendTo("body");
				}		
			} else {
				$("iframe").each(function() {					
					var co = $(this).offset({ border: false });
					$("<div class='DragDropIframeFix' style='background: #fff;'></div>").css("width", this.offsetWidth+"px").css("height", this.offsetHeight+"px").css("position", "absolute").css("opacity", "0.001").css("z-index", "1000").css("top", co.top+"px").css("left", co.left+"px").appendTo("body");
				});							
			}		
		}

	});
	
	$.ui.plugin.add("draggable","stop", "iframeFix", function(e,ui) {
		if(ui.options.iframeFix) $("div.DragDropIframeFix").each(function() { this.parentNode.removeChild(this); }); //Remove frame helpers	
	});
		
//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "start", "containment", function(e,ui) {

		var o = ui.options;

		if(!o.cursorAtIgnore || o.containment.left != undefined || o.containment.constructor == Array) return;
		if(o.containment == 'parent') o.containment = this.parentNode;


		if(o.containment == 'document') {
			o.containment = [
				0-o.margins.left,
				0-o.margins.top,
				$(document).width()-o.margins.right,
				($(document).height() || document.body.parentNode.scrollHeight)-o.margins.bottom
			];
		} else { //I'm a node, so compute top/left/right/bottom
			var ce = $(o.containment)[0];
			var co = $(o.containment).offset({ border: false });

			o.containment = [
				co.left-o.margins.left,
				co.top-o.margins.top,
				co.left+(ce.offsetWidth || ce.scrollWidth)-o.margins.right,
				co.top+(ce.offsetHeight || ce.scrollHeight)-o.margins.bottom
			];
		}

	});
	
	$.ui.plugin.add("draggable", "drag", "containment", function(e,ui) {
		
		var o = ui.options;
		if(!o.cursorAtIgnore) return;
			
		var h = $(ui.helper);
		var c = o.containment;
		if(c.constructor == Array) {
			
			if((ui.draggable.pos[0] < c[0]-o.po.left)) ui.draggable.pos[0] = c[0]-o.po.left;
			if((ui.draggable.pos[1] < c[1]-o.po.top)) ui.draggable.pos[1] = c[1]-o.po.top;
			if(ui.draggable.pos[0]+h[0].offsetWidth > c[2]-o.po.left) ui.draggable.pos[0] = c[2]-o.po.left-h[0].offsetWidth;
			if(ui.draggable.pos[1]+h[0].offsetHeight > c[3]-o.po.top) ui.draggable.pos[1] = c[3]-o.po.top-h[0].offsetHeight;
			
		} else {

			if(c.left && (ui.draggable.pos[0] < c.left)) ui.draggable.pos[0] = c.left;
			if(c.top && (ui.draggable.pos[1] < c.top)) ui.draggable.pos[1] = c.top;

			var p = $(o.pp);
			if(c.right && ui.draggable.pos[0]+h[0].offsetWidth > p[0].offsetWidth-c.right) ui.draggable.pos[0] = (p[0].offsetWidth-c.right)-h[0].offsetWidth;
			if(c.bottom && ui.draggable.pos[1]+h[0].offsetHeight > p[0].offsetHeight-c.bottom) ui.draggable.pos[1] = (p[0].offsetHeight-c.bottom)-h[0].offsetHeight;
			
		}

		
	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "drag", "grid", function(e,ui) {
		var o = ui.options;
		if(!o.cursorAtIgnore) return;
		ui.draggable.pos[0] = o.co.left + o.margins.left - o.po.left + Math.round((ui.draggable.pos[0] - o.co.left - o.margins.left + o.po.left) / o.grid[0]) * o.grid[0];
		ui.draggable.pos[1] = o.co.top + o.margins.top - o.po.top + Math.round((ui.draggable.pos[1] - o.co.top - o.margins.top + o.po.top) / o.grid[1]) * o.grid[1];
	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "drag", "axis", function(e,ui) {
		var o = ui.options;
		if(!o.cursorAtIgnore) return;
		if(o.constraint) o.axis = o.constraint; //Legacy check
		o.axis ? ( o.axis == 'x' ? ui.draggable.pos[1] = o.co.top - o.margins.top - o.po.top : ui.draggable.pos[0] = o.co.left - o.margins.left - o.po.left ) : null;
	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "drag", "scroll", function(e,ui) {

		var o = ui.options;
		o.scrollSensitivity	= o.scrollSensitivity || 20;
		o.scrollSpeed		= o.scrollSpeed || 20;

		if(o.pp && o.ppOverflow) { // If we have a positioned parent, we only scroll in this one
			// TODO: Extremely strange issues are waiting here..handle with care
		} else {
			if((ui.draggable.rpos[1] - $(window).height()) - $(document).scrollTop() > -o.scrollSensitivity) window.scrollBy(0,o.scrollSpeed);
			if(ui.draggable.rpos[1] - $(document).scrollTop() < o.scrollSensitivity) window.scrollBy(0,-o.scrollSpeed);
			if((ui.draggable.rpos[0] - $(window).width()) - $(document).scrollLeft() > -o.scrollSensitivity) window.scrollBy(o.scrollSpeed,0);
			if(ui.draggable.rpos[0] - $(document).scrollLeft() < o.scrollSensitivity) window.scrollBy(-o.scrollSpeed,0);
		}

	});

//----------------------------------------------------------------

	$.ui.plugin.add("draggable", "drag", "wrapHelper", function(e,ui) {

		var o = ui.options;
		if(o.cursorAtIgnore) return;
		var t = ui.helper;

		if(!o.pp || !o.ppOverflow) {
			var wx = $(window).width() - ($.browser.mozilla ? 20 : 0);
			var sx = $(document).scrollLeft();
			
			var wy = $(window).height();
			var sy = $(document).scrollTop();	
		} else {
			var wx = o.pp.offsetWidth + o.po.left - 20;
			var sx = o.pp.scrollLeft;
			
			var wy = o.pp.offsetHeight + o.po.top - 20;
			var sy = o.pp.scrollTop;						
		}

		ui.draggable.pos[0] -= ((ui.draggable.rpos[0]-o.cursorAt.left - wx + t.offsetWidth+o.margins.right) - sx > 0 || (ui.draggable.rpos[0]-o.cursorAt.left+o.margins.left) - sx < 0) ? (t.offsetWidth+o.margins.left+o.margins.right - o.cursorAt.left * 2) : 0;
		
		ui.draggable.pos[1] -= ((ui.draggable.rpos[1]-o.cursorAt.top - wy + t.offsetHeight+o.margins.bottom) - sy > 0 || (ui.draggable.rpos[1]-o.cursorAt.top+o.margins.top) - sy < 0) ? (t.offsetHeight+o.margins.top+o.margins.bottom - o.cursorAt.top * 2) : 0;

	});

	//Make nodes selectable by expression
	$.extend($.expr[':'], { droppable: "(' '+a.className+' ').indexOf(' ui-droppable ')" });

	//Macros for external methods that support chaining
	var methods = "destroy,enable,disable".split(",");
	for(var i=0;i<methods.length;i++) {
		var cur = methods[i], f;
		eval('f = function() { var a = arguments; return this.each(function() { if(jQuery(this).is(".ui-droppable")) jQuery.data(this, "ui-droppable")["'+cur+'"](a); }); }');
		$.fn["droppable"+cur.substr(0,1).toUpperCase()+cur.substr(1)] = f;
	};
	
	//get instance method
	$.fn.droppableInstance = function() {
		if($(this[0]).is(".ui-droppable")) return $.data(this[0], "ui-droppable");
		return false;
	};

	$.fn.droppable = function(o) {
		return this.each(function() {
			new $.ui.droppable(this,o);
		});
	};
	
	$.ui.droppable = function(el,o) {

		if(!o) var o = {};			
		this.element = el; if($.browser.msie) el.droppable = 1;
		$.data(el, "ui-droppable", this);
		
		this.options = {};
		$.extend(this.options, o);
		
		var accept = o.accept;
		$.extend(this.options, {
			accept: o.accept && o.accept.constructor == Function ? o.accept : function(d) {
				return $(d).is(accept);	
			},
			tolerance: o.tolerance || 'intersect'
		});
		o = this.options;
		var self = this;
		
		this.mouseBindings = [function(e) { return self.move.apply(self, [e]); },function(e) { return self.drop.apply(self, [e]); }];
		$(this.element).bind("mousemove", this.mouseBindings[0]);
		$(this.element).bind("mouseup", this.mouseBindings[1]);
		
		$.ui.ddmanager.droppables.push({ item: this, over: 0, out: 1 }); // Add the reference and positions to the manager
		$(this.element).addClass("ui-droppable");
			
	};
	
	$.extend($.ui.droppable.prototype, {
		plugins: {},
		prepareCallbackObj: function(c) {
			return {
				draggable: c,
				droppable: this,
				element: c.element,
				helper: c.helper,
				options: this.options	
			}			
		},
		destroy: function() {
			$(this.element).removeClass("ui-droppable").removeClass("ui-droppable-disabled");
			$(this.element).unbind("mousemove", this.mouseBindings[0]);
			$(this.element).unbind("mouseup", this.mouseBindings[1]);
			
			for(var i=0;i<$.ui.ddmanager.droppables.length;i++) {
				if($.ui.ddmanager.droppables[i].item == this) $.ui.ddmanager.droppables.splice(i,1);
			}
		},
		enable: function() {
			$(this.element).removeClass("ui-droppable-disabled");
			this.disabled = false;
		},
		disable: function() {
			$(this.element).addClass("ui-droppable-disabled");
			this.disabled = true;
		},
		move: function(e) {

			if(!$.ui.ddmanager.current) return;

			var o = this.options;
			var c = $.ui.ddmanager.current;
			
			/* Save current target, if no last target given */
			var findCurrentTarget = function(e) {
				if(e.currentTarget) return e.currentTarget;
				var el = e.srcElement; 
				do { if(el.droppable) return el; el = el.parentNode; } while (el); //This is only used in IE! references in DOM are evil!
			};
			if(c && o.accept(c.element)) c.currentTarget = findCurrentTarget(e);
			
			c.drag.apply(c, [e]);
			e.stopPropagation ? e.stopPropagation() : e.cancelBubble = true;
			
		},
		over: function(e) {

			var c = $.ui.ddmanager.current;
			if (!c || c.element == this.element) return; // Bail if draggable and droppable are same element
			
			var o = this.options;
			if (o.accept(c.element)) {
				$.ui.plugin.call(this, 'over', [e, this.prepareCallbackObj(c)]);
				$(this.element).triggerHandler("dropover", [e, this.prepareCallbackObj(c)], o.over);
			}
			
		},
		out: function(e) {

			var c = $.ui.ddmanager.current;
			if (!c || c.element == this.element) return; // Bail if draggable and droppable are same element

			var o = this.options;
			if (o.accept(c.element)) {
				$.ui.plugin.call(this, 'out', [e, this.prepareCallbackObj(c)]);
				$(this.element).triggerHandler("dropout", [e, this.prepareCallbackObj(c)], o.out);
			}
			
		},
		drop: function(e) {

			var c = $.ui.ddmanager.current;
			if (!c || c.element == this.element) return; // Bail if draggable and droppable are same element
			
			var o = this.options;
			if(o.accept(c.element)) { // Fire callback
				if(o.greedy && !c.slowMode) {
					if(c.currentTarget == this.element) {
						$.ui.plugin.call(this, 'drop', [e, {
							draggable: c,
							droppable: this,
							element: c.element,
							helper: c.helper	
						}]);
						$(this.element).triggerHandler("drop", [e, {
							draggable: c,
							droppable: this,
							element: c.element,
							helper: c.helper	
						}], o.drop);
					}
				} else {
					$.ui.plugin.call(this, 'drop', [e, this.prepareCallbackObj(c)]);
					$(this.element).triggerHandler("drop", [e, this.prepareCallbackObj(c)], o.drop);
				}
			}
			
		},
		activate: function(e) {
			var c = $.ui.ddmanager.current;
			$.ui.plugin.call(this, 'activate', [e, this.prepareCallbackObj(c)]);
			if(c) $(this.element).triggerHandler("dropactivate", [e, this.prepareCallbackObj(c)], this.options.activate);	
		},
		deactivate: function(e) {
			var c = $.ui.ddmanager.current;
			$.ui.plugin.call(this, 'deactivate', [e, this.prepareCallbackObj(c)]);
			if(c) $(this.element).triggerHandler("dropdeactivate", [e, this.prepareCallbackObj(c)], this.options.deactivate);
		}
	});
	
	$.ui.intersect = function(oDrag, oDrop, toleranceMode) {
		if (!oDrop.offset)
			return false;
		var x1 = oDrag.rpos[0] - oDrag.options.cursorAt.left + oDrag.options.margins.left, x2 = x1 + oDrag.helperSize.width,
		    y1 = oDrag.rpos[1] - oDrag.options.cursorAt.top + oDrag.options.margins.top, y2 = y1 + oDrag.helperSize.height;
		var l = oDrop.offset.left, r = l + oDrop.item.element.offsetWidth, 
		    t = oDrop.offset.top,  b = t + oDrop.item.element.offsetHeight;
		switch (toleranceMode) {
			case 'fit':
				return (   l < x1 && x2 < r
					&& t < y1 && y2 < b);
				break;
			case 'intersect':
				return (   l < x1 + (oDrag.helperSize.width  / 2)        // Right Half
					&&     x2 - (oDrag.helperSize.width  / 2) < r    // Left Half
					&& t < y1 + (oDrag.helperSize.height / 2)        // Bottom Half
					&&     y2 - (oDrag.helperSize.height / 2) < b ); // Top Half
				break;
			case 'pointer':
				return (   l < oDrag.rpos[0] && oDrag.rpos[0] < r
					&& t < oDrag.rpos[1] && oDrag.rpos[1] < b);
				break;
			case 'touch':
				return (   (l < x1 && x1 < r && t < y1 && y1 < b)    // Top-Left Corner
					|| (l < x1 && x1 < r && t < y2 && y2 < b)    // Bottom-Left Corner
					|| (l < x2 && x2 < r && t < y1 && y1 < b)    // Top-Right Corner
					|| (l < x2 && x2 < r && t < y2 && y2 < b) ); // Bottom-Right Corner
				break;
			default:
				return false;
				break;
		}
	};
	
	// options.activeClass
	$.ui.plugin.add("droppable", "activate", "activeClass", function(e,ui) {
		$(this).addClass(ui.options.activeClass);
	});
	$.ui.plugin.add("droppable", "deactivate", "activeClass", function(e,ui) {
		$(this).removeClass(ui.options.activeClass);
	});
	$.ui.plugin.add("droppable", "drop", "activeClass", function(e,ui) {
		$(this).removeClass(ui.options.activeClass);
	});

	// options.hoverClass
	$.ui.plugin.add("droppable", "over", "hoverClass", function(e,ui) {
		$(this).addClass(ui.options.hoverClass);
	});
	$.ui.plugin.add("droppable", "out", "hoverClass", function(e,ui) {
		$(this).removeClass(ui.options.hoverClass);
	});
	$.ui.plugin.add("droppable", "drop", "hoverClass", function(e,ui) {
		$(this).removeClass(ui.options.hoverClass);
	});

})(jQuery);
