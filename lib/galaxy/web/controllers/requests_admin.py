from galaxy.web.base.controller import *
from galaxy.web.framework.helpers import time_ago, iff, grids
from galaxy.model.orm import *
from galaxy import model, util
from galaxy.web.form_builder import *
from galaxy.web.controllers.requests_common import RequestsGrid, invalid_id_redirect
from amqplib import client_0_8 as amqp
import logging, os, pexpect, ConfigParser

log = logging.getLogger( __name__ )

class AdminRequestsGrid( RequestsGrid ):
    class UserColumn( grids.TextColumn ):
        def get_value( self, trans, grid, request ):
            return request.user.email
    # Grid definition
    columns = [ col for col in RequestsGrid.columns ]
    columns.append( UserColumn( "User",
                                model_class=model.User,
                                key='username' ) )
    operations = [ operation for operation in RequestsGrid.operations ]
    operations.append( grids.GridOperation( "Edit", allow_multiple=False, condition=( lambda item: not item.deleted ) ) )
    operations.append( grids.GridOperation( "Reject", allow_multiple=False, condition=( lambda item: not item.deleted and item.is_submitted ) ) )
    operations.append( grids.GridOperation( "Delete", allow_multiple=True, condition=( lambda item: not item.deleted ) ) )
    operations.append( grids.GridOperation( "Undelete", condition=( lambda item: item.deleted ) ) )
    global_actions = [
        grids.GridAction( "Create new request", dict( controller='requests_common',
                                                      action='create_request', 
                                                      cntrller='requests_admin' ) )
    ]

class RequestTypeGrid( grids.Grid ):
    # Custom column types
    class NameColumn( grids.TextColumn ):
        def get_value(self, trans, grid, request_type):
            return request_type.name
    class DescriptionColumn( grids.TextColumn ):
        def get_value(self, trans, grid, request_type):
            return request_type.desc
    class RequestFormColumn( grids.TextColumn ):
        def get_value(self, trans, grid, request_type):
            return request_type.request_form.name
    class SampleFormColumn( grids.TextColumn ):
        def get_value(self, trans, grid, request_type):
            return request_type.sample_form.name

    # Grid definition
    webapp = "galaxy"
    title = "Sequencer Configurations"
    template = "admin/requests/grid.mako"
    model_class = model.RequestType
    default_sort_key = "-create_time"
    num_rows_per_page = 50
    preserve_state = True
    use_paging = True
    default_filter = dict( deleted="False" )
    columns = [
        NameColumn( "Name", 
                    key="name",
                    link=( lambda item: iff( item.deleted, None, dict( operation="view", id=item.id ) ) ),
                    attach_popup=True,
                    filterable="advanced" ),
        DescriptionColumn( "Description",
                           key='desc',
                           filterable="advanced" ),
        RequestFormColumn( "Request Form", 
                           link=( lambda item: iff( item.deleted, None, dict( operation="view_form_definition", id=item.request_form.id ) ) ) ),
        SampleFormColumn( "Sample Form", 
                           link=( lambda item: iff( item.deleted, None, dict( operation="view_form_definition", id=item.sample_form.id ) ) ) ),
        grids.DeletedColumn( "Deleted", 
                             key="deleted", 
                             visible=False, 
                             filterable="advanced" )
    ]
    columns.append( grids.MulticolFilterColumn( "Search", 
                                                cols_to_filter=[ columns[0], columns[1] ], 
                                                key="free-text-search",
                                                visible=False,
                                                filterable="standard" ) )
    operations = [
        grids.GridOperation( "Permissions", allow_multiple=False, condition=( lambda item: not item.deleted  )  ),
        grids.GridOperation( "Delete", allow_multiple=True, condition=( lambda item: not item.deleted  )  ),
        grids.GridOperation( "Undelete", condition=( lambda item: item.deleted ) ),    
    ]
    global_actions = [
        grids.GridAction( "Create new sequencer configuration", dict( controller='requests_admin', action='create_request_type' ) )
    ]

class DataTransferGrid( grids.Grid ):
    # Custom column types
    class NameColumn( grids.TextColumn ):
        def get_value( self, trans, grid, sample_dataset ):
            return sample_dataset.name
    class SizeColumn( grids.TextColumn ):
        def get_value( self, trans, grid, sample_dataset ):
            return sample_dataset.size
    class StatusColumn( grids.TextColumn ):
        def get_value( self, trans, grid, sample_dataset ):
            return sample_dataset.status
    # Grid definition
    webapp = "galaxy"
    title = "Sample Datasets"
    template = "admin/requests/grid.mako"
    model_class = model.SampleDataset
    default_sort_key = "-create_time"
    num_rows_per_page = 50
    preserve_state = True
    use_paging = False
    columns = [
        NameColumn( "Name", 
                    link=( lambda item: dict( operation="view", id=item.id ) ),
                    attach_popup=True,
                    filterable="advanced" ),
        SizeColumn( "Size",
                    filterable="advanced" ),
        grids.GridColumn( "Last Updated", 
                          key="update_time", 
                          format=time_ago ),
        StatusColumn( "Status",
                      filterable="advanced" ),
    ]
    columns.append( grids.MulticolFilterColumn( "Search", 
                                                cols_to_filter=[ columns[0] ], 
                                                key="free-text-search",
                                                visible=False,
                                                filterable="standard" ) )
    operations = [
        grids.GridOperation( "Transfer",
                             allow_multiple=True,
                             condition=( lambda item: item.status in [ model.SampleDataset.transfer_status.NOT_STARTED ] ),
                             url_args=dict( webapp="galaxy" ) ),
        grids.GridOperation( "Rename",
                             allow_multiple=True,
                             allow_popup=False,
                             condition=( lambda item: item.status in [ model.SampleDataset.transfer_status.NOT_STARTED ] ),
                             url_args=dict( webapp="galaxy" ) ),
        grids.GridOperation( "Delete",
                             allow_multiple=True,
                             condition=( lambda item: item.status in [ model.SampleDataset.transfer_status.NOT_STARTED ] ),
                             url_args=dict( webapp="galaxy" ) )
    ]
    def apply_query_filter( self, trans, query, **kwd ):
        sample_id = kwd.get( 'sample_id', None )
        if not sample_id:
            return query
        return query.filter_by( sample_id=trans.security.decode_id( sample_id ) )

