$(document).ready(function(){replace_big_select_inputs()});$.fn.makeAbsolute=function(a){return this.each(function(){var b=$(this);var c=b.position();b.css({position:"absolute",marginLeft:0,marginTop:0,top:c.top,left:c.left,right:$(window).width()-(c.left+b.width())});if(a){b.remove().appendTo("body")}})};function ensure_popup_helper(){if($("#popup-helper").length===0){$("<div id='popup-helper'/>").css({background:"white",opacity:0,zIndex:15000,position:"absolute",top:0,left:0,width:"100%",height:"100%"}).appendTo("body").hide()}}function attach_popupmenu(b,d){var a=function(){d.unbind().hide();$("#popup-helper").unbind("click.popupmenu").hide()};var c=function(g){$("#popup-helper").bind("click.popupmenu",a).show();d.click(a).css({left:0,top:-1000}).show();var f=g.pageX-d.width()/2;f=Math.min(f,$(document).scrollLeft()+$(window).width()-$(d).width()-20);f=Math.max(f,$(document).scrollLeft()+20);d.css({top:g.pageY-5,left:f});return false};$(b).click(c)}function make_popupmenu(c,b){ensure_popup_helper();var a=$("<ul id='"+c.attr("id")+"-menu'></ul>");$.each(b,function(f,e){if(e){$("<li/>").html(f).click(e).appendTo(a)}else{$("<li class='head'/>").html(f).appendTo(a)}});var d=$("<div class='popmenu-wrapper'>");d.append(a).append("<div class='overlay-border'>").css("position","absolute").appendTo("body").hide();attach_popupmenu(c,d)}function make_popup_menus(){jQuery("div[popupmenu]").each(function(){var c={};$(this).find("a").each(function(){var b=$(this).attr("confirm"),d=$(this).attr("href"),e=$(this).attr("target");c[$(this).text()]=function(){if(!b||confirm(b)){var g=window;if(e=="_parent"){g=window.parent}else{if(e=="_top"){g=window.top}}g.location=d}}});var a=$("#"+$(this).attr("popupmenu"));make_popupmenu(a,c);$(this).remove();a.addClass("popup").show()})}function array_length(b){if(b.length){return b.length}var c=0;for(var a in b){c++}return c}function naturalSort(i,g){var n=/(-?[0-9\.]+)/g,j=i.toString().toLowerCase()||"",f=g.toString().toLowerCase()||"",k=String.fromCharCode(0),l=j.replace(n,k+"$1"+k).split(k),e=f.replace(n,k+"$1"+k).split(k),d=(new Date(j)).getTime(),m=d?(new Date(f)).getTime():null;if(m){if(d<m){return -1}else{if(d>m){return 1}}}for(var h=0,c=Math.max(l.length,e.length);h<c;h++){oFxNcL=parseFloat(l[h])||l[h];oFyNcL=parseFloat(e[h])||e[h];if(oFxNcL<oFyNcL){return -1}else{if(oFxNcL>oFyNcL){return 1}}}return 0}function replace_big_select_inputs(a){if(typeof jQuery().autocomplete=="undefined"){return}if(a===undefined){a=20}$("select").each(function(){var d=$(this);if(d.find("option").length<a){return}if(d.attr("multiple")==true){return}var j=d.attr("value");var b=$("<input type='text' class='text-and-autocomplete-select'></input>");b.attr("size",40);b.attr("name",d.attr("name"));b.attr("id",d.attr("id"));b.click(function(){var k=$(this).attr("value");$(this).attr("value","Loading...");$(this).showAllInCache();$(this).attr("value",k);$(this).select()});var e=[];var g={};d.children("option").each(function(){var l=$(this).text();var k=$(this).attr("value");e.push(l);g[l]=k;g[k]=k;if(k==j){b.attr("value",l)}});if(j==""||j=="?"){b.attr("value","Click to Search or Select")}if(d.attr("name")=="dbkey"){e=e.sort(naturalSort)}var f={selectFirst:false,autoFill:false,mustMatch:false,matchContains:true,max:1000,minChars:0,hideForLessThanMinChars:false};b.autocomplete(e,f);d.replaceWith(b);var i=function(){var l=b.attr("value");var k=g[l];if(k!==null&&k!==undefined){b.attr("value",k)}else{if(j!=""){b.attr("value",j)}else{b.attr("value","?")}}};b.parents("form").submit(function(){i()});$(document).bind("convert_dbkeys",function(){i()});if(d.attr("refresh_on_change")=="true"){var c=d.attr("refresh_on_change_values");if(c!==undefined){c=c.split(",")}var h=function(){var m=b.attr("value");var l=g[m];if(l!==null&&l!==undefined){refresh=false;if(c!==undefined){for(var k=0;k<c.length;k++){if(l==c[k]){refresh=true;break}}}else{refresh=true}if(refresh){b.attr("value",l);b.parents("form").submit()}}};b.bind("result",h);b.keyup(function(k){h()})}})}function async_save_text(d,f,e,a,c,h,i,g,b){if(c===undefined){c=30}if(i===undefined){i=4}$("#"+d).live("click",function(){if($("#renaming-active").length>0){return}var l=$("#"+f),k=l.text(),j;if(h){j=$("<textarea></textarea>").attr({rows:i,cols:c}).text(k)}else{j=$("<input type='text'></input>").attr({value:k,size:c})}j.attr("id","renaming-active");j.blur(function(){$(this).remove();l.show();if(b){b(j)}});j.keyup(function(n){if(n.keyCode===27){$(this).trigger("blur")}else{if(n.keyCode===13){var m={};m[a]=$(this).val();$(this).trigger("blur");$.ajax({url:e,data:m,error:function(){alert("Text editing for elt "+f+" failed")},success:function(o){l.text(o);if(b){b(j)}}})}}});if(g){g(j)}l.hide();j.insertAfter(l);j.focus();j.select();return})}function init_history_items(d,a,c){var b=function(){try{var e=$.jStore.store("history_expand_state");if(e){for(var g in e){$("#"+g+" div.historyItemBody").show()}}}catch(f){$.jStore.remove("history_expand_state")}if($.browser.mozilla){$("div.historyItemBody").each(function(){if(!$(this).is(":visible")){$(this).find("pre.peek").css("overflow","hidden")}})}d.each(function(){var j=this.id;var h=$(this).children("div.historyItemBody");var i=h.find("pre.peek");$(this).find(".historyItemTitleBar > .historyItemTitle").wrap("<a href='javascript:void(0);'></a>").click(function(){if(h.is(":visible")){if($.browser.mozilla){i.css("overflow","hidden")}h.slideUp("fast");if(!c){var k=$.jStore.store("history_expand_state");if(k){delete k[j];$.jStore.store("history_expand_state",k)}}}else{h.slideDown("fast",function(){if($.browser.mozilla){i.css("overflow","auto")}});if(!c){var k=$.jStore.store("history_expand_state");if(k===undefined){k={}}k[j]=true;$.jStore.store("history_expand_state",k)}}return false})});$("#top-links > a.toggle").click(function(){var h=$.jStore.store("history_expand_state");if(h===undefined){h={}}$("div.historyItemBody:visible").each(function(){if($.browser.mozilla){$(this).find("pre.peek").css("overflow","hidden")}$(this).slideUp("fast");if(h){delete h[$(this).parent().attr("id")]}});$.jStore.store("history_expand_state",h)}).show()};if(a){b()}else{$.jStore.init("galaxy");$.jStore.engineReady(function(){b()})}}function commatize(b){b+="";var a=/(\d+)(\d{3})/;while(a.test(b)){b=b.replace(a,"$1,$2")}return b}$(document).ready(function(){$("a[confirm]").click(function(){return confirm($(this).attr("confirm"))});if($.fn.tipsy){$(".tooltip").tipsy({gravity:"s"})}make_popup_menus()});