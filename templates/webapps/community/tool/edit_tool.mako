<%namespace file="/message.mako" import="render_msg" />

<%!
   def inherit(context):
       if context.get('use_panels'):
           return '/webapps/community/base_panels.mako'
       else:
           return '/base.mako'
%>
<%inherit file="${inherit(context)}"/>

<%def name="title()">Edit Tool</%def>

<h2>Edit Tool</h2>

%if message:
    ${render_msg( message, status )}
%endif

<form id="edit_tool" name="edit_tool" action="${h.url_for( controller='common', action='edit_tool' )}" method="post">
    <input type="hidden" name="id" value="${trans.app.security.encode_id( tool.id )}"/>
    <input type="hidden" name="cntrller" value="${cntrller}"/>
    <div class="toolForm">
        <div class="toolFormTitle">${tool.name} Version: ${tool.version}</div>
        <div class="toolFormBody">
        <div class="form-row">
            <label>Description:</label>
            <div class="form-row-input"><textarea name="description" rows="5" cols="35">${tool.user_description}</textarea></div>
            <div style="clear: both"></div>
        </div>
        <div class="form-row">
            <input type="submit" class="primary-button" name="edit_tool_button" value="Save">
        </div>
    </div>
</form>
