define(["libs/underscore"],function(m){function n(r,q){for(var o in r){var p=r[o];if(p&&typeof(p)=="object"){q(p);n(p,q)}}}function d(o){return $("<div/>").text(o).html()}function l(p){if(!(p instanceof Array)){p=[p]}for(var o in p){if(["None",null,"null",undefined,"undefined"].indexOf(p[o])>-1){return false}}return true}function h(o){var o=o.toString();if(o){o=o.replace(/,/g,", ");var p=o.lastIndexOf(", ");if(p!=-1){o=o.substr(0,p)+" or "+o.substr(p+1)}return o}return""}function e(o){top.__utils__get__=top.__utils__get__||{};if(o.cache&&top.__utils__get__[o.url]){o.success&&o.success(top.__utils__get__[o.url]);console.debug("utils.js::get() - Fetching from cache ["+o.url+"].")}else{i({url:o.url,data:o.data,success:function(p){top.__utils__get__[o.url]=p;o.success&&o.success(p)},error:function(p){o.error&&o.error(p)}})}}function i(p){$.ajaxSetup({traditional:true});var o={contentType:"application/json",type:p.type||"GET",data:p.data||{},url:p.url};if(o.type=="GET"||o.type=="DELETE"){if(o.url.indexOf("?")==-1){o.url+="?"}else{o.url+="&"}o.url=o.url+$.param(o.data);o.data=null}else{o.dataType="json";o.url=o.url;o.data=JSON.stringify(o.data)}$.ajax(o).done(function(q){if(typeof q==="string"){try{q=q.replace("Infinity,",'"Infinity",');q=jQuery.parseJSON(q)}catch(r){console.debug(r)}}p.success&&p.success(q)}).fail(function(r){var q=null;try{q=jQuery.parseJSON(r.responseText)}catch(s){q=r.responseText}p.error&&p.error(q,r)})}function j(r,o){var p=$('<div class="'+r+'"></div>');p.appendTo(":eq(0)");var q=p.css(o);p.remove();return q}function g(o){if(!$('link[href^="'+o+'"]').length){$('<link href="'+galaxy_config.root+o+'" rel="stylesheet">').appendTo("head")}}function k(o,p){if(o){return m.defaults(o,p)}else{return p}}function b(p,r){var q="";if(p>=100000000000){p=p/100000000000;q="TB"}else{if(p>=100000000){p=p/100000000;q="GB"}else{if(p>=100000){p=p/100000;q="MB"}else{if(p>=100){p=p/100;q="KB"}else{if(p>0){p=p*10;q="b"}else{return"<strong>-</strong>"}}}}}var o=(Math.round(p)/10);if(r){return o+" "+q}else{return"<strong>"+o+"</strong> "+q}}function a(){return"x"+Math.random().toString(36).substring(2,9)}function c(o){var p=$("<p></p>");p.append(o);return p}function f(){var q=new Date();var o=(q.getHours()<10?"0":"")+q.getHours();var p=(q.getMinutes()<10?"0":"")+q.getMinutes();var r=q.getDate()+"/"+(q.getMonth()+1)+"/"+q.getFullYear()+", "+o+":"+p;return r}return{cssLoadFile:g,cssGetAttribute:j,get:e,merge:k,bytesToString:b,uuid:a,time:f,wrap:c,request:i,sanitize:d,textify:h,validate:l,deepeach:n}});