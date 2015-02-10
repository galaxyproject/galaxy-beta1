define(["utils/utils","mvc/ui/ui-button-check"],function(c,e){var b=Backbone.View.extend({initialize:function(i){this.optionsDefault={visible:true,data:[],id:c.uuid(),error_text:"No data available.",wait_text:"Please wait...",multiple:false};this.options=c.merge(i,this.optionsDefault);this.setElement('<div class="ui-options"/>');this.$message=$("<div/>");this.$options=$(this._template(i));this.$menu=$('<div class="ui-options-menu"/>');this.$el.append(this.$message);this.$el.append(this.$menu);this.$el.append(this.$options);if(this.options.multiple){this.select_button=new e({onclick:function(){h.$("input").prop("checked",h.select_button.value()!==0);h._change()}});this.$menu.addClass("ui-margin-bottom");this.$menu.append(this.select_button.$el);this.$menu.append("Select/Unselect all")}if(!this.options.visible){this.$el.hide()}this.update(this.options.data);if(this.options.value!==undefined){this.value(this.options.value)}var h=this;this.on("change",function(){h._change()})},update:function(i){var l=this._getValue();this.$options.empty();if(this._templateOptions){this.$options.append(this._templateOptions(i))}else{for(var j in i){var k=$(this._templateOption(i[j]));k.addClass("ui-option");k.tooltip({title:i[j].tooltip,placement:"bottom"});this.$options.append(k)}}var h=this;this.$("input").on("change",function(){h.value(h._getValue());h._change()});this.value(l)},value:function(j){if(j!==undefined){if(!(j instanceof Array)){j=[j]}this.$("input").prop("checked",false);for(var h in j){this.$('input[value="'+j[h]+'"]').first().prop("checked",true)}}this._refresh();return this._getValue()},exists:function(j){if(j!==undefined){if(!(j instanceof Array)){j=[j]}for(var h in j){if(this.$('input[value="'+j[h]+'"]').length>0){return true}}}return false},first:function(){var h=this.$("input");if(h.length>0){return h.val()}else{return undefined}},validate:function(){return c.validate(this.value())},wait:function(){if(this._size()==0){this._messageShow(this.options.wait_text,"info");this.$options.hide();this.$menu.hide()}},unwait:function(){this._refresh()},_change:function(){if(this.options.onchange){this.options.onchange(this._getValue())}},_refresh:function(){if(this._size()==0){this._messageShow(this.options.error_text,"danger");this.$options.hide();this.$menu.hide()}else{this._messageHide();this.$options.css("display","inline-block");this.$menu.show()}if(this.select_button){var h=this._size();var i=this._getValue();if(!(i instanceof Array)){this.select_button.value(0)}else{if(i.length!==h){this.select_button.value(1)}else{this.select_button.value(2)}}}},_getValue:function(){var i=this.$(":checked");if(i.length==0){return"__null__"}if(this.options.multiple){var h=[];i.each(function(){h.push($(this).val())});return h}else{return i.val()}},_size:function(){return this.$(".ui-option").length},_messageShow:function(i,h){this.$message.show();this.$message.removeClass();this.$message.addClass("ui-message alert alert-"+h);this.$message.html(i)},_messageHide:function(){this.$message.hide()},_template:function(){return'<div class="ui-options-list"/>'}});var a=b.extend({_templateOption:function(h){var i=c.uuid();return'<div class="ui-option"><input id="'+i+'" type="'+this.options.type+'" name="'+this.options.id+'" value="'+h.value+'"/><label class="ui-options-label" for="'+i+'">'+h.label+"</label></div>"}});var f={};f.View=a.extend({initialize:function(h){h.type="radio";a.prototype.initialize.call(this,h)}});var d={};d.View=a.extend({initialize:function(h){h.multiple=true;h.type="checkbox";a.prototype.initialize.call(this,h)}});var g={};g.View=b.extend({initialize:function(h){b.prototype.initialize.call(this,h)},value:function(h){if(h!==undefined){this.$("input").prop("checked",false);this.$("label").removeClass("active");this.$('[value="'+h+'"]').prop("checked",true).closest("label").addClass("active")}return this._getValue()},_templateOption:function(j){var h="fa "+j.icon;if(!j.label){h+=" no-padding"}var i='<label class="btn btn-default">';if(j.icon){i+='<i class="'+h+'"/>'}i+='<input type="radio" name="'+this.options.id+'" value="'+j.value+'"/>';if(j.label){i+=j.label}i+="</label>";return i},_template:function(){return'<div class="btn-group ui-radiobutton" data-toggle="buttons"/>'}});return{Base:b,BaseIcons:a,Radio:f,RadioButton:g,Checkbox:d}});