class RequestsAdmin( BaseController, UsesFormDefinitionWidgets ):
    request_grid = AdminRequestsGrid()
    requesttype_grid = RequestTypeGrid()
    datatx_grid = DataTransferGrid()

    @web.expose
    @web.require_admin
    def index( self, trans ):
        return trans.fill_template( "/admin/requests/index.mako" )
    @web.expose
    @web.require_admin
    def browse_requests( self, trans, **kwd ):
        if 'operation' in kwd:
            operation = kwd['operation'].lower()
            if operation == "edit":
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='edit_basic_request_info',
                                                                  cntrller='requests_admin',
                                                                  **kwd ) )
            if operation == "edit_samples":
                kwd[ 'editing_samples' ] = True
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='edit_samples',
                                                                  cntrller='requests_admin',
                                                                  **kwd ) )
            if operation == "view_request":
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='view_request',
                                                                  cntrller='requests_admin',
                                                                  **kwd ) )
            if operation == "request_events":
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='request_events',
                                                                  cntrller='requests_admin',
                                                                  **kwd ) )
            if operation == "reject":
                return self.reject_request( trans, **kwd )
            if operation == "view_type":
                return self.view_request_type( trans, **kwd )
            if operation == "delete":
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='delete_request',
                                                                  cntrller='requests_admin',
                                                                  **kwd ) )
            if operation == "undelete":
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='undelete_request',
                                                                  cntrller='requests_admin',
                                                                  **kwd ) )
        # Render the list view
        return self.request_grid( trans, **kwd )
    @web.expose
    @web.require_admin
    def reject_request( self, trans, **kwd ):
        params = util.Params( kwd )
        request_id = params.get( 'id', '' )
        status = params.get( 'status', 'done' )
        message = params.get( 'message', 'done' )
        if params.get( 'cancel_reject_button', False ):
            return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                              action='view_request',
                                                              cntrller='requests_admin',
                                                              id=request_id ) )
        try:
            request = trans.sa_session.query( trans.model.Request ).get( trans.security.decode_id( request_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', request_id )
        # Validate
        comment = util.restore_text( params.get( 'comment', '' ) )
        if not comment:
            status='error'
            message='A reason for rejecting the request is required.'
            return trans.fill_template( '/admin/requests/reject.mako', 
                                        cntrller='requests_admin',
                                        request=request,
                                        status=status,
                                        message=message )
        # Create an event with state 'Rejected' for this request
        event_comment = "Request marked rejected by %s. Reason: %s " % ( trans.user.email, comment )
        event = trans.model.RequestEvent( request, request.states.REJECTED, event_comment )
        trans.sa_session.add( event )
        trans.sa_session.flush()
        message='Request (%s) has been rejected.' % request.name
        return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                          action='browse_requests',
                                                          status=status,
                                                          message=message,
                                                          **kwd ) )
    # Data transfer from sequencer
    @web.expose
    @web.require_admin
    def manage_datasets( self, trans, **kwd ):
        def handle_error( **kwd ):
            kwd[ 'status' ] = 'error'
            return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                              action='manage_datasets',
                                                              **kwd ) )
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        if 'operation' in kwd:
            operation = kwd[ 'operation' ].lower()
            sample_dataset_id = params.get( 'id', None )
            if not sample_dataset_id:
                message = 'Select at least 1 dataset to %s.' % operation
                kwd[ 'message' ] = message
                del kwd[ 'operation' ]
                handle_error( **kwd )
            id_list = util.listify( sample_dataset_id )
            selected_sample_datasets = []
            for sample_dataset_id in id_list:
                try:
                    sample_dataset = trans.sa_session.query( trans.model.SampleDataset ).get( trans.security.decode_id( sample_dataset_id ) )
                except:
                    return invalid_id_redirect( trans, 'requests_admin', sample_dataset_id )
                selected_sample_datasets.append( sample_dataset )
            if operation == "view":
                return trans.fill_template( '/admin/requests/view_sample_dataset.mako',
                                            cntrller='requests_admin',
                                            sample_dataset=selected_sample_datasets[0] )
            elif operation == "delete":
                not_deleted = []
                for sample_dataset in selected_sample_datasets:
                    # Make sure the dataset has been transferred before deleting it.
                    if sample_dataset in sample_dataset.sample.untransferred_dataset_files:
                        # Save the sample dataset
                        sample = sample_dataset.sample
                        trans.sa_session.delete( sample_dataset )
                        trans.sa_session.flush()
                    else:
                        not_deleted.append( sample_dataset.name )
                message = '%i datasets have been deleted.' % ( len( id_list ) - len( not_deleted ) )
                if not_deleted:
                    status = 'warning'
                    message = message + '  %s could not be deleted because their transfer status is not "Not Started". ' % str( not_deleted )
                return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                                  action='manage_datasets',
                                                                  sample_id=trans.security.encode_id( sample.id ),
                                                                  status=status,
                                                                  message=message ) )
            elif operation == "rename":
                # If one of the selected sample datasets is in the NOT_STARTED state,
                # then display an error message.  A NOT_STARTED state implies the dataset
                # has not yet been transferred.
                no_datasets_transferred = True
                for selected_sample_dataset in selected_sample_datasets:
                    if selected_sample_dataset in selected_sample_dataset.sample.untransferred_dataset_files:
                        no_datasets_transferred = False
                        break
                if no_datasets_transferred:
                    status = 'error'
                    message = 'A dataset can be renamed only if it has been transferred.'
                    return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                                      action='manage_datasets',
                                                                      sample_id=trans.security.encode_id( selected_sample_datasets[0].sample.id ),
                                                                      status=status,
                                                                      message=message ) )
                return trans.fill_template( '/admin/requests/rename_datasets.mako', 
                                            sample=selected_sample_datasets[0].sample,
                                            id_list=id_list )
            elif operation == "transfer":
                self.initiate_data_transfer( trans,
                                             trans.security.encode_id( selected_sample_datasets[0].sample.id ),
                                             sample_datasets=selected_sample_datasets )
        # Render the grid view
        sample_id = params.get( 'sample_id', None )
        try:
            sample = trans.sa_session.query( trans.model.Sample ).get( trans.security.decode_id ( sample_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', sample_id )
        request_id = trans.security.encode_id( sample.request.id )
        library_id = trans.security.encode_id( sample.library.id )
        self.datatx_grid.title = 'Manage "%s" datasets'  % sample.name
        self.datatx_grid.global_actions = [ grids.GridAction( "Select more datasets", 
                                                              dict( controller='requests_admin', 
                                                                    action='select_datasets_to_transfer',
                                                                    request_id=request_id,
                                                                    sample_id=sample_id ) ),
                                            grids.GridAction( "Browse target data library", 
                                                              dict( controller='library_common', 
                                                                    action='browse_library', 
                                                                    cntrller='library_admin', 
                                                                    id=library_id ) ),
                                            grids.GridAction( "Browse this request", 
                                                              dict( controller='requests_common', 
                                                                    action='view_request',
                                                                    cntrller='requests_admin',
                                                                    id=request_id ) ),
                                            grids.GridAction( "Refresh page", 
                                                              dict( controller='requests_admin', 
                                                                    action='manage_datasets',
                                                                    sample_id=sample_id ) ) ]
        return self.datatx_grid( trans, **kwd )
    @web.expose
    @web.require_admin
    def rename_datasets( self, trans, **kwd ):
        # This method is called from the DataTransferGrid when a user is renaming 1 or more
        # SampleDatasets.
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        sample_id = kwd.get( 'sample_id', None )
        try:
            sample = trans.sa_session.query( trans.model.Sample ).get( trans.security.decode_id( sample_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', sample_id )
        # id_list is list of SampleDataset ids, which is a subset of all
        # of the SampleDatasets associated with the Sample.  The user may
        # or may not have selected all of the SampleDatasets for renaming.
        id_list = util.listify( kwd.get( 'id_list', [] ) )
        # Get all of the SampleDatasets
        sample_datasets = []
        for sample_dataset_id in id_list:
            sample_dataset = trans.sa_session.query( trans.app.model.SampleDataset ).get( trans.security.decode_id( sample_dataset_id ) )
            sample_datasets.append( sample_dataset )
        if params.get( 'rename_datasets_button', False ):
            for sample_dataset in sample_datasets:
                encoded_id = trans.security.encode_id( sample_dataset.id )
                selected_option = util.restore_text( params.get( 'rename_datasets_for_sample_%s' % encoded_id, '' ) )
                new_name = util.restore_text( params.get( 'new_name_%s' % encoded_id, '' ) )
                if selected_option == 'none':
                    sample_dataset.name = new_name
                else: 
                    sample_dataset.name = '%s_%s' % ( selected_option, new_name )
                trans.sa_session.add( sample_dataset )
                trans.sa_session.flush()
            message = 'Changes saved successfully.'
            return trans.fill_template( '/admin/requests/rename_datasets.mako', 
                                        sample=sample,
                                        id_list=id_list,
                                        message=message,
                                        status=status )
        return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                          action='manage_datasets',
                                                          sample_id=sample_id ) )
    @web.expose
    @web.require_admin
    def select_datasets_to_transfer( self, trans, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', '' ) )
        status = params.get( 'status', 'done' )
        request_id = kwd.get( 'request_id', None )
        files = []
        def handle_error( **kwd ):
            kwd[ 'status' ] = 'error'
            return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                              action='select_datasets_to_transfer',
                                                              **kwd ) )
        try:
            request = trans.sa_session.query( trans.model.Request ).get( trans.security.decode_id( request_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', request_id )
        selected_datasets_to_transfer = util.restore_text( params.get( 'selected_datasets_to_transfer', '' ) )
        if selected_datasets_to_transfer:
            selected_datasets_to_transfer = selected_datasets_to_transfer.split(',')
        else:
            selected_datasets_to_transfer = []
        sample_id = kwd.get( 'sample_id', 'none' )
        sample_id_select_field = self.__build_sample_id_select_field( trans, request, sample_id )
        if sample_id != 'none':
            sample = trans.sa_session.query( trans.model.Sample ).get( trans.security.decode_id( sample_id ) )
        else:
            sample = None
        # The __get_files() method redirects here with a status of 'error' and a message if there
        # was a problem retrieving the files.
        if params.get( 'select_datasets_to_transfer_button', False ):
            # Get the sample that was sequenced to produce these datasets.
            if sample_id == 'none':
                message = 'Select the sample that was sequenced to produce the datasets you want to transfer.'
                kwd[ 'message' ] = message
                del kwd[ 'select_datasets_to_transfer_button' ]
                handle_error( **kwd )
            if sample in sample.request.samples_without_library_destinations:
                # Display an error if a sample has been selected that
                # has not yet been associated with a destination library.
                message = 'Select a target data library and folder for the sample before selecting the datasets.'
                status = 'error'
                return trans.response.send_redirect( web.url_for( controller='requests_common',
                                                                  action='edit_samples',
                                                                  cntrller='requests_admin',
                                                                  id=trans.security.encode_id( request.id ),
                                                                  editing_samples=True,
                                                                  status=status,
                                                                  message=message ) )
            # Save the sample datasets 
            sample_dataset_file_names = self.__save_sample_datasets( trans, sample, selected_datasets_to_transfer )
            if sample_dataset_file_names:
                message = 'Datasets (%s) have been selected for sample (%s)' % \
                    ( str( sample_dataset_file_names )[1:-1].replace( "'", "" ), sample.name )
            return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                              action='manage_datasets',
                                                              request_id=request_id,
                                                              sample_id=sample_id,
                                                              message=message,
                                                              status=status ) )
        return trans.fill_template( '/admin/requests/select_datasets_to_transfer.mako',
                                    cntrller='requests_admin',
                                    request=request,
                                    sample=sample,
                                    sample_id_select_field=sample_id_select_field,
                                    status=status,
                                    message=message )
    @web.json
    def get_file_details( self, trans, id, folder_path ):
        def print_ticks( d ):
            # pexpect timeout method
            pass
        # Avoid caching
        trans.response.headers['Pragma'] = 'no-cache'
        trans.response.headers['Expires'] = '0'
        request = trans.sa_session.query( trans.model.Request ).get( int( id ) )
        datatx_info = request.type.datatx_info
        cmd  = 'ssh %s@%s "ls -oghp \'%s\'"' % ( datatx_info['username'],
                                                 datatx_info['host'],
                                                 folder_path )
        output = pexpect.run( cmd,
                              events={ '.ssword:*' : datatx_info[ 'password'] + '\r\n', pexpect.TIMEOUT : print_ticks }, 
                              timeout=10 )
        return unicode( output.replace( '\n', '<br/>' ) )
    @web.json
    def open_folder( self, trans, id, key ):
        # Avoid caching
        trans.response.headers['Pragma'] = 'no-cache'
        trans.response.headers['Expires'] = '0'
        request = trans.sa_session.query( trans.model.Request ).get( int( id ) )
        folder_path = key
        files_list = self.__get_files( trans, request, folder_path )
        folder_contents = []
        for filename in files_list:
            is_folder = False
            if filename[-1] == os.sep:
                is_folder = True
            full_path = os.path.join(folder_path, filename)
            node = {"title": filename,
                    "isFolder": is_folder,
                    "isLazy": is_folder,
                    "tooltip": full_path,
                    "key": full_path
                    }
            folder_contents.append(node)
        return folder_contents
    def __get_files( self, trans, request, folder_path ):
        # Retrieves the filenames to be transferred from the remote host.
        ok = True
        datatx_info = request.type.datatx_info
        if not datatx_info[ 'host' ] or not datatx_info[ 'username' ] or not datatx_info[ 'password' ]:
            status = 'error'
            message = "Error in sequencer login information."
            ok = False
        def print_ticks( d ):
            pass
        cmd  = 'ssh %s@%s "ls -p \'%s\'"' % ( datatx_info['username'], datatx_info['host'], folder_path )
        output = pexpect.run( cmd,
                              events={ '.ssword:*' : datatx_info['password'] + '\r\n', pexpect.TIMEOUT : print_ticks }, 
                              timeout=10 )
        if 'No such file or directory' in output:
            status = 'error'
            message = "No folder named (%s) exists on the sequencer." % folder_path
            ok = False
        if ok:
            return output.splitlines()
        return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                          action='select_datasets_to_transfer',
                                                          request_id=trans.security.encode_id( request.id ),
                                                          status=status,
                                                          message=message ) )
    def __check_path( self, a_path ):
        # Return a valid folder_path
        if a_path and not a_path.endswith( os.sep ):
            a_path += os.sep
        return a_path
    def __save_sample_datasets( self, trans, sample, selected_datasets_to_transfer ):
        sample_dataset_file_names = []
        if selected_datasets_to_transfer:
            for filepath in selected_datasets_to_transfer:
                # FIXME: handle folder selection
                # ignore folders for now
                if filepath[-1] != os.sep:
                    name = self.__dataset_name( sample, filepath.split( '/' )[-1] )
                    status = trans.app.model.SampleDataset.transfer_status.NOT_STARTED
                    size = sample.get_untransferred_dataset_size( filepath )
                    sample_dataset = trans.model.SampleDataset( sample=sample,
                                                                file_path=filepath,
                                                                status=status,
                                                                name=name,
                                                                error_msg='',
                                                                size=size )
                    trans.sa_session.add( sample_dataset )
                    trans.sa_session.flush()
                    sample_dataset_file_names.append( str( sample_dataset.name ) )
        return sample_dataset_file_names
    def dataset_file_size( self, sample, filepath ):
        def print_ticks(d):
            pass
        datatx_info = sample.request.type.datatx_info
        cmd  = 'ssh %s@%s "du -sh \'%s\'"' % ( datatx_info['username'], datatx_info['host'], filepath )
        output = pexpect.run( cmd,
                              events={ '.ssword:*': datatx_info['password']+'\r\n', 
                                       pexpect.TIMEOUT:print_ticks}, 
                              timeout=10 )
        return output.replace( filepath, '' ).strip()
    def __dataset_name( self, sample, filepath ):
        name = filepath.split( '/' )[-1]
        options = sample.request.type.rename_dataset_options
        option = sample.request.type.datatx_info.get( 'rename_dataset', options.NO ) 
        if option == options.NO:
            return name
        if option == options.SAMPLE_NAME:
            return sample.name + '_' + name
        if option == options.EXPERIMENT_AND_SAMPLE_NAME:
            return sample.request.name + '_' + sample.name + '_' + name
        if opt == options.EXPERIMENT_NAME:
            return sample.request.name + '_' + name
    def __check_library_add_permission( self, trans, target_library, target_folder ):
        """
        Checks if the current admin user had ADD_LIBRARY permission on the target library
        and the target folder, if not provide the permissions.
        """
        current_user_roles = trans.user.all_roles()
        current_user_private_role = trans.app.security_agent.get_private_user_role( trans.user )
        # Make sure this user has LIBRARY_ADD permissions on the target library and folder.
        # If not, give them permission.
        if not trans.app.security_agent.can_add_library_item( current_user_roles, target_library ):
            lp = trans.model.LibraryPermissions( trans.app.security_agent.permitted_actions.LIBRARY_ADD.action,
                                                 target_library, 
                                                 current_user_private_role )
            trans.sa_session.add( lp )
        if not trans.app.security_agent.can_add_library_item( current_user_roles, target_folder ):
            lfp = trans.model.LibraryFolderPermissions( trans.app.security_agent.permitted_actions.LIBRARY_ADD.action,
                                                        target_folder, 
                                                        current_user_private_role )
            trans.sa_session.add( lfp )
            trans.sa_session.flush()
    def __create_data_transfer_message( self, trans, sample, selected_sample_datasets ):
        """
        Creates an xml message to send to the rabbitmq server
        """
        datatx_info = sample.request.type.datatx_info
        # Create the xml message based on the following template
        xml = \
            ''' <data_transfer>
                    <galaxy_host>%(GALAXY_HOST)s</galaxy_host>
                    <api_key>%(API_KEY)s</api_key>
                    <data_host>%(DATA_HOST)s</data_host>
                    <data_user>%(DATA_USER)s</data_user>
                    <data_password>%(DATA_PASSWORD)s</data_password>
                    <request_id>%(REQUEST_ID)s</request_id>
                    <sample_id>%(SAMPLE_ID)s</sample_id>
                    <library_id>%(LIBRARY_ID)s</library_id>
                    <folder_id>%(FOLDER_ID)s</folder_id>
                    %(DATASETS)s
                </data_transfer>'''
        dataset_xml = \
            '''<dataset>
                   <dataset_id>%(ID)s</dataset_id>
                   <name>%(NAME)s</name>
                   <file>%(FILE)s</file>
               </dataset>'''
        datasets = ''
        for sample_dataset in selected_sample_datasets:
            if sample_dataset.status == trans.app.model.SampleDataset.transfer_status.NOT_STARTED:
                datasets = datasets + dataset_xml % dict( ID=str( sample_dataset.id ),
                                                          NAME=sample_dataset.name,
                                                          FILE=sample_dataset.file_path )
                sample_dataset.status = trans.app.model.SampleDataset.transfer_status.IN_QUEUE
                trans.sa_session.add( sample_dataset )
                trans.sa_session.flush()
        message = xml % dict(  GALAXY_HOST=trans.request.host,
                               API_KEY=trans.user.api_keys[0].key,
                               DATA_HOST=datatx_info[ 'host' ],
                               DATA_USER=datatx_info[ 'username' ],
                               DATA_PASSWORD=datatx_info[ 'password' ],
                               REQUEST_ID=str( sample.request.id ),
                               SAMPLE_ID=str( sample.id ),
                               LIBRARY_ID=str( sample.library.id ),
                               FOLDER_ID=str( sample.folder.id ),
                               DATASETS=datasets )
        return message
    def __validate_data_transfer_settings( self, trans, sample ):
        err_msg = ''
        # check the sequencer login info
        datatx_info = sample.request.type.datatx_info
        if not datatx_info[ 'host' ] \
            or not datatx_info[ 'username' ] \
            or not datatx_info[ 'password' ]:
            err_msg += "Error in sequencer login information.  "
        # Make sure web API is enabled and API key exists
        if not trans.app.config.enable_api:
            err_msg += "The 'enable_api = True' setting is not correctly set in the Galaxy config file.  "
        if not trans.user.api_keys:
            err_msg += "Set your API Key in your User Preferences to transfer datasets."
        # check if library_import_dir is set
        if not trans.app.config.library_import_dir:
            err_msg = "'The library_import_dir' setting is not set in the Galaxy config file."
        # check the RabbitMQ server settings in the config file
        for k, v in trans.app.config.amqp.items():
            if not v:
                err_msg += 'Set RabbitMQ server settings in the "galaxy_amqp" section of the Galaxy config file. %s is not set.' % k
                break
        return err_msg
    @web.expose
    @web.require_admin
    def initiate_data_transfer( self, trans, sample_id, sample_datasets=[], sample_dataset_id='' ):
        '''
        This method initiates the transfer of the datasets from the sequencer. It 
        happens in the following steps:
        - The current admin user needs to have LIBRARY_ADD permission for the
          target library and folder
        - Create an XML message encapsulating all the data transfer info and send it
          to the message queue (RabbitMQ broker)
        '''
        try:
            sample = trans.sa_session.query( trans.model.Sample ).get( trans.security.decode_id( sample_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', sample_id )
        # Check data transfer settings
        err_msg = self.__validate_data_transfer_settings( trans, sample )
        if not err_msg:
            # Make sure the current user has LIBRARY_ADD
            # permission on the target library and folder.
            self.__check_library_add_permission( trans, sample.library, sample.folder )
            if sample_dataset_id and not sample_datasets:
                # Either a list of SampleDataset objects or a comma-separated string of
                # encoded SampleDataset ids can be received.  If the latter, parse the
                # sample_dataset_id to build the list of sample_datasets.
                id_list = util.listify( sample_dataset_id )
                for sample_dataset_id in id_list:
                    sample_dataset = trans.sa_session.query( trans.model.SampleDataset ).get( trans.security.decode_id( sample_dataset_id ) )
                sample_datasets.append( sample_dataset )
            # Create the message
            message = self.__create_data_transfer_message( trans, 
                                                           sample, 
                                                           sample_datasets )
            # Send the message 
            try:
                conn = amqp.Connection( host=trans.app.config.amqp[ 'host' ] + ":" + trans.app.config.amqp[ 'port' ], 
                                        userid=trans.app.config.amqp[ 'userid' ], 
                                        password=trans.app.config.amqp[ 'password' ], 
                                        virtual_host=trans.app.config.amqp[ 'virtual_host' ], 
                                        insist=False )    
                chan = conn.channel()
                msg = amqp.Message( message.replace( '\n', '' ).replace( '\r', '' ), 
                                    content_type='text/plain', 
                                    application_headers={ 'msg_type': 'data_transfer' } )
                msg.properties[ "delivery_mode" ] = 2
                chan.basic_publish( msg,
                                    exchange=trans.app.config.amqp[ 'exchange' ],
                                    routing_key=trans.app.config.amqp[ 'routing_key' ] )
                chan.close()
                conn.close()
            except Exception, e:
                err_msg = "Error sending the data transfer message to the Galaxy AMQP message queue:<br/>%s" % str(e)
        if not err_msg:
            err_msg = "%i datasets have been queued for transfer from the sequencer. Click the Refresh button above to monitor the transfer status." % len( sample_datasets )
            status = "done"
        else:
            status = 'error'
        return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                          action='manage_datasets',
                                                          sample_id=trans.security.encode_id( sample.id ),
                                                          status=status,
                                                          message=err_msg ) )
    @web.expose
    def update_sample_dataset_status(self, trans, cntrller, sample_dataset_ids, new_status, error_msg=None ):
        # check if the new status is a valid transfer status
        possible_status_list = [v[1] for v in trans.app.model.SampleDataset.transfer_status.items()] 
        if new_status not in possible_status_list:
            trans.response.status = 400
            return "The requested transfer status ( %s ) is not a valid transfer status." % new_status
        for id in util.listify( sample_dataset_ids ):
            try:
                sd_id = trans.security.decode_id( id )
                sample_dataset = trans.sa_session.query( trans.app.model.SampleDataset ).get( sd_id )
            except:
                trans.response.status = 400
                return "Invalid sample dataset id ( %s ) specified." % str( id )
            sample_dataset.status = new_status
            sample_dataset.error_msg = error_msg
            trans.sa_session.add( sample_dataset )
            trans.sa_session.flush()
        return 200, 'Done'
    # Request Type Stuff
    @web.expose
    @web.require_admin
    def browse_request_types( self, trans, **kwd ):
        if 'operation' in kwd:
            operation = kwd['operation'].lower()
            obj_id = kwd.get( 'id', None )
            if operation == "view_form_definition":
                return self.view_form_definition( trans, **kwd )
            elif operation == "view":
                return self.view_request_type( trans, **kwd )
            elif operation == "delete":
                return self.delete_request_type( trans, **kwd )
            elif operation == "undelete":
                return self.undelete_request_type( trans, **kwd )
            elif operation == "permissions":
                return self.request_type_permissions( trans, **kwd )
        # Render the grid view
        return self.requesttype_grid( trans, **kwd )
    @web.expose
    @web.require_admin
    def create_request_type( self, trans, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        rt_info_widgets, rt_states_widgets = self.__create_request_type_form( trans, **kwd )
        rename_dataset_select_field = self.__build_rename_dataset_select_field( trans )
        if params.get( 'add_state_button', False ):
            # FIXME: why do we append a tuple of 2 empty strings????
            rt_states_widgets.append( ( "", "" ) )
        elif params.get( 'remove_state_button', False ):
            index = int( params.get( 'remove_state_button', '' ).split(" ")[2] )
            del rt_states_widgets[ index-1 ]
        elif params.get( 'save_request_type', False ):
            request_type, message = self.__save_request_type( trans, **kwd )
            if not request_type:
                status='error'
            else:
                message = 'Sequencer configuration (%s) has been created' % request_type.name
                return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                                  action='browse_request_types',
                                                                  message=message,
                                                                  status=status ) )
        elif params.get( 'save_changes', False ):
            request_type_id = params.get( 'rt_id', None )
            try:
                request_type = trans.sa_session.query( trans.model.RequestType ).get( trans.security.decode_id( request_type_id ) )
            except:
                return invalid_id_redirect( trans, 'requests_admin', request_type_id, action='browse_request_types' )
            # Data transfer info - make sure password is retrieved from kwd rather
            # than Params since Params may have munged the characters.
            request_type.datatx_info = dict( host=util.restore_text( params.get( 'host', '' ) ),
                                             username=util.restore_text( params.get( 'username', '' ) ),
                                             password=kwd.get( 'password', '' ),
                                             data_dir=util.restore_text( params.get( 'data_dir', '' ) ),
                                             rename_dataset=util.restore_text( params.get( 'rename_dataset', False ) ) )
            data_dir = self.__check_path( request_type.datatx_info[ 'data_dir' ] )
            request_type.datatx_info[ 'data_dir' ] = data_dir
            trans.sa_session.add( request_type )
            trans.sa_session.flush()
            message = 'Changes made to sequencer configuration <b>%s</b> has been saved' % request_type.name
            return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                              action='view_request_type',
                                                              id=request_type_id,
                                                              message=message,
                                                              status=status ) )
        return trans.fill_template( '/admin/requests/create_request_type.mako',
                                    rt_info_widgets=rt_info_widgets,
                                    rt_states_widgets=rt_states_widgets,
                                    rename_dataset_select_field=rename_dataset_select_field,
                                    message=message,
                                    status=status )
    def __create_request_type_form( self, trans, **kwd ):
        request_form_definitions = self.get_all_forms( trans, 
                                                        filter=dict( deleted=False ),
                                                        form_type=trans.model.FormDefinition.types.REQUEST )
        sample_form_definitions = self.get_all_forms( trans, 
                                                      filter=dict( deleted=False ),
                                                      form_type=trans.model.FormDefinition.types.SAMPLE )
        if not request_form_definitions or not sample_form_definitions:
            return [],[]
        params = util.Params( kwd )
        request_form_id = params.get( 'request_form_id', 'none' )
        sample_form_id = params.get( 'sample_form_id', 'none' )
        request_form_id_select_field = build_select_field( trans,
                                                           objs=request_form_definitions,
                                                           label_attr='name',
                                                           select_field_name='request_form_id',
                                                           selected_value=request_form_id,
                                                           refresh_on_change=False )
        sample_form_id_select_field = build_select_field( trans,
                                                           objs=sample_form_definitions,
                                                           label_attr='name',
                                                           select_field_name='sample_form_id',
                                                           selected_value=sample_form_id,
                                                           refresh_on_change=False )
        rt_info_widgets = [ dict( label='Name', 
                                  widget=TextField( 'name', 40, util.restore_text( params.get( 'name', '' ) ) ) ),
                            dict( label='Description', 
                                  widget=TextField( 'desc', 40, util.restore_text( params.get( 'desc', '' ) ) ) ),
                            dict( label='Request form',
                                  widget=request_form_id_select_field ),
                            dict( label='Sample form',
                                  widget=sample_form_id_select_field ) ]
        # Possible sample states
        rt_states = []
        i=0
        while True:
            if kwd.has_key( 'state_name_%i' % i ):
                rt_states.append( ( params.get( 'state_name_%i' % i, ''  ), 
                                    params.get( 'state_desc_%i' % i, ''  ) ) )
                i += 1
            else:
                break
        return rt_info_widgets, rt_states
    def __save_request_type(self, trans, **kwd):
        params = util.Params( kwd )
        name = util.restore_text( params.get( 'name', ''  ) )
        desc = util.restore_text( params.get( 'desc', '' ) )
        request_form_id = params.get( 'request_form_id', None )
        request_form = trans.sa_session.query( trans.model.FormDefinition ).get( trans.security.decode_id( request_form_id ) )
        sample_form_id = params.get( 'sample_form_id', None )
        sample_form = trans.sa_session.query( trans.model.FormDefinition ).get( trans.security.decode_id( sample_form_id ) )
        data_dir = util.restore_text( params.get( 'data_dir', ''  ) )
        data_dir = self.__check_path( data_dir )
        # Data transfer info - Make sure password is retrieved from kwd rather than Params
        # since Params may have munged the characters.
        datatx_info = dict( host=util.restore_text( params.get( 'host', ''  ) ),
                            username=util.restore_text( params.get( 'username', ''  ) ),
                            password=kwd.get( 'password', '' ),
                            data_dir=data_dir,
                            rename_dataset=util.restore_text( params.get( 'rename_dataset', '' ) ) )
        request_type = trans.model.RequestType( name=name, desc=desc, request_form=request_form, sample_form=sample_form, datatx_info=datatx_info ) 
        trans.sa_session.add( request_type )
        trans.sa_session.flush()
        # set sample states
        ss_list = trans.sa_session.query( trans.model.SampleState ) \
                                  .filter( trans.model.SampleState.table.c.request_type_id == request_type.id )
        for ss in ss_list:
            trans.sa_session.delete( ss )
            trans.sa_session.flush()
        i = 0
        while True:
            if kwd.has_key( 'state_name_%i' % i ):
                name = util.restore_text( params.get( 'state_name_%i' % i, None ) )
                desc = util.restore_text( params.get( 'state_desc_%i' % i, None ) )
                ss = trans.model.SampleState( name, desc, request_type ) 
                trans.sa_session.add( ss )
                trans.sa_session.flush()
                i = i + 1
            else:
                break
        message = "The new sequencer configuration named (%s) with %s states has been created" % ( request_type.name, i )
        return request_type, message
    @web.expose
    @web.require_admin
    def view_request_type( self, trans, **kwd ):
        request_type_id = kwd.get( 'id', None )
        try:
            request_type = trans.sa_session.query( trans.model.RequestType ).get( trans.security.decode_id( request_type_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', request_type_id, action='browse_request_types' )
        forms = self.get_all_forms( trans )
        rename_dataset_select_field = self.__build_rename_dataset_select_field( trans, request_type )
        return trans.fill_template( '/admin/requests/view_request_type.mako', 
                                    request_type=request_type,
                                    forms=forms,
                                    rename_dataset_select_field=rename_dataset_select_field )
    @web.expose
    @web.require_admin
    def view_form_definition( self, trans, **kwd ):
        form_definition_id = kwd.get( 'id', None )
        try:
            form_definition = trans.sa_session.query( trans.model.FormDefinition ).get( trans.security.decode_id( form_definition_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', form_definition_id, action='browse_request_types' )
        return trans.fill_template( '/admin/forms/show_form_read_only.mako',
                                    form_definition=form_definition )
    @web.expose
    @web.require_admin
    def delete_request_type( self, trans, **kwd ):
        rt_id = kwd.get( 'id', '' )
        rt_id_list = util.listify( rt_id )
        for rt_id in rt_id_list:
            try:
                request_type = trans.sa_session.query( trans.model.RequestType ).get( trans.security.decode_id( rt_id ) )
            except:
                return invalid_id_redirect( trans, 'requests_admin', rt_id, action='browse_request_types' )
            request_type.deleted = True
            trans.sa_session.add( request_type )
            trans.sa_session.flush()
        status = 'done'
        message = '%i sequencer configurations has been deleted' % len( rt_id_list )
        return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                          action='browse_request_types',
                                                          message=message,
                                                          status='done' ) )
    @web.expose
    @web.require_admin
    def undelete_request_type( self, trans, **kwd ):
        rt_id = kwd.get( 'id', '' )
        rt_id_list = util.listify( rt_id )
        for rt_id in rt_id_list:
            try:
                request_type = trans.sa_session.query( trans.model.RequestType ).get( trans.security.decode_id( rt_id ) )
            except:
                return invalid_id_redirect( trans, 'requests_admin', rt_id, action='browse_request_types' )
            request_type.deleted = False
            trans.sa_session.add( request_type )
            trans.sa_session.flush()
        status = 'done'
        message = '%i sequencer configurations have been undeleted' % len( rt_id_list )
        return trans.response.send_redirect( web.url_for( controller='requests_admin',
                                                          action='browse_request_types',
                                                          message=message,
                                                          status=status ) )
    @web.expose
    @web.require_admin
    def request_type_permissions( self, trans, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        request_type_id = kwd.get( 'id', '' )
        try:
            request_type = trans.sa_session.query( trans.model.RequestType ).get( trans.security.decode_id( request_type_id ) )
        except:
            return invalid_id_redirect( trans, 'requests_admin', request_type_id, action='browse_request_types' )
        roles = trans.sa_session.query( trans.model.Role ) \
                                .filter( trans.model.Role.table.c.deleted==False ) \
                                .order_by( trans.model.Role.table.c.name )
        if params.get( 'update_roles_button', False ):
            permissions = {}
            for k, v in trans.model.RequestType.permitted_actions.items():
                in_roles = [ trans.sa_session.query( trans.model.Role ).get( x ) for x in util.listify( params.get( k + '_in', [] ) ) ]
                permissions[ trans.app.security_agent.get_action( v.action ) ] = in_roles
            trans.app.security_agent.set_request_type_permissions( request_type, permissions )
            trans.sa_session.refresh( request_type )
            message = "Permissions updated for sequencer configuration '%s'" % request_type.name
        return trans.fill_template( '/admin/requests/request_type_permissions.mako',
                                    request_type=request_type,
                                    roles=roles,
                                    status=status,
                                    message=message )
    # ===== Methods for building SelectFields used on various admin_requests forms
    def __build_sample_id_select_field( self, trans, request, selected_value ):
        return build_select_field( trans, request.samples, 'name', 'sample_id', selected_value=selected_value, refresh_on_change=False )
    def __build_rename_dataset_select_field( self, trans, request_type=None ):
        if request_type:
            selected_value = request_type.datatx_info.get( 'rename_dataset', trans.model.RequestType.rename_dataset_options.NO )
        else:
            selected_value = trans.model.RequestType.rename_dataset_options.NO
        return build_select_field( trans,
                                   objs=[ v for k, v in trans.model.RequestType.rename_dataset_options.items() ],
                                   label_attr='self',
                                   select_field_name='rename_dataset',
                                   selected_value=selected_value,
                                   refresh_on_change=False )
# ===== Methods for building SelectFields used on various admin_requests forms - used outside this controller =====
def build_rename_datasets_for_sample_select_field( trans, sample_dataset, selected_value='none' ):
    options = []
    for option_index, option in enumerate( sample_dataset.file_path.split( os.sep )[ :-1 ] ):
        option = option.strip()
        if option:
           options.append( option )
    return build_select_field( trans,
                               objs=options,
                               label_attr='self',
                               select_field_name='rename_datasets_for_sample_%s' % trans.security.encode_id( sample_dataset.id ),
                               selected_value=selected_value,
                               refresh_on_change=False )
