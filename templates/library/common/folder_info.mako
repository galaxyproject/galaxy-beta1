<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/library/common/common.mako" import="render_template_info" />

<%
    from cgi import escape
    folder_name = escape( str( folder.name ), quote=True )
    folder_description = escape( str( folder.description ), quote=True )
%>

<br/><br/>
<ul class="manage-table-actions">
    <li>
        <a class="action-button" href="${h.url_for( controller='library_common', action='browse_library', cntrller=cntrller, id=library_id, use_panels=use_panels, show_deleted=show_deleted )}"><span>Browse this data library</span></a>
    </li>
</ul>

%if msg:
    ${render_msg( msg, messagetype )}
%endif

<div class="toolForm">
    <div class="toolFormTitle">Edit folder name and description</div>
    <div class="toolFormBody">
        %if cntrller=='library_admin' or trans.app.security_agent.can_modify_library_item( current_user_roles, folder ):
            <form name="folder" action="${h.url_for( controller='library_common', action='folder_info', cntrller=cntrller, id=trans.security.encode_id( folder.id ), library_id=library_id, use_panels=use_panels, show_deleted=show_deleted )}" method="post" >
                <div class="form-row">
                    <label>Name:</label>
                    <input type="text" name="name" value="${folder_name}" size="40"/>
                    <div style="clear: both"></div>
                </div>
                <div class="form-row">
                    <label>Description:</label>
                    <input type="text" name="description" value="${folder_description}" size="40"/>
                    <div style="clear: both"></div>
                </div>
                <div class="form-row">
                    <input type="submit" name="rename_folder_button" value="Save"/>
                </div>
            </form>
        %else:
            <div class="form-row">
                <label>Name:</label>
                ${folder_name}
                <div style="clear: both"></div>
            </div>
            <div class="form-row">
                <label>Description:</label>
                ${folder_description}
                <div style="clear: both"></div>
            </div>
        %endif
    </div>
</div>
%if widgets:
    ${render_template_info( cntrller=cntrller, item_type='folder', library_id=library_id, widgets=widgets, info_association=info_association, inherited=inherited, folder_id=trans.security.encode_id( folder.id ) )}
%endif
