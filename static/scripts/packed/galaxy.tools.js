define(["libs/underscore","mvc/tools"],function(c,b){var a=function(g,f){$("input[name='"+g+"'][type='checkbox']").attr("checked",!!f)};$("div.checkUncheckAllPlaceholder").each(function(){var f=$(this).attr("checkbox_name");select_link=$("<a class='action-button'></a>").text("Select All").click(function(){a(f,true)});unselect_link=$("<a class='action-button'></a>").text("Unselect All").click(function(){a(f,false)});$(this).append(select_link).append(" ").append(unselect_link)});var e={select_single:{icon_class:"fa-file-o",select_by:"Run tool on single input",allow_remap:true},select_multiple:{icon_class:"fa-files-o",select_by:"Run tool in parallel across multiple datasets",allow_remap:false,min_option_count:2},select_collection:{icon_class:"fa-folder-o",select_by:"Run tool in parallel across dataset collection",allow_remap:false},multiselect_single:{icon_class:"fa-list-alt",select_by:"Run tool over multiple datasets",allow_remap:true},multiselect_collection:{icon_class:"fa-folder-o",select_by:"Run tool over dataset collection",allow_remap:false,},select_single_collection:{icon_class:"fa-file-o",select_by:"Run tool on single collection",allow_remap:true},select_map_over_collections:{icon_class:"fa-folder-o",select_by:"Map tool over compontents of nested collection",allow_remap:false,}};var d=Backbone.View.extend({initialize:function(l){var g=l.default_option;var m=null;var k=l.switch_options;this.switchOptions=k;this.prefix=l.prefix;var j=this.$el;var f=this;var h=0;var i=0;c.each(this.switchOptions,function(r,t){var n=c.size(r.options);var q=e[t];var p=h++;var s=false;if(g==t){m=p}else{if(n<(q.min_option_count||1)){s=true}}if(!s){i++;var o=$('<i class="fa '+q.icon_class+' runOptionIcon" style="padding-left: 5px; padding-right: 2px;"></i>').click(function(){f.enableSelectBy(p,t)}).attr("title",q.select_by);f.formRow().find("label").append(o)}});if(i<2){f.formRow().find("i.runOptionIcon").hide()}if(m!=null){f.enableSelectBy(m,g)}},formRow:function(){return this.$el.closest(".form-row")},render:function(){},enableSelectBy:function(k,j){var h=e[j];if(h.allow_remap){$("div#remap-row").css("display","none")}else{$("div#remap-row").css("display","inherit")}this.formRow().find("i").each(function(l,m){if(l==k){$(m).css("color","black")}else{$(m).css("color","Gray")}});var g=this.$("select");var f=this.switchOptions[j];g.attr("name",this.prefix+f.name);g.attr("multiple",f.multiple);var i=this.$(".select2-container").length>0;g.html("");c.each(f.options,function(m){var o=m[0];var n=m[1];var l=m[2];g.append($("<option />",{text:o,val:n,selected:l}))});if(i){g.select2()}}});return{SwitchSelectView:d}});