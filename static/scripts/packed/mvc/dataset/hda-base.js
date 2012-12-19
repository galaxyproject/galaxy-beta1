var HDABaseView=BaseView.extend(LoggableMixin).extend({tagName:"div",className:"historyItemContainer",initialize:function(a){if(a.logger){this.logger=this.model.logger=a.logger}this.log(this+".initialize:",a);this.defaultPrimaryActionButtonRenderers=[this._render_showParamsButton];if(!a.urlTemplates){throw ("HDAView needs urlTemplates on initialize")}this.urlTemplates=a.urlTemplates;this.expanded=a.expanded||false;this.model.bind("change",this.render,this)},render:function(){var b=this,e=this.model.get("id"),c=this.model.get("state"),a=$("<div/>").attr("id","historyItem-"+e),d=(this.$el.children().size()===0);this.$el.attr("id","historyItemContainer-"+e);this.urls=this._renderUrls(this.urlTemplates,this.model.toJSON());a.addClass("historyItemWrapper").addClass("historyItem").addClass("historyItem-"+c);a.append(this._render_warnings());a.append(this._render_titleBar());this._setUpBehaviors(a);this.body=$(this._render_body());a.append(this.body);this.$el.fadeOut("fast",function(){b.$el.children().remove();b.$el.append(a).fadeIn("fast",function(){b.log(b+" rendered:",b.$el);var f="rendered";if(d){f+=":initial"}else{if(b.model.inReadyState()){f+=":ready"}}b.trigger(f)})});return this},_renderUrls:function(d,a){var b=this,c={};_.each(d,function(e,f){if(_.isObject(e)){c[f]=b._renderUrls(e,a)}else{if(f==="meta_download"){c[f]=b._renderMetaDownloadUrls(e,a)}else{try{c[f]=_.template(e,a)}catch(g){throw (b+"._renderUrls error: "+g+"\n rendering:"+e+"\n with "+JSON.stringify(a))}}}});return c},_renderMetaDownloadUrls:function(b,a){return _.map(a.meta_files,function(c){return{url:_.template(b,{id:a.id,file_type:c.file_type}),file_type:c.file_type}})},_setUpBehaviors:function(a){a=a||this.$el;make_popup_menus(a);a.find(".tooltip").tooltip({placement:"bottom"})},_render_warnings:function(){return $(jQuery.trim(HDABaseView.templates.messages(this.model.toJSON())))},_render_titleBar:function(){var a=$('<div class="historyItemTitleBar" style="overflow: hidden"></div>');a.append(this._render_titleButtons());a.append('<span class="state-icon"></span>');a.append(this._render_titleLink());return a},_render_titleButtons:function(){var a=$('<div class="historyItemButtons"></div>');a.append(this._render_displayButton());return a},_render_displayButton:function(){if((!this.model.inReadyState())||(this.model.get("state")===HistoryDatasetAssociation.STATES.NOT_VIEWABLE)||(!this.model.get("accessible"))){this.displayButton=null;return null}var a={icon_class:"display",target:"galaxy_main"};if(this.model.get("purged")){a.enabled=false;a.title=_l("Cannot display datasets removed from disk")}else{a.title=_l("Display data in browser");a.href=this.urls.display}this.displayButton=new IconButtonView({model:new IconButton(a)});return this.displayButton.render().$el},_render_titleLink:function(){return $(jQuery.trim(HDABaseView.templates.titleLink(_.extend(this.model.toJSON(),{urls:this.urls}))))},_render_hdaSummary:function(){var a=_.extend(this.model.toJSON(),{urls:this.urls});return HDABaseView.templates.hdaSummary(a)},_render_primaryActionButtons:function(c){var a=this,b=$("<div/>").attr("id","primary-actions-"+this.model.get("id"));_.each(c,function(d){b.append(d.call(a))});return b},_render_downloadButton:function(){if(this.model.get("purged")||!this.model.hasData()){return null}var a=HDABaseView.templates.downloadLinks(_.extend(this.model.toJSON(),{urls:this.urls}));return $(a)},_render_showParamsButton:function(){this.showParamsButton=new IconButtonView({model:new IconButton({title:_l("View details"),href:this.urls.show_params,target:"galaxy_main",icon_class:"information"})});return this.showParamsButton.render().$el},_render_displayApps:function(){if(!this.model.hasData()){return null}var a=$("<div/>").addClass("display-apps");if(!_.isEmpty(this.model.get("display_types"))){a.append(HDABaseView.templates.displayApps({displayApps:this.model.get("display_types")}))}if(!_.isEmpty(this.model.get("display_apps"))){a.append(HDABaseView.templates.displayApps({displayApps:this.model.get("display_apps")}))}return a},_render_peek:function(){if(!this.model.get("peek")){return null}return $("<div/>").append($("<pre/>").attr("id","peek"+this.model.get("id")).addClass("peek").append(this.model.get("peek")))},_render_body:function(){var a=$("<div/>").attr("id","info-"+this.model.get("id")).addClass("historyItemBody").attr("style","display: none");if(this.expanded){this._render_body_html(a);a.show()}return a},_render_body_html:function(a){a.html("");switch(this.model.get("state")){case HistoryDatasetAssociation.STATES.NEW:break;case HistoryDatasetAssociation.STATES.NOT_VIEWABLE:this._render_body_not_viewable(a);break;case HistoryDatasetAssociation.STATES.UPLOAD:this._render_body_uploading(a);break;case HistoryDatasetAssociation.STATES.PAUSED:this._render_body_paused(a);break;case HistoryDatasetAssociation.STATES.QUEUED:this._render_body_queued(a);break;case HistoryDatasetAssociation.STATES.RUNNING:this._render_body_running(a);break;case HistoryDatasetAssociation.STATES.ERROR:this._render_body_error(a);break;case HistoryDatasetAssociation.STATES.DISCARDED:this._render_body_discarded(a);break;case HistoryDatasetAssociation.STATES.SETTING_METADATA:this._render_body_setting_metadata(a);break;case HistoryDatasetAssociation.STATES.EMPTY:this._render_body_empty(a);break;case HistoryDatasetAssociation.STATES.FAILED_METADATA:this._render_body_failed_metadata(a);break;case HistoryDatasetAssociation.STATES.OK:this._render_body_ok(a);break;default:a.append($('<div>Error: unknown dataset state "'+this.model.get("state")+'".</div>'))}a.append('<div style="clear: both"></div>');this._setUpBehaviors(a)},_render_body_not_viewable:function(a){a.append($("<div>"+_l("You do not have permission to view dataset")+".</div>"))},_render_body_uploading:function(a){a.append($("<div>"+_l("Dataset is uploading")+"</div>"))},_render_body_queued:function(a){a.append($("<div>"+_l("Job is waiting to run")+".</div>"));a.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_paused:function(a){a.append($("<div>"+_l("Job is paused.  Use the history menu to unpause")+".</div>"));a.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_running:function(a){a.append("<div>"+_l("Job is currently running")+".</div>");a.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_error:function(a){if(!this.model.get("purged")){a.append($("<div>"+this.model.get("misc_blurb")+"</div>"))}a.append((_l("An error occurred running this job")+": <i>"+$.trim(this.model.get("misc_info"))+"</i>"));a.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers.concat([this._render_downloadButton])))},_render_body_discarded:function(a){a.append("<div>"+_l("The job creating this dataset was cancelled before completion")+".</div>");a.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_setting_metadata:function(a){a.append($("<div>"+_l("Metadata is being auto-detected")+".</div>"))},_render_body_empty:function(a){a.append($("<div>"+_l("No data")+": <i>"+this.model.get("misc_blurb")+"</i></div>"));a.append(this._render_primaryActionButtons(this.defaultPrimaryActionButtonRenderers))},_render_body_failed_metadata:function(a){a.append($(HDABaseView.templates.failedMetadata(this.model.toJSON())));this._render_body_ok(a)},_render_body_ok:function(a){a.append(this._render_hdaSummary());if(this.model.isDeletedOrPurged()){a.append(this._render_primaryActionButtons([this._render_downloadButton,this._render_showParamsButton]));return}a.append(this._render_primaryActionButtons([this._render_downloadButton,this._render_showParamsButton]));a.append('<div class="clear"/>');a.append(this._render_displayApps());a.append(this._render_peek())},events:{"click .historyItemTitle":"toggleBodyVisibility"},toggleBodyVisibility:function(c,a){var b=this;this.expanded=(a===undefined)?(!this.body.is(":visible")):(a);if(this.expanded){b._render_body_html(b.body);this.body.slideDown("fast",function(){b.trigger("body-expanded",b.model.get("id"))})}else{this.body.slideUp("fast",function(){b.trigger("body-collapsed",b.model.get("id"))})}},remove:function(b){var a=this;this.$el.fadeOut("fast",function(){a.$el.remove();if(b){b()}})},toString:function(){var a=(this.model)?(this.model+""):("(no model)");return"HDABaseView("+a+")"}});HDABaseView.templates={warningMsg:Handlebars.templates["template-warningmessagesmall"],messages:Handlebars.templates["template-hda-warning-messages"],titleLink:Handlebars.templates["template-hda-titleLink"],hdaSummary:Handlebars.templates["template-hda-hdaSummary"],downloadLinks:Handlebars.templates["template-hda-downloadLinks"],failedMetadata:Handlebars.templates["template-hda-failedMetadata"],displayApps:Handlebars.templates["template-hda-displayApps"]};