define(["galaxy.masthead"],function(b){var a=Backbone.Model.extend({options:null,masthead:null,initialize:function(c){this.options=c.config;this.masthead=c.masthead;this.create()},create:function(){var d=new b.GalaxyMastheadTab({title:"Analyze Data",content:"root/index"});this.masthead.append(d);var c=new b.GalaxyMastheadTab({title:"Workflow",content:"workflow"});this.masthead.append(c);var g=new b.GalaxyMastheadTab({title:"Shared Data",content:"library/index"});g.addMenu({title:"Data Libraries",content:"library/index",divider:true});g.addMenu({title:"Published Histories",content:"history/list_published"});g.addMenu({title:"Published Workflows",content:"workflow/list_published"});g.addMenu({title:"Published Visualizations",content:"visualization/list_published"});g.addMenu({title:"Published Pages",content:"page/list_published"});this.masthead.append(g);if(this.options.user.requests){var h=new b.GalaxyMastheadTab({title:"Lab"});h.addMenu({title:"Sequencing Requests",content:"requests/index"});h.addMenu({title:"Find Samples",content:"requests/find_samples_index"});h.addMenu({title:"Help",content:this.options.lims_doc_url});this.masthead.append(h)}var k=new b.GalaxyMastheadTab({title:"Visualization",content:"visualization/list"});k.addMenu({title:"New Track Browser",content:"visualization/trackster",target:"_frame"});k.addMenu({title:"Saved Visualizations",content:"visualization/list",target:"_frame"});this.masthead.append(k);if(this.options.enable_cloud_launch){var e=new b.GalaxyMastheadTab({title:"Cloud",content:"cloudlaunch/index"});e.addMenu({title:"New Cloud Cluster",content:"cloudlaunch/index"});this.masthead.append(e)}if(this.options.is_admin_user){var f=new b.GalaxyMastheadTab({title:"Admin",content:"admin/index",extra_class:"admin-only"});this.masthead.append(f)}var j=new b.GalaxyMastheadTab({title:"Help"});if(this.options.biostar_url){j.addMenu({title:"Galaxy Q&A Site",content:this.options.biostar_url_redirect,target:"_blank"});j.addMenu({title:"Ask a question",content:"biostar/biostar_question_redirect",target:"_blank"})}j.addMenu({title:"Support",content:this.options.support_url,target:"_blank"});j.addMenu({title:"Search",content:this.options.search_url,target:"_blank"});j.addMenu({title:"Mailing Lists",content:this.options.mailing_lists,target:"_blank"});j.addMenu({title:"Videos",content:this.options.screencasts_url,target:"_blank"});j.addMenu({title:"Wiki",content:this.options.wiki_url,target:"_blank"});j.addMenu({title:"How to Cite Galaxy",content:this.options.citation_url,target:"_blank"});if(!this.options.terms_url){j.addMenu({title:"Terms and Conditions",content:this.options.terms_url,target:"_blank"})}this.masthead.append(j);if(!this.options.user.valid){var i=new b.GalaxyMastheadTab({title:"User",extra_class:"loggedout-only"});i.addMenu({title:"Login",content:"user/login",target:"galaxy_main"});if(this.options.allow_user_creation){i.addMenu({title:"Register",content:"user/create",target:"galaxy_main"})}this.masthead.append(i)}else{var i=new b.GalaxyMastheadTab({title:"User",extra_class:"loggedin-only"});i.addMenu({title:"Logged in as "+this.options.user.email});if(this.options.use_remote_user&&this.options.remote_user_logout_href){i.addMenu({title:"Logout",content:this.options.remote_user_logout_href,target:"_top"})}else{i.addMenu({title:"Preferences",content:"user?cntrller=user",target:"galaxy_main"});i.addMenu({title:"Custom Builds",content:"user/dbkeys",target:"galaxy_main"});i.addMenu({title:"Logout",content:"user/logout",target:"_top",divider:true})}i.addMenu({title:"Saved Histories",content:"history/list",target:"galaxy_main"});i.addMenu({title:"Saved Datasets",content:"dataset/list",target:"galaxy_main"});i.addMenu({title:"Saved Pages",content:"page/list",target:"_top"});i.addMenu({title:"API Keys",content:"user/api_keys?cntrller=user",target:"galaxy_main"});if(this.options.use_remote_user){i.addMenu({title:"Public Name",content:"user/edit_username?cntrller=user",target:"galaxy_main"})}this.masthead.append(i)}}});return{GalaxyMenu:a}});