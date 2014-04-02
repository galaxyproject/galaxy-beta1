define(["utils/utils","libs/underscore","libs/d3","viz/visualization","utils/config"],function(h,i,n,k,c){h.cssLoadFile("static/style/circster.css");var o=Backbone.Model.extend({is_visible:function(s,p){var q=s.getBoundingClientRect(),r=$("svg")[0].getBoundingClientRect();if(q.right<0||q.left>r.right||q.bottom<0||q.top>r.bottom){return false}return true}});var j={drawTicks:function(t,s,x,r,p){var w=t.append("g").selectAll("g").data(s).enter().append("g").selectAll("g").data(x).enter().append("g").attr("class","tick").attr("transform",function(y){return"rotate("+(y.angle*180/Math.PI-90)+")translate("+y.radius+",0)"});var v=[],u=[],q=function(y){return y.angle>Math.PI?"end":null};if(p){v=[0,0,0,-4];u=[4,0,"",".35em"];q=null}else{v=[1,0,4,0];u=[0,4,".35em",""]}w.append("line").attr("x1",v[0]).attr("y1",v[1]).attr("x2",v[2]).attr("y1",v[3]).style("stroke","#000");w.append("text").attr("x",u[0]).attr("y",u[1]).attr("dx",u[2]).attr("dy",u[3]).attr("text-anchor",q).attr("transform",r).text(function(y){return y.label})},formatNum:function(q,p){if(p===undefined){p=2}if(q===null){return null}var s=null;if(Math.abs(q)<1){s=q.toPrecision(p)}else{var r=Math.round(q.toPrecision(p));q=Math.abs(q);if(q<1000){s=r}else{if(q<1000000){s=Math.round((r/1000).toPrecision(3)).toFixed(0)+"K"}else{if(q<1000000000){s=Math.round((r/1000000).toPrecision(3)).toFixed(0)+"M"}}}}return s}};var d=Backbone.Model.extend({});var a=Backbone.View.extend({className:"circster",initialize:function(p){this.genome=p.genome;this.label_arc_height=50;this.scale=1;this.circular_views=null;this.chords_views=null;this.model.get("drawables").on("add",this.add_track,this);this.model.get("drawables").on("remove",this.remove_track,this);var q=this.model.get("config");q.get("arc_dataset_height").on("change:value",this.update_track_bounds,this);q.get("track_gap").on("change:value",this.update_track_bounds,this)},get_circular_tracks:function(){return this.model.get("drawables").filter(function(p){return p.get("track_type")!=="DiagonalHeatmapTrack"})},get_chord_tracks:function(){return this.model.get("drawables").filter(function(p){return p.get("track_type")==="DiagonalHeatmapTrack"})},get_tracks_bounds:function(){var r=this.get_circular_tracks(),t=this.model.get("config").get_value("arc_dataset_height"),s=this.model.get("config").get_value("track_gap"),p=Math.min(this.$el.width(),this.$el.height())-20,v=p/2-r.length*(t+s)+s-this.label_arc_height,u=n.range(v,p/2,t+s);var q=this;return i.map(u,function(w){return[w,w+t]})},render:function(){var y=this,p=y.$el.width(),x=y.$el.height(),u=this.get_circular_tracks(),s=this.get_chord_tracks(),r=y.model.get("config").get_value("total_gap"),t=this.get_tracks_bounds(),q=n.select(y.$el[0]).append("svg").attr("width",p).attr("height",x).attr("pointer-events","all").append("svg:g").call(n.behavior.zoom().on("zoom",function(){var z=n.event.scale;q.attr("transform","translate("+n.event.translate+") scale("+z+")");if(y.scale!==z){if(y.zoom_drag_timeout){clearTimeout(y.zoom_drag_timeout)}y.zoom_drag_timeout=setTimeout(function(){},400)}})).attr("transform","translate("+p/2+","+x/2+")").append("svg:g").attr("class","tracks");this.circular_views=u.map(function(A,B){var z=new e({el:q.append("g")[0],track:A,radius_bounds:t[B],genome:y.genome,total_gap:r});z.render();return z});this.chords_views=s.map(function(A){var z=new l({el:q.append("g")[0],track:A,radius_bounds:t[0],genome:y.genome,total_gap:r});z.render();return z});var w=this.circular_views[this.circular_views.length-1].radius_bounds[1],v=[w,w+this.label_arc_height];this.label_track_view=new b({el:q.append("g")[0],track:new d(),radius_bounds:v,genome:y.genome,total_gap:r});this.label_track_view.render()},add_track:function(v){var q=this.model.get("config").get_value("total_gap");if(v.get("track_type")==="DiagonalHeatmapTrack"){var r=this.circular_views[0].radius_bounds,u=new l({el:n.select("g.tracks").append("g")[0],track:v,radius_bounds:r,genome:this.genome,total_gap:q});u.render();this.chords_views.push(u)}else{var t=this.get_tracks_bounds();i.each(this.circular_views,function(w,x){w.update_radius_bounds(t[x])});i.each(this.chords_views,function(w){w.update_radius_bounds(t[0])});var s=this.circular_views.length,p=new e({el:n.select("g.tracks").append("g")[0],track:v,radius_bounds:t[s],genome:this.genome,total_gap:q});p.render();this.circular_views.push(p)}},remove_track:function(q,s,r){var p=this.circular_views[r.index];this.circular_views.splice(r.index,1);p.$el.remove();var t=this.get_tracks_bounds();i.each(this.circular_views,function(u,v){u.update_radius_bounds(t[v])})},update_track_bounds:function(){var p=this.get_tracks_bounds();i.each(this.circular_views,function(q,r){q.update_radius_bounds(p[r])});i.each(this.chords_views,function(q){q.update_radius_bounds(p[0])})}});var m=Backbone.View.extend({tagName:"g",initialize:function(p){this.bg_stroke="ddd";this.loading_bg_fill="ffc";this.bg_fill="ddd";this.total_gap=p.total_gap;this.track=p.track;this.radius_bounds=p.radius_bounds;this.genome=p.genome;this.chroms_layout=this._chroms_layout();this.data_bounds=[];this.scale=1;this.parent_elt=n.select(this.$el[0])},get_fill_color:function(){var p=this.track.get("config").get_value("block_color");if(!p){p=this.track.get("config").get_value("color")}return p},render:function(){var t=this.parent_elt;var s=this.chroms_layout,v=n.svg.arc().innerRadius(this.radius_bounds[0]).outerRadius(this.radius_bounds[1]),p=t.selectAll("g").data(s).enter().append("svg:g"),r=p.append("path").attr("d",v).attr("class","chrom-background").style("stroke",this.bg_stroke).style("fill",this.loading_bg_fill);r.append("title").text(function(x){return x.data.chrom});var q=this,u=q.track.get("data_manager"),w=(u?u.data_is_ready():true);$.when(w).then(function(){$.when(q._render_data(t)).then(function(){r.style("fill",q.bg_fill);q.render_labels()})})},render_labels:function(){},update_radius_bounds:function(q){this.radius_bounds=q;var p=n.svg.arc().innerRadius(this.radius_bounds[0]).outerRadius(this.radius_bounds[1]);this.parent_elt.selectAll("g>path.chrom-background").transition().duration(1000).attr("d",p);this._transition_chrom_data();this._transition_labels()},update_scale:function(s){var r=this.scale;this.scale=s;if(s<=r){return}var q=this,p=new o();this.parent_elt.selectAll("path.chrom-data").filter(function(u,t){return p.is_visible(this)}).each(function(z,v){var y=n.select(this),u=y.attr("chrom"),x=q.genome.get_chrom_region(u),w=q.track.get("data_manager"),t;if(!w.can_get_more_detailed_data(x)){return}t=q.track.get("data_manager").get_more_detailed_data(x,"Coverage",0,s);$.when(t).then(function(C){y.remove();q._update_data_bounds();var B=i.find(q.chroms_layout,function(D){return D.data.chrom===u});var A=q.get_fill_color();q._render_chrom_data(q.parent_elt,B,C).style("stroke",A).style("fill",A)})});return q},_transition_chrom_data:function(){var q=this.track,s=this.chroms_layout,p=this.parent_elt.selectAll("g>path.chrom-data"),t=p[0].length;if(t>0){var r=this;$.when(q.get("data_manager").get_genome_wide_data(this.genome)).then(function(v){var u=i.reject(i.map(v,function(w,x){var y=null,z=r._get_path_function(s[x],w);if(z){y=z(w.data)}return y}),function(w){return w===null});p.each(function(x,w){n.select(this).transition().duration(1000).attr("d",u[w])})})}},_transition_labels:function(){},_update_data_bounds:function(){var p=this.data_bounds;this.data_bounds=this.get_data_bounds(this.track.get("data_manager").get_genome_wide_data(this.genome));if(this.data_bounds[0]<p[0]||this.data_bounds[1]>p[1]){this._transition_chrom_data()}},_render_data:function(s){var r=this,q=this.chroms_layout,p=this.track,t=$.Deferred();$.when(p.get("data_manager").get_genome_wide_data(this.genome)).then(function(v){r.data_bounds=r.get_data_bounds(v);layout_and_data=i.zip(q,v),chroms_data_layout=i.map(layout_and_data,function(w){var x=w[0],y=w[1];return r._render_chrom_data(s,x,y)});var u=r.get_fill_color();r.parent_elt.selectAll("path.chrom-data").style("stroke",u).style("fill",u);t.resolve(s)});return t},_render_chrom_data:function(p,q,r){},_get_path_function:function(q,p){},_chroms_layout:function(){var q=this.genome.get_chroms_info(),s=n.layout.pie().value(function(u){return u.len}).sort(null),t=s(q),p=2*Math.PI*this.total_gap/q.length,r=i.map(t,function(w,v){var u=w.endAngle-p;w.endAngle=(u>w.startAngle?u:w.startAngle);return w});return r}});var b=m.extend({initialize:function(p){m.prototype.initialize.call(this,p);this.innerRadius=this.radius_bounds[0];this.radius_bounds[0]=this.radius_bounds[1];this.bg_stroke="fff";this.bg_fill="fff";this.min_arc_len=0.05},_render_data:function(r){var q=this,p=r.selectAll("g");p.selectAll("path").attr("id",function(v){return"label-"+v.data.chrom});p.append("svg:text").filter(function(v){return v.endAngle-v.startAngle>q.min_arc_len}).attr("text-anchor","middle").append("svg:textPath").attr("class","chrom-label").attr("xlink:href",function(v){return"#label-"+v.data.chrom}).attr("startOffset","25%").text(function(v){return v.data.chrom});var s=function(x){var v=(x.endAngle-x.startAngle)/x.value,w=n.range(0,x.value,25000000).map(function(y,z){return{radius:q.innerRadius,angle:y*v+x.startAngle,label:z===0?0:(z%3?null:q.formatNum(y))}});if(w.length<4){w[w.length-1].label=q.formatNum(Math.round((w[w.length-1].angle-x.startAngle)/v))}return w};var u=function(v){return v.angle>Math.PI?"rotate(180)translate(-16)":null};var t=i.filter(this.chroms_layout,function(v){return v.endAngle-v.startAngle>q.min_arc_len});this.drawTicks(this.parent_elt,t,s,u)}});i.extend(b.prototype,j);var g=m.extend({_quantile:function(q,p){q.sort(n.ascending);return n.quantile(q,p)},_render_chrom_data:function(p,s,q){var t=this._get_path_function(s,q);if(!t){return null}var r=p.datum(q.data),u=r.append("path").attr("class","chrom-data").attr("chrom",s.data.chrom).attr("d",t);return u},_get_path_function:function(s,r){if(typeof r==="string"||!r.data||r.data.length===0){return null}var p=n.scale.linear().domain(this.data_bounds).range(this.radius_bounds).clamp(true);var t=n.scale.linear().domain([0,r.data.length]).range([s.startAngle,s.endAngle]);var q=n.svg.line.radial().interpolate("linear").radius(function(u){return p(u[1])}).angle(function(v,u){return t(u)});return n.svg.area.radial().interpolate(q.interpolate()).innerRadius(p(0)).outerRadius(q.radius()).angle(q.angle())},render_labels:function(){var p=this,q=function(){return"rotate(90)"};this.drawTicks(this.parent_elt,[this.chroms_layout[0]],this._data_bounds_ticks_fn(),q,true)},_transition_labels:function(){if(this.data_bounds.length===0){return}var q=this,s=i.filter(this.chroms_layout,function(t){return t.endAngle-t.startAngle>0.08}),r=i.filter(s,function(u,t){return t%3===0}),p=i.flatten(i.map(r,function(t){return q._data_bounds_ticks_fn()(t)}));this.parent_elt.selectAll("g.tick").data(p).transition().attr("transform",function(t){return"rotate("+(t.angle*180/Math.PI-90)+")translate("+t.radius+",0)"})},_data_bounds_ticks_fn:function(){var p=this;visibleChroms=0;return function(q){return[{radius:p.radius_bounds[0],angle:q.startAngle,label:p.formatNum(p.data_bounds[0])},{radius:p.radius_bounds[1],angle:q.startAngle,label:p.formatNum(p.data_bounds[1])}]}},get_data_bounds:function(p){}});i.extend(g.prototype,j);var e=g.extend({get_data_bounds:function(q){var p=i.flatten(i.map(q,function(r){if(r){return i.map(r.data,function(s){return parseInt(s[1],10)||0})}else{return 0}}));return[i.min(p),this._quantile(p,0.5)||i.max(p)]}});var l=m.extend({render:function(){var p=this;$.when(p.track.get("data_manager").data_is_ready()).then(function(){$.when(p.track.get("data_manager").get_genome_wide_data(p.genome)).then(function(s){var r=[],q=p.genome.get_chroms_info();i.each(s,function(w,v){var t=q[v].chrom;var u=i.map(w.data,function(y){var x=p._get_region_angle(t,y[1]),z=p._get_region_angle(y[3],y[4]);return{source:{startAngle:x,endAngle:x+0.01},target:{startAngle:z,endAngle:z+0.01}}});r=r.concat(u)});p.parent_elt.append("g").attr("class","chord").selectAll("path").data(r).enter().append("path").style("fill",p.get_fill_color()).attr("d",n.svg.chord().radius(p.radius_bounds[0])).style("opacity",1)})})},update_radius_bounds:function(p){this.radius_bounds=p;this.parent_elt.selectAll("path").transition().attr("d",n.svg.chord().radius(this.radius_bounds[0]))},_get_region_angle:function(r,p){var q=i.find(this.chroms_layout,function(s){return s.data.chrom===r});return q.endAngle-((q.endAngle-q.startAngle)*(q.data.len-p)/q.data.len)}});var f=Backbone.View.extend({initialize:function(){var p=new k.Genome(galaxy_config.app.genome),q=new k.GenomeVisualization(galaxy_config.app.viz_config);q.get("config").add([{key:"arc_dataset_height",label:"Arc Dataset Height",type:"int",value:25,view:"circster"},{key:"track_gap",label:"Gap Between Tracks",type:"int",value:5,view:"circster"},{key:"total_gap",label:"Gap [0-1]",type:"float",value:0.4,view:"circster",hidden:true}]);var s=new a({el:$("#center .unified-panel-body"),genome:p,model:q});s.render();$("#center .unified-panel-header-inner").append(galaxy_config.app.viz_config.title+" "+galaxy_config.app.viz_config.dbkey);var r=create_icon_buttons_menu([{icon_class:"plus-button",title:"Add tracks",on_click:function(){k.select_datasets(galaxy_config.root+"visualization/list_current_history_datasets",galaxy_config.root+"api/datasets",q.get("dbkey"),function(t){q.add_tracks(t)})}},{icon_class:"gear",title:"Settings",on_click:function(){var t=new c.ConfigSettingCollectionView({collection:q.get("config")});t.render_in_modal("Configure Visualization")}},{icon_class:"disk--arrow",title:"Save",on_click:function(){Galaxy.modal.show({title:"Saving...",body:"progress"});$.ajax({url:galaxy_config.root+"visualization/save",type:"POST",dataType:"json",data:{id:q.get("vis_id"),title:q.get("title"),dbkey:q.get("dbkey"),type:"trackster",vis_json:JSON.stringify(q)}}).success(function(t){Galaxy.modal.hide();q.set("vis_id",t.vis_id)}).error(function(){Galaxy.modal.show({title:"Could Not Save",body:"Could not save visualization. Please try again later.",buttons:{Cancel:function(){Galaxy.modal.hide()}}})})}},{icon_class:"cross-circle",title:"Close",on_click:function(){window.location=galaxy_config.root+"visualization/list"}}],{tooltip_config:{placement:"bottom"}});r.$el.attr("style","float: right");$("#center .unified-panel-header-inner").append(r.$el);$(".menu-button").tooltip({placement:"bottom"})}});return{GalaxyApp:f}});