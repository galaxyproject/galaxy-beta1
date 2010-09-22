import pkg_resources
pkg_resources.require( "twill==0.9" )

import StringIO, os, sys, random, filecmp, time, unittest, urllib, logging, difflib, tarfile, zipfile, tempfile, re, shutil
from itertools import *

import twill
import twill.commands as tc
from twill.other_packages._mechanize_dist import ClientForm
pkg_resources.require( "elementtree" )
from elementtree import ElementTree
from galaxy.web import security
from galaxy.web.framework.helpers import iff

buffer = StringIO.StringIO()

#Force twill to log to a buffer -- FIXME: Should this go to stdout and be captured by nose?
twill.set_output(buffer)
tc.config('use_tidy', 0)

# Dial ClientCookie logging down (very noisy)
logging.getLogger( "ClientCookie.cookies" ).setLevel( logging.WARNING )
log = logging.getLogger( __name__ )

class TwillTestCase( unittest.TestCase ):

    def setUp( self ):
        # Security helper
        self.security = security.SecurityHelper( id_secret='changethisinproductiontoo' )
        self.history_id = os.environ.get( 'GALAXY_TEST_HISTORY_ID', None )
        self.host = os.environ.get( 'GALAXY_TEST_HOST' )
        self.port = os.environ.get( 'GALAXY_TEST_PORT' )
        self.url = "http://%s:%s" % ( self.host, self.port )
        self.file_dir = os.environ.get( 'GALAXY_TEST_FILE_DIR' )
        self.home()
        #self.set_history()

    # Functions associated with files
    def files_diff( self, file1, file2, attributes=None ):
        """Checks the contents of 2 files for differences"""
        def get_lines_diff( diff ):
            count = 0
            for line in diff:
                if ( line.startswith( '+' ) and not line.startswith( '+++' ) ) or ( line.startswith( '-' ) and not line.startswith( '---' ) ):
                    count += 1
            return count
        if not filecmp.cmp( file1, file2 ):
            files_differ = False
            local_file = open( file1, 'U' ).readlines()
            history_data = open( file2, 'U' ).readlines()
            if attributes is None:
                attributes = {}
            if attributes.get( 'sort', False ):
                history_data.sort()
            ##Why even bother with the check loop below, why not just use the diff output? This seems wasteful.
            if len( local_file ) == len( history_data ):
                for i in range( len( history_data ) ):
                    if local_file[i].rstrip( '\r\n' ) != history_data[i].rstrip( '\r\n' ):
                        files_differ = True
                        break
            else:
                files_differ = True
            if files_differ:
                allowed_diff_count = int(attributes.get( 'lines_diff', 0 ))
                diff = list( difflib.unified_diff( local_file, history_data, "local_file", "history_data" ) )
                diff_lines = get_lines_diff( diff )
                log.debug('## files diff on %s and %s lines_diff=%d, found diff = %d' % (file1,file2,allowed_diff_count,diff_lines))
                if diff_lines > allowed_diff_count:
                    diff_slice = diff[0:40]
                    #FIXME: This pdf stuff is rather special cased and has not been updated to consider lines_diff 
                    #due to unknown desired behavior when used in conjunction with a non-zero lines_diff
                    #PDF forgiveness can probably be handled better by not special casing by __extension__ here
                    #and instead using lines_diff or a regular expression matching
                    #or by creating and using a specialized pdf comparison function
                    if file1.endswith( '.pdf' ) or file2.endswith( '.pdf' ):
                        # PDF files contain creation dates, modification dates, ids and descriptions that change with each
                        # new file, so we need to handle these differences.  As long as the rest of the PDF file does
                        # not differ we're ok.
                        valid_diff_strs = [ 'description', 'createdate', 'creationdate', 'moddate', 'id', 'producer', 'creator' ]
                        valid_diff = False
                        for line in diff_slice:
                            # Make sure to lower case strings before checking.
                            line = line.lower()
                            # Diff lines will always start with a + or - character, but handle special cases: '--- local_file \n', '+++ history_data \n'
                            if ( line.startswith( '+' ) or line.startswith( '-' ) ) and line.find( 'local_file' ) < 0 and line.find( 'history_data' ) < 0:
                                for vdf in valid_diff_strs:
                                    if line.find( vdf ) < 0:
                                        valid_diff = False
                                    else:
                                        valid_diff = True
                                        # Stop checking as soon as we know we have a valid difference
                                        break
                                if not valid_diff:
                                    # Print out diff_slice so we can see what failed
                                    print "###### diff_slice ######"
                                    raise AssertionError( "".join( diff_slice ) )
                    else:
                        for line in diff_slice:
                            for char in line:
                                if ord( char ) > 128:
                                    raise AssertionError( "Binary data detected, not displaying diff" )
                        raise AssertionError( "".join( diff_slice )  )

    def files_re_match( self, file1, file2, attributes=None ):
        """Checks the contents of 2 files for differences using re.match"""
        local_file = open( file1, 'U' ).readlines() #regex file
        history_data = open( file2, 'U' ).readlines()
        assert len( local_file ) == len( history_data ), 'Data File and Regular Expression File contain a different number of lines (%s != %s)' % ( len( local_file ), len( history_data ) )
        if attributes is None:
            attributes = {}
        if attributes.get( 'sort', False ):
            history_data.sort()
        lines_diff = int(attributes.get( 'lines_diff', 0 ))
        line_diff_count = 0
        diffs = []
        for i in range( len( history_data ) ):
            if not re.match( local_file[i].rstrip( '\r\n' ), history_data[i].rstrip( '\r\n' ) ):
                line_diff_count += 1
                diffs.append( 'Regular Expression: %s\nData file         : %s' % ( local_file[i].rstrip( '\r\n' ),  history_data[i].rstrip( '\r\n' ) ) )
            if line_diff_count > lines_diff:
                raise AssertionError, "Regular expression did not match data file (allowed variants=%i):\n%s" % ( lines_diff, "".join( diffs ) )

    def files_re_match_multiline( self, file1, file2, attributes=None ):
        """Checks the contents of 2 files for differences using re.match in multiline mode"""
        local_file = open( file1, 'U' ).read() #regex file
        if attributes is None:
            attributes = {}
        if attributes.get( 'sort', False ):
            history_data = open( file2, 'U' ).readlines()
            history_data.sort()
            history_data = ''.join( history_data )
        else:
            history_data = open( file2, 'U' ).read()
        #lines_diff not applicable to multiline matching
        assert re.match( local_file, history_data, re.MULTILINE ), "Multiline Regular expression did not match data file"

    def get_filename( self, filename ):
        full = os.path.join( self.file_dir, filename)
        return os.path.abspath(full)

    def save_log( *path ):
        """Saves the log to a file"""
        filename = os.path.join( *path )
        file(filename, 'wt').write(buffer.getvalue())

    def upload_file( self, filename, ftype='auto', dbkey='unspecified (?)', space_to_tab = False, metadata = None, composite_data = None ):
        """Uploads a file"""
        self.visit_url( "%s/tool_runner?tool_id=upload1" % self.url )
        try: 
            self.refresh_form( "file_type", ftype ) #Refresh, to support composite files
            tc.fv("1","dbkey", dbkey)
            if metadata:
                for elem in metadata:
                    tc.fv( "1", "files_metadata|%s" % elem.get( 'name' ), elem.get( 'value' ) )
            if composite_data:
                for i, composite_file in enumerate( composite_data ):
                    filename = self.get_filename( composite_file.get( 'value' ) )
                    tc.formfile( "1", "files_%i|file_data" % i, filename )
                    tc.fv( "1", "files_%i|space_to_tab" % i, composite_file.get( 'space_to_tab', False ) )
            else:
                filename = self.get_filename( filename )
                tc.formfile( "1", "file_data", filename )
                tc.fv( "1", "space_to_tab", space_to_tab )
            tc.submit("runtool_btn")
            self.home()
        except AssertionError, err:
            errmsg = "Uploading file resulted in the following exception.  Make sure the file (%s) exists.  " % filename
            errmsg += str( err )
            raise AssertionError( errmsg )
        # Make sure every history item has a valid hid
        hids = self.get_hids_in_history()
        for hid in hids:
            try:
                valid_hid = int( hid )
            except:
                raise AssertionError, "Invalid hid (%s) created when uploading file %s" % ( hid, filename )
        # Wait for upload processing to finish (TODO: this should be done in each test case instead)
        self.wait()
    def upload_url_paste( self, url_paste, ftype='auto', dbkey='unspecified (?)' ):
        """Pasted data in the upload utility"""
        self.visit_page( "tool_runner/index?tool_id=upload1" )
        try: 
            tc.fv( "1", "file_type", ftype )
            tc.fv( "1", "dbkey", dbkey )
            tc.fv( "1", "url_paste", url_paste )
            tc.submit( "runtool_btn" )
            self.home()
        except Exception, e:
            errmsg = "Problem executing upload utility using url_paste: %s" % str( e )
            raise AssertionError( e )
        # Make sure every history item has a valid hid
        hids = self.get_hids_in_history()
        for hid in hids:
            try:
                valid_hid = int( hid )
            except:
                raise AssertionError, "Invalid hid (%s) created when pasting %s" % ( hid, url_paste )
        # Wait for upload processing to finish (TODO: this should be done in each test case instead)
        self.wait()

    # Functions associated with histories
    def check_history_for_errors( self ):
        """Raises an exception if there are errors in a history"""
        self.home()
        self.visit_page( "history" )
        page = self.last_page()
        if page.find( 'error' ) > -1:
            raise AssertionError('Errors in the history for user %s' % self.user )
    def check_history_for_string( self, patt, show_deleted=False ):
        """Looks for 'string' in history page"""
        self.home()
        if show_deleted:
            self.visit_page( "history?show_deleted=True" )
        else:
            self.visit_page( "history" )
        for subpatt in patt.split():
            tc.find(subpatt)
        self.home()
    def clear_history( self ):
        """Empties a history of all datasets"""
        self.visit_page( "clear_history" )
        self.check_history_for_string( 'Your history is empty' )
        self.home()
    def delete_history( self, id ):
        """Deletes one or more histories"""
        history_list = self.get_histories_as_data_list()
        self.assertTrue( history_list )
        num_deleted = len( id.split( ',' ) )
        self.home()
        self.visit_page( "history/list?operation=delete&id=%s" % ( id ) )
        check_str = 'Deleted %d %s' % ( num_deleted, iff( num_deleted != 1, "histories", "history" ) )
        self.check_page_for_string( check_str )
        self.home()
    def delete_current_history( self, strings_displayed=[] ):
        """Deletes the current history"""
        self.home()
        self.visit_page( "history/delete_current" )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def get_histories_as_data_list( self ):
        """Returns the data elements of all histories"""
        tree = self.histories_as_xml_tree()
        data_list = [ elem for elem in tree.findall("data") ]
        return data_list
    def get_history_as_data_list( self, show_deleted=False ):
        """Returns the data elements of a history"""
        tree = self.history_as_xml_tree( show_deleted=show_deleted )
        data_list = [ elem for elem in tree.findall("data") ]
        return data_list
    def history_as_xml_tree( self, show_deleted=False ):
        """Returns a parsed xml object of a history"""
        self.home()
        self.visit_page( 'history?as_xml=True&show_deleted=%s' % show_deleted )
        xml = self.last_page()
        tree = ElementTree.fromstring(xml)
        return tree
    def histories_as_xml_tree( self ):
        """Returns a parsed xml object of all histories"""
        self.home()
        self.visit_page( 'history/list_as_xml' )
        xml = self.last_page()
        tree = ElementTree.fromstring(xml)
        return tree
    def history_options( self, user=False, active_datasets=False, activatable_datasets=False, histories_shared_by_others=False ):
        """Mimics user clicking on history options link"""
        self.home()
        self.visit_page( "root/history_options" )
        if user:
            self.check_page_for_string( 'Previously</a> stored histories' )
            if active_datasets:
                self.check_page_for_string( 'Create</a> a new empty history' )
                self.check_page_for_string( 'Construct workflow</a> from current history' )
                self.check_page_for_string( 'Clone</a> current history' ) 
            self.check_page_for_string( 'Share</a> current history' )
            self.check_page_for_string( 'Change default permissions</a> for current history' )
            if histories_shared_by_others:
                self.check_page_for_string( 'Histories</a> shared with you by others' )
        if activatable_datasets:
            self.check_page_for_string( 'Show deleted</a> datasets in current history' )
        self.check_page_for_string( 'Rename</a> current history' )
        self.check_page_for_string( 'Delete</a> current history' )
        self.home()
    def new_history( self, name=None ):
        """Creates a new, empty history"""
        self.home()
        if name:
            self.visit_url( "%s/history_new?name=%s" % ( self.url, name ) )
        else:
            self.visit_url( "%s/history_new" % self.url )
        self.check_history_for_string('Your history is empty')
        self.home()
    def rename_history( self, id, old_name, new_name ):
        """Rename an existing history"""
        self.home()
        self.visit_page( "history/rename?id=%s&name=%s" %( id, new_name ) )
        check_str = 'History: %s renamed to: %s' % ( old_name, urllib.unquote( new_name ) )
        self.check_page_for_string( check_str )
        self.home()
    def set_history( self ):
        """Sets the history (stores the cookies for this run)"""
        if self.history_id:
            self.home()
            self.visit_page( "history?id=%s" % self.history_id )
        else:
            self.new_history()
        self.home()
    def share_current_history( self, email, strings_displayed=[], strings_displayed_after_submit=[],
                               action='', action_strings_displayed=[], action_strings_displayed_after_submit=[] ):
        """Share the current history with different users"""
        self.visit_url( "%s/history/share" % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( 'share', 'email', email )
        tc.submit( 'share_button' )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        if action:
            # If we have an action, then we are sharing datasets with users that do not have access permissions on them
            for check_str in action_strings_displayed:
                self.check_page_for_string( check_str )
            tc.fv( 'share_restricted', 'action', action )
            tc.submit( "share_restricted_button" )
            for check_str in action_strings_displayed_after_submit:
                self.check_page_for_string( check_str )
        self.home()
    def share_histories_with_users( self, ids, emails, strings_displayed=[], strings_displayed_after_submit=[],
                                    action=None, action_strings_displayed=[] ):
        """Share one or more histories with one or more different users"""
        self.visit_url( "%s/history/list?id=%s&operation=Share" % ( self.url, ids ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( 'share', 'email', emails )
        tc.submit( 'share_button' )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        if action:
            # If we have an action, then we are sharing datasets with users that do not have access permissions on them
            tc.fv( 'share_restricted', 'action', action )
            tc.submit( "share_restricted_button" )
            for check_str in action_strings_displayed:
                self.check_page_for_string( check_str )
        self.home()
    def unshare_history( self, history_id, user_id, strings_displayed=[] ):
        """Unshare a history that has been shared with another user"""
        self.visit_url( "%s/history/list?id=%s&operation=share+or+publish" % ( self.url, history_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.visit_url( "%s/history/sharing?unshare_user=%s&id=%s" % ( self.url, user_id, history_id ) )
        self.home()
    def switch_history( self, id='', name='' ):
        """Switches to a history in the current list of histories"""
        self.visit_url( "%s/history/list?operation=switch&id=%s" % ( self.url, id ) )
        if name:
            self.check_history_for_string( name )
        self.home()
    def view_stored_active_histories( self, strings_displayed=[] ):
        self.home()
        self.visit_page( "history/list" )
        self.check_page_for_string( 'Saved Histories' )
        self.check_page_for_string( '<input type="checkbox" name="id" value=' )
        self.check_page_for_string( 'operation=Rename' )
        self.check_page_for_string( 'operation=Switch' )
        self.check_page_for_string( 'operation=Delete' )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def view_stored_deleted_histories( self, strings_displayed=[] ):
        self.home()
        self.visit_page( "history/list?f-deleted=True" )
        self.check_page_for_string( 'Saved Histories' )
        self.check_page_for_string( '<input type="checkbox" name="id" value=' )
        self.check_page_for_string( 'operation=Undelete' )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def view_shared_histories( self, strings_displayed=[] ):
        self.home()
        self.visit_page( "history/list_shared" )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def clone_history( self, history_id, clone_choice, strings_displayed=[], strings_displayed_after_submit=[] ):
        self.home()
        self.visit_page( "history/clone?id=%s" % history_id )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( '1', 'clone_choice', clone_choice )
        tc.submit( 'clone_choice_button' )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def make_accessible_via_link( self, history_id, strings_displayed=[], strings_displayed_after_submit=[] ):
        self.home()
        self.visit_page( "history/list?operation=share+or+publish&id=%s" % history_id )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        # twill barfs on this form, possibly because it contains no fields, but not sure.
        # In any case, we have to mimic the form submission
        self.home()
        self.visit_page( 'history/sharing?id=%s&make_accessible_via_link=True' % history_id )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def disable_access_via_link( self, history_id, strings_displayed=[], strings_displayed_after_submit=[] ):
        self.home()
        self.visit_page( "history/list?operation=share+or+publish&id=%s" % history_id )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        # twill barfs on this form, possibly because it contains no fields, but not sure.
        # In any case, we have to mimic the form submission
        self.home()
        self.visit_page( 'history/sharing?id=%s&disable_link_access=True' % history_id )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def import_history_via_url( self, history_id, email, strings_displayed_after_submit=[] ):
        self.home()
        self.visit_page( "history/imp?&id=%s" % history_id )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()

    # Functions associated with datasets (history items) and meta data
    def get_job_stderr( self, id ):
        self.visit_page( "dataset/stderr?id=%s" % id )
        return self.last_page()

    def _assert_dataset_state( self, elem, state ):
        if elem.get( 'state' ) != state:
            errmsg = "Expecting dataset state '%s', but state is '%s'. Dataset blurb: %s\n\n" % ( state, elem.get('state'), elem.text.strip() )
            errmsg += "---------------------- >> begin tool stderr << -----------------------\n"
            errmsg += self.get_job_stderr( elem.get( 'id' ) ) + "\n"
            errmsg += "----------------------- >> end tool stderr << ------------------------\n"
            raise AssertionError( errmsg )

    def check_metadata_for_string( self, patt, hid=None ):
        """Looks for 'patt' in the edit page when editing a dataset"""
        data_list = self.get_history_as_data_list()
        self.assertTrue( data_list )
        if hid is None: # take last hid
            elem = data_list[-1]
            hid = int( elem.get('hid') )
        self.assertTrue( hid )
        self.visit_page( "edit?hid=%s" % hid )
        for subpatt in patt.split():
            tc.find(subpatt)
    def delete_history_item( self, hda_id, strings_displayed=[] ):
        """Deletes an item from a history"""
        try:
            hda_id = int( hda_id )
        except:
            raise AssertionError, "Invalid hda_id '%s' - must be int" % hda_id
        self.visit_url( "%s/root/delete?show_deleted_on_refresh=False&id=%s" % ( self.url, hda_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def undelete_history_item( self, hda_id, strings_displayed=[] ):
        """Un-deletes a deleted item in a history"""
        try:
            hda_id = int( hda_id )
        except:
            raise AssertionError, "Invalid hda_id '%s' - must be int" % hda_id
        self.visit_url( "%s/dataset/undelete?id=%s" % ( self.url, hda_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def display_history_item( self, hda_id, strings_displayed=[] ):
        """Displays a history item - simulates eye icon click"""
        self.visit_url( '%s/datasets/%s/display/' % ( self.url, self.security.encode_id( hda_id ) ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def view_history( self, history_id, strings_displayed=[] ):
        """Displays a history for viewing"""
        self.visit_url( '%s/history/view?id=%s' % ( self.url, self.security.encode_id( history_id ) ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def edit_hda_attribute_info( self, hda_id, new_name='', new_info='', new_dbkey='', new_startcol='',
                                 strings_displayed=[], strings_not_displayed=[] ):
        """Edit history_dataset_association attribute information"""
        self.home()
        self.visit_url( "%s/root/edit?id=%s" % ( self.url, hda_id ) )
        submit_required = False
        self.check_page_for_string( 'Edit Attributes' )
        if new_name:
            tc.fv( 'edit_attributes', 'name', new_name )
            submit_required = True
        if new_info:
            tc.fv( 'edit_attributes', 'info', new_info )
            submit_required = True
        if new_dbkey:
            tc.fv( 'edit_attributes', 'dbkey', new_dbkey )
            submit_required = True
        if new_startcol:
            tc.fv( 'edit_attributes', 'startCol', new_startcol )
            submit_required = True
        if submit_required:
            tc.submit( 'save' )
            self.check_page_for_string( 'Attributes updated' )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) incorrectly displayed on Edit Attributes page." % check_str
            except:
                pass
        self.home()
    def check_hda_attribute_info( self, hda_id, strings_displayed=[] ):
        """Edit history_dataset_association attribute information"""
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def auto_detect_metadata( self, hda_id ):
        """Auto-detect history_dataset_association metadata"""
        self.home()
        self.visit_url( "%s/root/edit?id=%s" % ( self.url, hda_id ) )
        self.check_page_for_string( 'This will inspect the dataset and attempt' )
        tc.fv( 'auto_detect', 'id', hda_id )
        tc.submit( 'detect' )
        try:
            self.check_page_for_string( 'Attributes have been queued to be updated' )
            self.wait()
        except AssertionError:
            self.check_page_for_string( 'Attributes updated' )
        #self.check_page_for_string( 'Attributes updated' )
        self.home()
    def convert_format( self, hda_id, target_type ):
        """Convert format of history_dataset_association"""
        self.home()
        self.visit_url( "%s/root/edit?id=%s" % ( self.url, hda_id ) )
        self.check_page_for_string( 'This will inspect the dataset and attempt' )
        tc.fv( 'convert_data', 'target_type', target_type )
        tc.submit( 'convert_data' )
        self.check_page_for_string( 'The file conversion of Convert BED to GFF on data' )
        self.wait() #wait for the format convert tool to finish before returning
        self.home()
    def change_datatype( self, hda_id, datatype ):
        """Change format of history_dataset_association"""
        self.home()
        self.visit_url( "%s/root/edit?id=%s" % ( self.url, hda_id ) )
        self.check_page_for_string( 'This will change the datatype of the existing dataset but' )
        tc.fv( 'change_datatype', 'datatype', datatype )
        tc.submit( 'change' )
        self.check_page_for_string( 'Changed the type of dataset' )
        self.home()
    def copy_history_item( self, source_dataset_ids='', target_history_ids=[], all_target_history_ids=[],
                           deleted_history_ids=[] ):
        """Copy 1 or more history_dataset_associations to 1 or more histories"""
        self.home()
        self.visit_url( "%s/dataset/copy_datasets?source_dataset_ids=%s" % ( self.url, source_dataset_ids ) )
        self.check_page_for_string( 'Source History Items' )
        # Make sure all of users active histories are displayed
        for id in all_target_history_ids:
            self.check_page_for_string( id )
        # Make sure only active histories are displayed
        for id in deleted_history_ids:
            try:
                self.check_page_for_string( id )
                raise AssertionError, "deleted history id %d displayed in list of target histories" % id
            except:
                pass
        # Check each history to which we want to copy the item
        for id in target_history_ids:
            tc.fv( '1', 'target_history_ids', id )
        tc.submit( 'do_copy' )
        no_source_ids = len( source_dataset_ids.split( ',' ) )
        check_str = '%d datasets copied to %d histories.' % ( no_source_ids, len( target_history_ids ) )
        self.check_page_for_string( check_str )
        self.home()
    def get_hids_in_history( self ):
        """Returns the list of hid values for items in a history"""
        data_list = self.get_history_as_data_list()
        hids = []
        for elem in data_list:
            hid = elem.get('hid')
            hids.append(hid)
        return hids
    def get_hids_in_histories( self ):
        """Returns the list of hids values for items in all histories"""
        data_list = self.get_histories_as_data_list()
        hids = []
        for elem in data_list:
            hid = elem.get('hid')
            hids.append(hid)
        return hids

    def makeTfname(self, fname=None):
	"""
        safe temp name - preserve the file extension for tools that interpret it
	"""
        suffix = os.path.split(fname)[-1] # ignore full path
	fd,temp_prefix = tempfile.mkstemp(prefix='tmp',suffix=suffix)
	return temp_prefix


    def verify_dataset_correctness( self, filename, hid=None, wait=True, maxseconds=120, attributes=None ):
        """Verifies that the attributes and contents of a history item meet expectations"""
        if wait:
            self.wait( maxseconds=maxseconds ) #wait for job to finish
        data_list = self.get_history_as_data_list()
        self.assertTrue( data_list )
        if hid is None: # take last hid
            elem = data_list[-1]
            hid = str( elem.get('hid') )
        else:
            hid = str( hid )
            elems = [ elem for elem in data_list if elem.get('hid') == hid ]
            self.assertTrue( len(elems) == 1 )
            elem = elems[0]
        self.assertTrue( hid )
        self._assert_dataset_state( elem, 'ok' )
        if self.is_zipped( filename ):
            errmsg = 'History item %s is a zip archive which includes invalid files:\n' % hid
            zip_file = zipfile.ZipFile( filename, "r" )
            name = zip_file.namelist()[0]
            test_ext = name.split( "." )[1].strip().lower()
            if not ( test_ext == 'scf' or test_ext == 'ab1' or test_ext == 'txt' ):
                raise AssertionError( errmsg )
            for name in zip_file.namelist():
                ext = name.split( "." )[1].strip().lower()
                if ext != test_ext:
                    raise AssertionError( errmsg )
        else:
            local_name = self.get_filename( filename )
            temp_name = self.makeTfname(fname = filename)
            self.home()
            self.visit_page( "display?hid=" + hid )
            data = self.last_page()
            file( temp_name, 'wb' ).write(data)
            try:
                # have to nest try-except in try-finally to handle 2.4
                try:
                    if attributes is None:
                        attributes = {}
                    compare = attributes.get( 'compare', 'diff' )
                    extra_files = attributes.get( 'extra_files', None )
                    if compare == 'diff':
                        self.files_diff( local_name, temp_name, attributes=attributes )
                    elif compare == 're_match':
                        self.files_re_match( local_name, temp_name, attributes=attributes )
                    elif compare == 're_match_multiline':
                        self.files_re_match_multiline( local_name, temp_name, attributes=attributes )
    	            elif compare == 'sim_size':
    	                delta = attributes.get('delta','100')
    	                s1 = len(data)
    	                s2 = os.path.getsize(local_name)
    	                if abs(s1-s2) > int(delta):
    	                   raise Exception, 'Files %s=%db but %s=%db - compare (delta=%s) failed' % (temp_name,s1,local_name,s2,delta)
                        else:
                            raise Exception, 'Unimplemented Compare type: %s' % compare
                        if extra_files:
                            self.verify_extra_files_content( extra_files, elem.get( 'id' ) )
                except AssertionError, err:
                    errmsg = 'History item %s different than expected, difference (using %s):\n' % ( hid, compare )
                    errmsg += str( err )
                    raise AssertionError( errmsg )
            finally:
                os.remove( temp_name )

    def verify_extra_files_content( self, extra_files, hda_id ):
        files_list = []
        for extra_type, extra_value, extra_name, extra_attributes in extra_files:
            if extra_type == 'file':
                files_list.append( ( extra_name, extra_value, extra_attributes ) )
            elif extra_type == 'directory':
                for filename in os.listdir( self.get_filename( extra_value ) ):
                    files_list.append( ( filename, os.path.join( extra_value, filename ), extra_attributes ) )
            else:
                raise ValueError, 'unknown extra_files type: %s' % extra_type
        for filename, filepath, attributes in files_list:
            self.verify_composite_datatype_file_content( filepath, hda_id, base_name = filename, attributes = attributes )
        
    def verify_composite_datatype_file_content( self, file_name, hda_id, base_name = None, attributes = None ):
        local_name = self.get_filename( file_name )
        if base_name is None:
            base_name = os.path.split(file_name)[-1]
        temp_name = self.makeTfname(fname = base_name)
        self.visit_url( "%s/datasets/%s/display/%s" % ( self.url, self.security.encode_id( hda_id ), base_name ) )
        data = self.last_page()
        file( temp_name, 'wb' ).write( data )
        try:
            # have to nest try-except in try-finally to handle 2.4
            try:
                if attributes is None:
                    attributes = {}
                compare = attributes.get( 'compare', 'diff' )
                if compare == 'diff':
                    self.files_diff( local_name, temp_name, attributes=attributes )
                elif compare == 're_match':
                    self.files_re_match( local_name, temp_name, attributes=attributes )
                elif compare == 're_match_multiline':
                    self.files_re_match_multiline( local_name, temp_name, attributes=attributes )
                elif compare == 'sim_size':
                    delta = attributes.get('delta','100')
                    s1 = len(data)
                    s2 = os.path.getsize(local_name)
                    if abs(s1-s2) > int(delta):
                       raise Exception, 'Files %s=%db but %s=%db - compare (delta=%s) failed' % (temp_name,s1,local_name,s2,delta)
                else:
                    raise Exception, 'Unimplemented Compare type: %s' % compare
            except AssertionError, err:
                errmsg = 'Composite file (%s) of History item %s different than expected, difference (using %s):\n' % ( base_name, hda_id, compare )
                errmsg += str( err )
                raise AssertionError( errmsg )
        finally:
	    os.remove( temp_name )

    def is_zipped( self, filename ):
        if not zipfile.is_zipfile( filename ):
            return False
        return True

    def is_binary( self, filename ):
        temp = open( filename, "U" ) # why is this not filename? Where did temp_name come from
        lineno = 0
        for line in temp:
            lineno += 1
            line = line.strip()
            if line:
                for char in line:
                    if ord( char ) > 128:
                        return True
            if lineno > 10:
                break
        return False

    def verify_genome_build( self, dbkey='hg17' ):
        """Verifies that the last used genome_build at history id 'hid' is as expected"""
        data_list = self.get_history_as_data_list()
        self.assertTrue( data_list )
        elems = [ elem for elem in data_list ]
        elem = elems[-1]
        genome_build = elem.get('dbkey')
        self.assertTrue( genome_build == dbkey )

    # Functions associated with user accounts
    def create( self, email='test@bx.psu.edu', password='testuser', username='admin-user', webapp='galaxy', referer='' ):
        # HACK: don't use panels because late_javascripts() messes up the twill browser and it 
        # can't find form fields (and hence user can't be logged in).
        self.visit_url( "%s/user/create?use_panels=False" % self.url )
        tc.fv( '1', 'email', email )
        tc.fv( '1', 'webapp', webapp )
        tc.fv( '1', 'referer', referer )
        tc.fv( '1', 'password', password )
        tc.fv( '1', 'confirm', password )
        tc.fv( '1', 'username', username )
        tc.submit( 'create_user_button' )
        previously_created = False
        username_taken = False
        invalid_username = False
        try:
            self.check_page_for_string( "Created new user account" )
        except:
            try:
                # May have created the account in a previous test run...
                self.check_page_for_string( "User with that email already exists" )
                previously_created = True
            except:
                try:
                    self.check_page_for_string( 'This user name is not available' )
                    username_taken = True
                except:
                    try:
                        # Note that we're only checking if the usr name is >< 4 chars here...
                        self.check_page_for_string( 'User name must be at least 4 characters in length' )
                        invalid_username = True
                    except:
                        pass
        return previously_created, username_taken, invalid_username
    def create_user_with_info( self, email, password, username, user_info_values, user_info_select='', admin_view='False',
                               strings_displayed=[], strings_displayed_after_submit=[] ):
        # This method creates a new user with associated info
        self.visit_url( "%s/user/create?admin_view=%s&use_panels=False" % ( self.url, admin_view ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str)
        tc.fv( "1", "email", email )
        tc.fv( "1", "password", password )
        tc.fv( "1", "confirm", password )
        tc.fv( "1", "username", username )
        if user_info_select:
            # The user_info_select SelectField requires a refresh_on_change
            self.refresh_form( 'user_info_select', user_info_select )
        for index, info_value in enumerate( user_info_values ):
            tc.fv( "1", "field_%i" % index, info_value )
        tc.submit( "create_user_button" )
    def edit_user_info( self, new_email='', new_username='', password='', new_password='',
                        info_values=[], strings_displayed=[], strings_displayed_after_submit=[] ):
        self.visit_url( "%s/user/show_info" % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        if new_email or new_username:
            if new_email:
                tc.fv( "login_info", "email", new_email )
            if new_username:
                tc.fv( "login_info", "username", new_username )
            tc.submit( "login_info_button" )
        if password and new_password:
            tc.fv( "change_password", "current", password )
            tc.fv( "change_password", "password", new_password )
            tc.fv( "change_password", "confirm", new_password )
            tc.submit( "change_password_button" )
        if info_values:
            for index, info_value in enumerate( info_values ):
                tc.fv( "user_info", "field_%i" % index, info_value )
            tc.submit( "edit_user_info_button" )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def user_set_default_permissions( self, permissions_out=[], permissions_in=[], role_id='2' ):
        # role.id = 2 is Private Role for test2@bx.psu.edu 
        # NOTE: Twill has a bug that requires the ~/user/permissions page to contain at least 1 option value 
        # in each select list or twill throws an exception, which is: ParseError: OPTION outside of SELECT
        # Due to this bug, we'll bypass visiting the page, and simply pass the permissions on to the 
        # /user/set_default_permissions method.
        url = "user/set_default_permissions?update_roles_button=Save&id=None"
        for po in permissions_out:
            key = '%s_out' % po
            url ="%s&%s=%s" % ( url, key, str( role_id ) )
        for pi in permissions_in:
            key = '%s_in' % pi
            url ="%s&%s=%s" % ( url, key, str( role_id ) )
        self.home()
        self.visit_url( "%s/%s" % ( self.url, url ) )
        self.last_page()
        self.check_page_for_string( 'Default new history permissions have been changed.' )
        self.home()
    def history_set_default_permissions( self, permissions_out=[], permissions_in=[], role_id=3 ): # role.id = 3 is Private Role for test3@bx.psu.edu 
        # NOTE: Twill has a bug that requires the ~/user/permissions page to contain at least 1 option value 
        # in each select list or twill throws an exception, which is: ParseError: OPTION outside of SELECT
        # Due to this bug, we'll bypass visiting the page, and simply pass the permissions on to the 
        # /user/set_default_permissions method.
        url = "root/history_set_default_permissions?update_roles_button=Save&id=None&dataset=True"
        for po in permissions_out:
            key = '%s_out' % po
            url ="%s&%s=%s" % ( url, key, str( role_id ) )
        for pi in permissions_in:
            key = '%s_in' % pi
            url ="%s&%s=%s" % ( url, key, str( role_id ) )
        self.home()
        self.visit_url( "%s/%s" % ( self.url, url ) )
        self.check_page_for_string( 'Default history permissions have been changed.' )
        self.home()
    def login( self, email='test@bx.psu.edu', password='testuser', username='admin-user', webapp='galaxy', referer='' ):
        # test@bx.psu.edu is configured as an admin user
        previously_created, username_taken, invalid_username = \
            self.create( email=email, password=password, username=username, webapp=webapp, referer=referer )
        if previously_created:
            # The acount has previously been created, so just login.
            # HACK: don't use panels because late_javascripts() messes up the twill browser and it 
            # can't find form fields (and hence user can't be logged in).
            self.visit_url( "%s/user/login?use_panels=False" % self.url )
            tc.fv( '1', 'email', email )
            tc.fv( '1', 'webapp', webapp )
            tc.fv( '1', 'referer', referer )
            tc.fv( '1', 'password', password )
            tc.submit( 'login_button' )
    def logout( self ):
        self.home()
        self.visit_page( "user/logout" )
        self.check_page_for_string( "You have been logged out" )
        self.home()
    
    # Functions associated with browsers, cookies, HTML forms and page visits
    
    def check_page_for_string( self, patt ):
        """Looks for 'patt' in the current browser page"""        
        page = self.last_page()
        for subpatt in patt.split():
            if page.find( patt ) == -1:
                fname = self.write_temp_file( page )
                errmsg = "no match to '%s'\npage content written to '%s'" % ( patt, fname )
                raise AssertionError( errmsg )
    
    def write_temp_file( self, content, suffix='.html' ):
        fd, fname = tempfile.mkstemp( suffix=suffix, prefix='twilltestcase-' )
        f = os.fdopen( fd, "w" )
        f.write( content )
        f.close()
        return fname

    def clear_cookies( self ):
        tc.clear_cookies()

    def clear_form( self, form=0 ):
        """Clears a form"""
        tc.formclear(str(form))

    def home( self ):
        self.visit_url( self.url )

    def last_page( self ):
        return tc.browser.get_html()

    def load_cookies( self, file ):
        filename = self.get_filename(file)
        tc.load_cookies(filename)

    def reload_page( self ):
        tc.reload()
        tc.code(200)

    def show_cookies( self ):
        return tc.show_cookies()

    def showforms( self ):
        """Shows form, helpful for debugging new tests"""
        return tc.showforms()

    def submit_form( self, form_no=0, button="runtool_btn", **kwd ):
        """Populates and submits a form from the keyword arguments."""
        # An HTMLForm contains a sequence of Controls.  Supported control classes are:
        # TextControl, FileControl, ListControl, RadioControl, CheckboxControl, SelectControl,
        # SubmitControl, ImageControl
        for i, f in enumerate( self.showforms() ):
            if i == form_no:
                break
        # To help with debugging a tool, print out the form controls when the test fails
        print "form '%s' contains the following controls ( note the values )" % f.name
        controls = {}
        hc_prefix = '<HiddenControl('
        for i, control in enumerate( f.controls ):
           print "control %d: %s" % ( i, str( control ) )
           if not hc_prefix in str( control ):
              try:
                #check if a repeat element needs to be added
                if control.name not in kwd and control.name.endswith( '_add' ):
                    #control name doesn't exist, could be repeat
                    repeat_startswith = control.name[0:-4]
                    if repeat_startswith and not [ c_name for c_name in controls.keys() if c_name.startswith( repeat_startswith ) ] and [ c_name for c_name in kwd.keys() if c_name.startswith( repeat_startswith ) ]:
                        tc.submit( control.name )
                        return self.submit_form( form_no=form_no, button=button, **kwd )
                # Check for refresh_on_change attribute, submit a change if required
                if hasattr( control, 'attrs' ) and 'refresh_on_change' in control.attrs.keys():
                    changed = False
                    item_labels = [ item.attrs[ 'label' ] for item in control.get_items() if item.selected ] #For DataToolParameter, control.value is the HDA id, but kwd contains the filename.  This loop gets the filename/label for the selected values.
                    for value in kwd[ control.name ]:
                        if value not in control.value and True not in [ value in item_label for item_label in item_labels ]:
                            changed = True
                            break
                    if changed:
                        # Clear Control and set to proper value
                        control.clear()
                        # kwd[control.name] should be a singlelist
                        for elem in kwd[ control.name ]:
                            tc.fv( f.name, control.name, str( elem ) )
                        # Create a new submit control, allows form to refresh, instead of going to next page
                        control = ClientForm.SubmitControl( 'SubmitControl', '___refresh_grouping___', {'name':'refresh_grouping'} )
                        control.add_to_form( f )
                        control.fixup()
                        # Submit for refresh
                        tc.submit( '___refresh_grouping___' )
                        return self.submit_form( form_no=form_no, button=button, **kwd )
              except Exception, e:
                log.debug( "In submit_form, continuing, but caught exception: %s" % str( e ) )
                continue
              controls[ control.name ] = control
        # No refresh_on_change attribute found in current form, so process as usual
        for control_name, control_value in kwd.items():
            if control_name not in controls:
                continue # these cannot be handled safely - cause the test to barf out
            if not isinstance( control_value, list ):
                control_value = [ control_value ]
            control = controls[ control_name ]
            control.clear()
            if control.is_of_kind( "text" ):
                tc.fv( f.name, control.name, ",".join( control_value ) )
            elif control.is_of_kind( "list" ):
                try:
                    if control.is_of_kind( "multilist" ):
                        if control.type == "checkbox":
                            def is_checked( value ):
                                # Copied from form_builder.CheckboxField
                                if value == True:
                                    return True
                                if isinstance( value, list ):
                                    value = value[0]
                                return isinstance( value, basestring ) and value.lower() in ( "yes", "true", "on" )
                            try:
                                checkbox = control.get()
                                checkbox.selected = is_checked( control_value )
                            except Exception, e1:
                                print "Attempting to set checkbox selected value threw exception: ", e1
                                # if there's more than one checkbox, probably should use the behaviour for
                                # ClientForm.ListControl ( see twill code ), but this works for now...
                                for elem in control_value:
                                    control.get( name=elem ).selected = True
                        else:
                            for elem in control_value:
                                control.get( name=elem ).selected = True
                    else: # control.is_of_kind( "singlelist" )
                        for elem in control_value:
                            try:
                                tc.fv( f.name, control.name, str( elem ) )
                            except Exception, e2:
                                print "Attempting to set control '", control.name, "' to value '", elem, "' threw exception: ", e2
                                # Galaxy truncates long file names in the dataset_collector in ~/parameters/basic.py
                                if len( elem ) > 30:
                                    elem_name = '%s..%s' % ( elem[:17], elem[-11:] )
                                else:
                                    elem_name = elem
                                tc.fv( f.name, control.name, str( elem_name ) )
                except Exception, exc:
                    errmsg = "Attempting to set field '%s' to value '%s' in form '%s' threw exception: %s\n" % ( control_name, str( control_value ), f.name, str( exc ) )
                    errmsg += "control: %s\n" % str( control )
                    errmsg += "If the above control is a DataToolparameter whose data type class does not include a sniff() method,\n"
                    errmsg += "make sure to include a proper 'ftype' attribute to the tag for the control within the <test> tag set.\n"
                    raise AssertionError( errmsg )
            else:
                # Add conditions for other control types here when necessary.
                pass
        tc.submit( button )
    def refresh_form( self, control_name, value, form_no=0, **kwd ):
        """Handles Galaxy's refresh_on_change for forms without ultimately submitting the form"""
        # control_name is the name of the form field that requires refresh_on_change, and value is
        # the value to which that field is being set.
        for i, f in enumerate( self.showforms() ):
            if i == form_no:
                break
        try:
            control = f.find_control( name=control_name )
        except:
            # This assumes we always want the first control of the given name, which may not be ideal...
            control = f.find_control( name=control_name, nr=0 )
        # Check for refresh_on_change attribute, submit a change if required
        if 'refresh_on_change' in control.attrs.keys():
            # Clear Control and set to proper value
            control.clear()
            tc.fv( f.name, control.name, value )
            # Create a new submit control, allows form to refresh, instead of going to next page
            control = ClientForm.SubmitControl( 'SubmitControl', '___refresh_grouping___', {'name':'refresh_grouping'} )
            control.add_to_form( f )
            control.fixup()
            # Submit for refresh
            tc.submit( '___refresh_grouping___' )
    def visit_page( self, page ):
        # tc.go("./%s" % page)
        if not page.startswith( "/" ):
            page = "/" + page 
        tc.go( self.url + page )
        tc.code( 200 )

    def visit_url( self, url ):
        tc.go("%s" % url)
        tc.code( 200 )

    """Functions associated with Galaxy tools"""
    def run_tool( self, tool_id, repeat_name=None, **kwd ):
        tool_id = tool_id.replace(" ", "+")
        """Runs the tool 'tool_id' and passes it the key/values from the *kwd"""
        self.visit_url( "%s/tool_runner/index?tool_id=%s" % (self.url, tool_id) )
        if repeat_name is not None:
            repeat_button = '%s_add' % repeat_name
            # Submit the "repeat" form button to add an input)
            tc.submit( repeat_button )
            print "button '%s' clicked" % repeat_button
        tc.find( 'runtool_btn' )
        self.submit_form( **kwd )

    def run_ucsc_main( self, track_params, output_params ):
        """Gets Data From UCSC"""
        tool_id = "ucsc_table_direct1"
        track_string = urllib.urlencode( track_params )
        galaxy_url = urllib.quote_plus( "%s/tool_runner/index?" % self.url )
        self.visit_url( "http://genome.ucsc.edu/cgi-bin/hgTables?GALAXY_URL=%s&hgta_compressType=none&tool_id=%s&%s" % ( galaxy_url, tool_id, track_string ) )
        tc.fv( "mainForm", "hgta_doTopSubmit", "get output" )
        self.submit_form( button="get output" )#, **track_params )
        tc.fv( 2, "hgta_doGalaxyQuery", "Send query to Galaxy" )
        self.submit_form( button="Send query to Galaxy" )#, **output_params ) #AssertionError: Attempting to set field 'fbQual' to value '['whole']' in form 'None' threw exception: no matching forms! control: <RadioControl(fbQual=[whole, upstreamAll, endAll])>

    def wait( self, maxseconds=120 ):
        """Waits for the tools to finish"""
        sleep_amount = 0.1
        slept = 0
        self.home()
        while slept <= maxseconds:
            self.visit_page( "history" )
            page = tc.browser.get_html()
            if page.find( '<!-- running: do not change this comment, used by TwillTestCase.wait -->' ) > -1:
                time.sleep( sleep_amount )
                slept += sleep_amount
                sleep_amount *= 2
                if slept + sleep_amount > maxseconds:
                    sleep_amount = maxseconds - slept # don't overshoot maxseconds
            else:
                break
        assert slept < maxseconds

    # Dataset Security stuff
    # Tests associated with users
    def create_new_account_as_admin( self, email='test4@bx.psu.edu', password='testuser',
                                     username='regular-user4', webapp='galaxy', referer='' ):
        """Create a new account for another user"""
        # HACK: don't use panels because late_javascripts() messes up the twill browser and it 
        # can't find form fields (and hence user can't be logged in).
        self.visit_url( "%s/user/create?admin_view=True" % self.url )
        tc.fv( '1', 'email', email )
        tc.fv( '1', 'webapp', webapp )
        tc.fv( '1', 'referer', referer )
        tc.fv( '1', 'password', password )
        tc.fv( '1', 'confirm', password )
        tc.fv( '1', 'username', username )
        tc.submit( 'create_user_button' )
        previously_created = False
        username_taken = False
        invalid_username = False
        try:
            self.check_page_for_string( "Created new user account" )
        except:
            try:
                # May have created the account in a previous test run...
                self.check_page_for_string( "User with that email already exists" )
                previously_created = True
            except:
                try:
                    self.check_page_for_string( 'This user name is not available' )
                    username_taken = True
                except:
                    try:
                        # Note that we're only checking if the usr name is >< 4 chars here...
                        self.check_page_for_string( 'User name must be at least 4 characters in length' )
                        invalid_username = True
                    except:
                        pass
        return previously_created, username_taken, invalid_username
    def reset_password_as_admin( self, user_id, password='testreset' ):
        """Reset a user password"""
        self.home()
        self.visit_url( "%s/admin/reset_user_password?id=%s" % ( self.url, user_id ) )
        tc.fv( "1", "password", password )
        tc.fv( "1", "confirm", password )
        tc.submit( "reset_user_password_button" )
        self.check_page_for_string( "Passwords reset for 1 users" )
        self.home()
    def mark_user_deleted( self, user_id, email='' ):
        """Mark a user as deleted"""
        self.home()
        self.visit_url( "%s/admin/users?operation=delete&id=%s" % ( self.url, user_id ) )
        check_str = "Deleted 1 users"
        self.check_page_for_string( check_str )
        self.home()
    def undelete_user( self, user_id, email='' ):
        """Undelete a user"""
        self.home()
        self.visit_url( "%s/admin/users?operation=undelete&id=%s" % ( self.url, user_id ) )
        check_str = "Undeleted 1 users"
        self.check_page_for_string( check_str )
        self.home()
    def purge_user( self, user_id, email ):
        """Purge a user account"""
        self.home()
        self.visit_url( "%s/admin/users?operation=purge&id=%s" % ( self.url, user_id ) )
        check_str = "Purged 1 users"
        self.check_page_for_string( check_str )
        self.home()
    def manage_roles_and_groups_for_user( self, user_id, in_role_ids=[], out_role_ids=[],
                                          in_group_ids=[], out_group_ids=[], strings_displayed=[] ):
        self.home()
        url = "%s/admin/manage_roles_and_groups_for_user?id=%s" % ( self.url, user_id )
        if in_role_ids:
            url += "&in_roles=%s" % ','.join( in_role_ids )
        if out_role_ids:
            url += "&out_roles=%s" % ','.join( out_role_ids )
        if in_group_ids:
            url += "&in_groups=%s" % ','.join( in_group_ids )
        if out_group_ids:
            url += "&out_groups=%s" % ','.join( out_group_ids )
        if in_role_ids or out_role_ids or in_group_ids or out_group_ids:
            url += "&user_roles_groups_edit_button=Save"
        self.visit_url( url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()

    # Tests associated with roles
    def browse_roles( self, strings_displayed=[] ):
        self.visit_url( '%s/admin/roles' % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def create_role( self,
                     name='Role One',
                     description="This is Role One",
                     in_user_ids=[],
                     in_group_ids=[],
                     create_group_for_role='no',
                     private_role='' ):
        """Create a new role"""
        url = "%s/admin/roles?operation=create&create_role_button=Save&name=%s&description=%s" % ( self.url, name.replace( ' ', '+' ), description.replace( ' ', '+' ) )
        if in_user_ids:
            url += "&in_users=%s" % ','.join( in_user_ids )
        if in_group_ids:
            url += "&in_groups=%s" % ','.join( in_group_ids )
        if create_group_for_role == 'yes':
            url += '&create_group_for_role=yes'
        self.home()
        self.visit_url( url )
        if create_group_for_role == 'yes':
            check_str = "Group '%s' has been created, and role '%s' has been created with %d associated users and %d associated groups" % \
                ( name, name, len( in_user_ids ), len( in_group_ids ) )
        else:
            check_str = "Role '%s' has been created with %d associated users and %d associated groups" % \
                ( name, len( in_user_ids ), len( in_group_ids ) ) 
        self.check_page_for_string( check_str )
        if private_role:
            # Make sure no private roles are displayed
            try:
                self.check_page_for_string( private_role )
                errmsg = 'Private role %s displayed on Roles page' % private_role
                raise AssertionError( errmsg )
            except AssertionError:
                # Reaching here is the behavior we want since no private roles should be displayed
                pass
        self.home()
        self.visit_url( "%s/admin/roles" % self.url )
        self.check_page_for_string( name )
        self.home()
    def rename_role( self, role_id, name='Role One Renamed', description='This is Role One Re-described' ):
        """Rename a role"""
        self.home()
        self.visit_url( "%s/admin/roles?operation=rename&id=%s" % ( self.url, role_id ) )
        self.check_page_for_string( 'Change role name and description' )
        tc.fv( "1", "name", name )
        tc.fv( "1", "description", description )
        tc.submit( "rename_role_button" )
        self.home()
    def mark_role_deleted( self, role_id, role_name ):
        """Mark a role as deleted"""
        self.home()
        self.visit_url( "%s/admin/roles?operation=delete&id=%s" % ( self.url, role_id ) )
        check_str = "Deleted 1 roles:  %s" % role_name
        self.check_page_for_string( check_str )
        self.home()
    def undelete_role( self, role_id, role_name ):
        """Undelete an existing role"""
        self.home()
        self.visit_url( "%s/admin/roles?operation=undelete&id=%s" % ( self.url, role_id ) )
        check_str = "Undeleted 1 roles:  %s" % role_name
        self.check_page_for_string( check_str )
        self.home()
    def purge_role( self, role_id, role_name ):
        """Purge an existing role"""
        self.home()
        self.visit_url( "%s/admin/roles?operation=purge&id=%s" % ( self.url, role_id ) )
        check_str = "Purged 1 roles:  %s" % role_name
        self.check_page_for_string( check_str )
        self.home()
    def associate_users_and_groups_with_role( self, role_id, role_name, user_ids=[], group_ids=[] ):
        self.home()
        url = "%s/admin/role?id=%s&role_members_edit_button=Save" % ( self.url, role_id )
        if user_ids:
            url += "&in_users=%s" % ','.join( user_ids )
        if group_ids:
            url += "&in_groups=%s" % ','.join( group_ids )
        self.visit_url( url )
        check_str = "Role '%s' has been updated with %d associated users and %d associated groups" % ( role_name, len( user_ids ), len( group_ids ) )
        self.check_page_for_string( check_str )
        self.home()

    # Tests associated with groups
    def create_group( self, name='Group One', in_user_ids=[], in_role_ids=[] ):
        """Create a new group"""
        url = "%s/admin/groups?operation=create&create_group_button=Save&name=%s" % ( self.url, name.replace( ' ', '+' ) )
        if in_user_ids:
            url += "&in_users=%s" % ','.join( in_user_ids )
        if in_role_ids:
            url += "&in_roles=%s" % ','.join( in_role_ids )
        self.home()
        self.visit_url( url )
        check_str = "Group '%s' has been created with %d associated users and %d associated roles" % ( name, len( in_user_ids ), len( in_role_ids ) ) 
        self.check_page_for_string( check_str )
        self.home()
        self.visit_url( "%s/admin/groups" % self.url )
        self.check_page_for_string( name )
        self.home()
    def browse_groups( self, strings_displayed=[] ):
        self.visit_url( '%s/admin/groups' % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def rename_group( self, group_id, name='Group One Renamed' ):
        """Rename a group"""
        self.home()
        self.visit_url( "%s/admin/groups?operation=rename&id=%s" % ( self.url, group_id ) )
        self.check_page_for_string( 'Change group name' )
        tc.fv( "1", "name", name )
        tc.submit( "rename_group_button" )
        self.home()
    def associate_users_and_roles_with_group( self, group_id, group_name, user_ids=[], role_ids=[] ):
        self.home()
        url = "%s/admin/manage_users_and_roles_for_group?id=%s&group_roles_users_edit_button=Save" % ( self.url, group_id )
        if user_ids:
            url += "&in_users=%s" % ','.join( user_ids )
        if role_ids:
            url += "&in_roles=%s" % ','.join( role_ids )
        self.visit_url( url )
        check_str = "Group '%s' has been updated with %d associated roles and %d associated users" % ( group_name, len( role_ids ), len( user_ids ) )
        self.check_page_for_string( check_str )
        self.home()
    def mark_group_deleted( self, group_id, group_name ):
        """Mark a group as deleted"""
        self.home()
        self.visit_url( "%s/admin/groups?operation=delete&id=%s" % ( self.url, group_id ) )
        check_str = "Deleted 1 groups:  %s" % group_name
        self.check_page_for_string( check_str )
        self.home()
    def undelete_group( self, group_id, group_name ):
        """Undelete an existing group"""
        self.home()
        self.visit_url( "%s/admin/groups?operation=undelete&id=%s" % ( self.url, group_id ) )
        check_str = "Undeleted 1 groups:  %s" % group_name
        self.check_page_for_string( check_str )
        self.home()
    def purge_group( self, group_id, group_name ):
        """Purge an existing group"""
        self.home()
        self.visit_url( "%s/admin/groups?operation=purge&id=%s" % ( self.url, group_id ) )
        check_str = "Purged 1 groups:  %s" % group_name
        self.check_page_for_string( check_str )
        self.home()

    # Form stuff
    def create_form( self, name, desc, form_type, field_type='TextField', form_layout_name='',
                     num_fields=1, num_options=0, strings_displayed=[], strings_displayed_after_submit=[] ):
        """Create a new form definition."""
        self.visit_url( "%s/forms/new" % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( "1", "name", name )
        tc.fv( "1", "description", desc )
        tc.fv( "1", "form_type_selectbox", form_type )
        tc.submit( "create_form_button" )
        if form_type == "Sequencing Sample Form":
            tc.submit( "add_layout_grid" )
            tc.fv( "1", "grid_layout0", form_layout_name )
        # Add fields to the new form definition
        for index1 in range( num_fields ):
            field_name = 'field_name_%i' % index1
            field_contents = field_type
            field_help_name = 'field_helptext_%i' % index1
            field_help_contents = 'Field %i help' % index1
            field_default = 'field_default_0'
            field_default_contents = '%s default contents' % form_type
            tc.fv( "1", field_name, field_contents )
            tc.fv( "1", field_help_name, field_help_contents )
            if field_type == 'SelectField':
                # SelectField field_type requires a refresh_on_change
                self.refresh_form( 'field_type_0', field_type )
                # Add options so our select list is functional
                if num_options == 0:
                    # Default to 2 options
                    num_options = 2
                for index2 in range( 1, num_options+1 ):
                    tc.submit( "addoption_0" )
                # Add contents to the new options fields
                for index2 in range( num_options ):
                    option_field_name = 'field_0_option_%i' % index2
                    option_field_value = 'Option%i' % index2
                    tc.fv( "1", option_field_name, option_field_value )
            else:
                tc.fv( "1", "field_type_0", field_type )
            tc.fv( "1", field_default, field_default_contents )
        tc.submit( "save_changes_button" )
        if num_fields == 0:
            self.visit_url( "%s/forms/manage" % self.url )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def edit_form( self, id, form_type='', new_form_name='', new_form_desc='', field_dicts=[], field_index=0,
                   strings_displayed=[], strings_not_displayed=[], strings_displayed_after_submit=[] ):
        """Edit form details; name and description"""
        self.home()
        self.visit_url( "%s/forms/manage?operation=Edit&id=%s" % ( self.url, id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        if new_form_name:
            tc.fv( "1", "name", new_form_name )
        if new_form_desc:
            tc.fv( "1", "description", new_form_desc )
        for i, field_dict in enumerate( field_dicts ):
            index = i + field_index
            tc.submit( "add_field_button" )
            field_name = "field_name_%i" % index
            field_value = field_dict[ 'name' ]
            field_help = "field_helptext_%i" % index
            field_help_value = field_dict[ 'desc' ]
            field_type = "field_type_%i" % index
            field_type_value = field_dict[ 'type' ]
            field_required = "field_required_%i" % index
            field_required_value = field_dict[ 'required' ]
            tc.fv( "1", field_name, field_value )
            tc.fv( "1", field_help, field_help_value )
            tc.fv( "1", field_required, field_required_value )
            if field_type_value.lower() == 'selectfield':
                # SelectFields require a refresh_on_change
                self.refresh_form( field_type, field_type_value )
                for option_index, option in enumerate( field_dict[ 'selectlist' ] ):
                    tc.submit( "addoption_0" )
                    tc.fv( "1", "field_%i_option_%i" % ( index, option_index ), option )
            else:
                tc.fv( "1", field_type, field_type_value )
        tc.submit( "save_changes_button" )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def mark_form_deleted( self, form_id ):
        """Mark a form_definition as deleted"""
        self.home()
        url = "%s/forms/manage?operation=delete&id=%s" % ( self.url, form_id )
        self.visit_url( url )
        check_str = "1 form(s) is deleted."
        self.check_page_for_string( check_str )
        self.home()

    # Requests stuff
    def check_request_grid( self, cntrller, state, deleted=False, strings_displayed=[] ):
        self.visit_url( '%s/%s/list?sort=create_time&f-state=%s&f-deleted=%s' % \
                        ( self.url, cntrller, state.replace( ' ', '+' ), str( deleted ) ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def create_request_type( self, name, desc, request_form_id, sample_form_id, states, strings_displayed=[], strings_displayed_after_submit=[] ):
        self.home()
        self.visit_url( "%s/requests_admin/create_request_type" % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( "1", "name", name )
        tc.fv( "1", "desc", desc )
        tc.fv( "1", "request_form_id", request_form_id )
        tc.fv( "1", "sample_form_id", sample_form_id )
        for index, state in enumerate(states):
            tc.submit( "add_state_button" )
            tc.fv("1", "state_name_%i" % index, state[0])
            tc.fv("1", "state_desc_%i" % index, state[1])
        tc.submit( "save_request_type" )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
    def request_type_permissions( self, request_type_id, request_type_name, role_ids_str, permissions_in, permissions_out ):
        # role_ids_str must be a comma-separated string of role ids
        url = "requests_admin/manage_request_types?operation=permissions&id=%s&update_roles_button=Save" % ( request_type_id )
        for po in permissions_out:
            key = '%s_out' % po
            url ="%s&%s=%s" % ( url, key, role_ids_str )
        for pi in permissions_in:
            key = '%s_in' % pi
            url ="%s&%s=%s" % ( url, key, role_ids_str )
        self.home()
        self.visit_url( "%s/%s" % ( self.url, url ) )
        check_str = "Permissions updated for sequencer configuration '%s'" % request_type_name
        self.check_page_for_string( check_str )
        self.home()
    def create_request( self, cntrller, request_type_id, name, desc, field_value_tuples, select_user_id='',
                        refresh='False', strings_displayed=[], strings_displayed_after_submit=[] ):
        self.visit_url( "%s/requests_common/new?cntrller=%s&refresh=%s&select_request_type=True" % ( self.url, cntrller, refresh ) )
        # The select_request_type SelectList requires a refresh_on_change
        self.refresh_form( 'select_request_type', request_type_id )
        if cntrller == 'requests_admin' and select_user_id:
            # The admin is creating a request on behalf of another user
            # The select_user SelectList requires a refresh_on_change
            # gvk - 9/22/10: TODO: why does select_user require a refresh_on_change?  Nothing in the
            # code is apparent as to why this is done.
            self.refresh_form( 'select_user', select_user_id )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( "1", "name", name )
        tc.fv( "1", "desc", desc )
        for index, field_value_tuple in enumerate( field_value_tuples ):
            field_name = "field_%i" % index
            field_value, refresh_on_change = field_value_tuple
            if refresh_on_change:
                # TODO: If the field is an AddressField, we should test for adding a new address
                # which would need to be handled here.  This currently only allows an existing
                # user_address to be selected.
                self.refresh_form( field_name, field_value )
            else:
                data = self.last_page()
                file( 'greg.html', 'wb' ).write(data )
                tc.fv( "1", field_name, field_value )
        tc.submit( "create_request_button" )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        self.home()
    def edit_request( self, request_id, name, new_name='', new_desc='', new_fields=[], strings_displayed=[], strings_displayed_after_submit=[] ):
        self.visit_url( "%s/requests/list?operation=Edit&id=%s" % ( self.url, request_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.check_page_for_string( 'Edit sequencing request "%s"' % name )
        if new_name:
            tc.fv( "1", "name", new_name )
        if new_desc:
            tc.fv( "1", "desc", new_desc )
        for index, field_value in enumerate( new_fields ):
            tc.fv( "1", "field_%i" % index, field_value )
        tc.submit( "save_changes_request_button" )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
    def add_samples( self, cntrller, request_id, request_name, sample_value_tuples, strings_displayed=[], strings_displayed_after_submit=[] ):
        self.visit_url( "%s/requests/list?operation=show&id=%s" % ( self.url, request_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        # Simulate clicking the add-sample_button on the form.  (gvk: 9/21/10 - TODO : There must be a bug in the mako template 
        # because twill cannot find any forms on the page, but I cannot find it although I've spent time cleaning up the
        # template code and looking for any problems. 
        url = "%s/requests_common/request_page?cntrller=%s&edit_mode=False&id=%s" % ( self.url, cntrller, request_id )
        # This should work, but although twill does not thorw any exceptions, the button click never occurs
        # There are multiple forms on this page, and we'll only be using the form named show_request.
        # for sample_index, sample_value_tuple in enumerate( sample_value_tuples ):
        #     # Add the following form value to the already populated hidden field so that the show_request
        #     # form is the current form
        #     tc.fv( "1", "id", request_id )
        #     tc.submit( 'add_sample_button' )
        for sample_index, sample_value_tuple in enumerate( sample_value_tuples ):
            sample_name, field_values = sample_value_tuple
            sample_name = sample_name.replace( ' ', '+' )
            field_name = "sample_%i_name" % sample_index
            # The following form_value setting should work but since twill barfed on submitting the add_sample_button
            # above, we have to simulate it by appending to the url.
            # tc.fv( "1", field_name, sample_name )
            url += "&%s=%s" % ( field_name, sample_name )
            for field_index, field_value in enumerate( field_values ):
                field_name = "sample_%i_field_%i" % ( sample_index, field_index )
                field_value = field_value.replace( ' ', '+' )
                # The following form_value setting should work but since twill barfed on submitting the add_sample_button
                # above, we have to simulate it by appending to the url.
                # tc.fv( "1", field_name, field_value )
                url += "&%s=%s" % ( field_name , field_value )
        # The following button submit should work but since twill barfed on submitting the add_sample_button
        # above, we have to simulate it by appending to the url.
        # tc.submit( "save_samples_button" )
        url += "&save_samples_button=Save"
        self.visit_url( url )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
    def submit_request( self, cntrller, request_id, request_name, strings_displayed_after_submit=[] ):
        self.visit_url( "%s/%s/list?operation=Submit&id=%s" % ( self.url, cntrller, request_id ) )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
    def reject_request( self, request_id, request_name, comment, strings_displayed=[], strings_displayed_after_submit=[] ):
        self.visit_url( "%s/requests_admin/list?operation=Reject&id=%s" % ( self.url, request_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        tc.fv( "1", "comment", comment )
        tc.submit( "reject_button" )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
    def add_bar_codes( self, request_id, request_name, bar_codes, samples, strings_displayed_after_submit=[] ):
        # We have to simulate the form submission here since twill barfs on the page
        # gvk - 9/22/10 - TODO: make sure the mako template produces valid html
        url = "%s/requests_common/request_page?cntrller=requests_admin&edit_mode=True&id=%s" % ( self.url, request_id )
        for index, field_value in enumerate( bar_codes ):
            sample_field_name = "sample_%i_name" % index
            sample_field_value = samples[ index ].name.replace( ' ', '+' )
            field_name = "sample_%i_barcode" % index
            url += "&%s=%s" % ( field_name, field_value )
            url += "&%s=%s" % ( sample_field_name, sample_field_value )
        url += "&save_samples_button=Save"
        self.visit_url( url )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
    def change_sample_state( self, request_id, request_name, sample_name, sample_id, new_state_id, new_state_name, comment='',
                             strings_displayed=[], strings_displayed_after_submit=[] ):
        # We have to simulate the form submission here since twill barfs on the page
        # gvk - 9/22/10 - TODO: make sure the mako template produces valid html
        url = "%s/requests_common/request_page?cntrller=requests_admin&edit_mode=False&id=%s" % ( self.url, request_id )
        # select_sample_%i=true must be included twice to simulate a CheckboxField checked setting.
        url += "&comment=%s&select_sample_%i=true&select_sample_%i=true&select_state=%i" % ( comment, sample_id, sample_id, new_state_id )
        url += "&select_sample_operation=Change%20state&refresh=true"
        url += "&change_state_button=Save"
        self.visit_url( url )        
        self.check_page_for_string( 'Sequencing Request "%s"' % request_name )
        self.visit_url( "%s/requests_common/sample_events?cntrller=requests_admin&sample_id=%i" % (self.url, sample_id) )
        self.check_page_for_string( 'Events for Sample "%s"' % sample_name )
        self.check_page_for_string( new_state_name )
    def add_user_address( self, user_id, address_dict ):
        self.home()
        self.visit_url( "%s/user/new_address?admin_view=False&user_id=%i" % ( self.url, user_id ) )
        self.check_page_for_string( 'Add new address' )
        for field_name, value in address_dict.items():
            tc.fv( "1", field_name, value )
        tc.submit( "new_address_button" )
        self.check_page_for_string( 'Address (%s) has been added' % address_dict[ 'short_desc' ] )
        
    # Library stuff
    def add_library_template( self, cntrller, item_type, library_id, form_id, form_name, folder_id=None, ldda_id=None ):
        """
        Add a new info template to a library item - the template will ALWAYS BE SET TO INHERITABLE here.  If you want to
        dis-inherit your template, call the manage_library_template_inheritance() below immediately after you call this
        method in your test code.
        """
        self.home()
        if item_type == 'library':
            url = "%s/library_common/add_template?cntrller=%s&item_type=%s&library_id=%s" % \
            ( self.url, cntrller, item_type, library_id )
        elif item_type == 'folder':
            url = "%s/library_common/add_template?cntrller=%s&item_type=%s&library_id=%s&folder_id=%s" % \
            ( self.url, cntrller, item_type, library_id, folder_id )
        elif item_type == 'ldda':
            url = "%s/library_common/add_template?cntrller=%s&item_type=%s&library_id=%s&folder_id=%s&ldda_id=%s" % \
            ( self.url, cntrller, item_type, library_id, folder_id, ldda_id )
        self.visit_url( url )
        self.check_page_for_string ( "Select a template for the" )
        self.refresh_form( "form_id", form_id )
        # For some unknown reason, twill barfs if the form number ( 1 ) is used in the following
        # rather than the form anme ( select_template ), so we have to use the form name.
        tc.fv( "select_template", "inheritable", '1' )
        tc.submit( "add_template_button" )
        self.check_page_for_string = 'A template based on the form "%s" has been added to this' % form_name
        self.home()
    def manage_library_template_inheritance( self, cntrller, item_type, library_id, folder_id=None, ldda_id=None, inheritable=True ):
        # If inheritable is True, the item is currently inheritable.
        self.home()
        if item_type == 'library':
            url = "%s/library_common/manage_template_inheritance?cntrller=%s&item_type=%s&library_id=%s" % \
            ( self.url, cntrller, item_type, library_id )
        elif item_type == 'folder':
            url = "%s/library_common/manage_template_inheritance?cntrller=%s&item_type=%s&library_id=%s&folder_id=%s" % \
            ( self.url, cntrller, item_type, library_id, folder_id )
        elif item_type == 'ldda':
            url = "%s/library_common/manage_template_inheritance?cntrller=%s&item_type=%s&library_id=%s&folder_id=%s&ldda_id=%s" % \
            ( self.url, cntrller, item_type, library_id, folder_id, ldda_id )
        self.visit_url( url )
        if inheritable:
            self.check_page_for_string = 'will no longer be inherited to contained folders and datasets'
        else:
            self.check_page_for_string = 'will now be inherited to contained folders and datasets'
        self.home()
    def browse_libraries_admin( self, deleted=False, strings_displayed=[], strings_not_displayed=[] ):
        self.visit_url( '%s/library_admin/browse_libraries?sort=name&f-description=All&f-name=All&f-deleted=%s' % ( self.url, str( deleted ) ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) incorrectly displayed when browing library." % check_str
            except:
                pass
    def browse_libraries_regular_user( self, strings_displayed=[], strings_not_displayed=[] ):
        self.visit_url( '%s/library/browse_libraries' % self.url )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) incorrectly displayed when browing library." % check_str
            except:
                pass
    def browse_library( self, cntrller, id, show_deleted=False, strings_displayed=[], strings_not_displayed=[] ):
        self.visit_url( '%s/library_common/browse_library?cntrller=%s&id=%s&show_deleted=%s' % ( self.url, cntrller, id, str( show_deleted ) ) )
        data=self.last_page()
        file( 'greg.html', 'wb' ).write( data )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) incorrectly displayed when browing library." % check_str
            except:
                pass
    def create_library( self, name='Library One', description='This is Library One', synopsis='Synopsis for Library One' ):
        """Create a new library"""
        self.visit_url( "%s/library_admin/create_library" % self.url )
        self.check_page_for_string( 'Create a new data library' )
        tc.fv( "1", "name", name )
        tc.fv( "1", "description", description )
        tc.fv( "1", "synopsis", synopsis )
        tc.submit( "create_library_button" )
        check_str = "The new library named '%s' has been created" % name
        self.check_page_for_string( check_str )
        self.home()
    def edit_template( self, cntrller, item_type, library_id, field_type, field_name_1, field_helptext_1, field_default_1,
                       folder_id='', ldda_id='', action='add_field'  ):
        """Edit the form fields defining a library template"""
        self.visit_url( "%s/library_common/edit_template?cntrller=%s&item_type=%s&library_id=%s" % \
                        ( self.url, cntrller, item_type, library_id ) )
        self.check_page_for_string( "Edit form definition" )
        if action == 'add_field':
            tc.submit( "add_field_button" )
            tc.fv( "edit_form", "field_name_1", field_name_1 )
            tc.fv( "edit_form", "field_helptext_1", field_helptext_1 )
            if field_type == 'SelectField':
                # Performs a refresh_on_change in this case
                self.refresh_form( "field_type_1", field_type )
            else:
                tc.fv( "edit_form", "field_type_1", field_type )
            tc.fv( "edit_form", "field_default_1", field_default_1 )
        tc.submit( 'save_changes_button' )
        self.check_page_for_string( "The template for this data library has been updated with your changes." )
    def library_info( self, cntrller, library_id, library_name='', new_name='', new_description='', new_synopsis='', 
                      template_fields=[], strings_displayed=[] ):
        """Edit information about a library, optionally using an existing template with up to 2 elements"""
        self.visit_url( "%s/library_common/library_info?cntrller=%s&id=%s" % ( self.url, cntrller, library_id ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        if new_name and new_description and new_synopsis:
            tc.fv( '1', 'name', new_name )
            tc.fv( '1', 'description', new_description )
            tc.fv( '1', 'synopsis', new_synopsis )
            tc.submit( 'library_info_button' )
            self.check_page_for_string( "Information updated for library" )
        if template_fields:
            for field_name, field_value in template_fields:
                # The 2nd form on the page contains the template, and the form is named edit_info.
                # Set the template field value
                tc.fv( "edit_info", field_name, field_value )
            tc.submit( 'edit_info_button' )
        self.home()
    def library_permissions( self, library_id, library_name, role_ids_str, permissions_in, permissions_out, cntrller='library_admin' ):
        # role_ids_str must be a comma-separated string of role ids
        url = "library_common/library_permissions?id=%s&cntrller=%s&update_roles_button=Save" % ( library_id, cntrller )
        for po in permissions_out:
            key = '%s_out' % po
            url ="%s&%s=%s" % ( url, key, role_ids_str )
        for pi in permissions_in:
            key = '%s_in' % pi
            url ="%s&%s=%s" % ( url, key, role_ids_str )
        self.home()
        self.visit_url( "%s/%s" % ( self.url, url ) )
        check_str = "Permissions updated for library '%s'." % library_name
        self.check_page_for_string( check_str )
        self.home()
    def make_library_item_public( self, library_id, id, cntrller='library_admin', item_type='library',
                                  contents=False, library_name='', folder_name='', ldda_name='' ):
        url = "%s/library_common/make_library_item_public?cntrller=%s&library_id=%s&item_type=%s&id=%s&contents=%s" % \
            ( self.url, cntrller, library_id, item_type, id, str( contents ) )
        self.visit_url( url )
        if item_type == 'library':
            if contents:
                check_str = "The data library (%s) and all it's contents have been made publicly accessible." % library_name
            else:
                check_str = "The data library (%s) has been made publicly accessible, but access to it's contents has been left unchanged." % library_name
        elif item_type == 'folder':
            check_str = "All of the contents of folder (%s) have been made publicly accessible." % folder_name
        elif item_type == 'ldda':
            check_str = "The libary dataset (%s) has been made publicly accessible." % ldda_name
        self.check_page_for_string( check_str )

    # Library folder stuff
    def add_folder( self, cntrller, library_id, folder_id, name='Folder One', description='This is Folder One' ):
        """Create a new folder"""
        url = "%s/library_common/create_folder?cntrller=%s&library_id=%s&parent_id=%s" % ( self.url, cntrller, library_id, folder_id )
        self.visit_url( url )
        self.check_page_for_string( 'Create a new folder' )
        tc.fv( "1", "name", name )
        tc.fv( "1", "description", description )
        tc.submit( "new_folder_button" )
        check_str = "The new folder named '%s' has been added to the data library." % name
        self.check_page_for_string( check_str )
        self.home()
    def folder_info( self, cntrller, folder_id, library_id, name='', new_name='', description='',
                     template_refresh_field_contents='', template_fields=[], strings_displayed=[], strings_not_displayed=[],
                     strings_displayed_after_submit=[], strings_not_displayed_after_submit=[] ):
        """Add information to a library using an existing template with 2 elements"""
        self.visit_url( "%s/library_common/folder_info?cntrller=%s&id=%s&library_id=%s" % \
                        ( self.url, cntrller, folder_id, library_id ) )
        if name and new_name and description:
            tc.fv( '1', "name", new_name )
            tc.fv( '1', "description", description )
            tc.submit( 'rename_folder_button' )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) incorrectly displayed." % check_str
            except:
                pass
        if template_refresh_field_contents:
            # A template containing an AddressField is displayed on the form, so we need to refresh the form 
            # with the received template_refresh_field_contents.  There are 2 forms on the folder_info page
            # when in edit mode, and the 2nd one is the one we want.
            self.refresh_form( "field_0", template_refresh_field_contents, form_no=2 )
        if template_fields:
            # We have an information template associated with the folder, so
            # there are 2 forms on this page and the template is the 2nd form
            for field_name, field_value in template_fields:
                tc.fv( "edit_info", field_name, field_value )
            tc.submit( 'edit_info_button' )
        for check_str in strings_displayed_after_submit:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed_after_submit:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) incorrectly displayed." % check_str
            except:
                pass
        self.home()

    # Library dataset stuff
    def upload_library_dataset( self, cntrller, library_id, folder_id, filename='', server_dir='', replace_id='',
                                upload_option='upload_file', file_type='auto', dbkey='hg18', space_to_tab='',
                                link_data_only='', dont_preserve_dirs='', roles=[], ldda_message='', hda_ids='',
                                template_refresh_field_contents='', template_fields=[], show_deleted='False', strings_displayed=[] ):
        """Add datasets to library using any upload_option"""
        # NOTE: due to the library_wait() method call at the end of this method, no tests should be done
        # for strings_displayed_after_submit.
        url = "%s/library_common/upload_library_dataset?cntrller=%s&library_id=%s&folder_id=%s" % \
            ( self.url, cntrller, library_id, folder_id )
        if replace_id:
            # If we're uploading a new version of a library dataset, we have to include the replace_id param in the
            # request because the form field named replace_id will not be displayed on the upload form if we dont.
            url += "&replace_id=%s" % replace_id
        self.visit_url( url )
        if template_refresh_field_contents:
            # A template containing an AddressField is displayed on the upload form, so we need to refresh the form 
            # with the received template_refresh_field_contents.
            self.refresh_form( "field_0", template_refresh_field_contents )
        for tup in template_fields:
            tc.fv( "1", tup[0], tup[1] )
        tc.fv( "1", "library_id", library_id )
        tc.fv( "1", "folder_id", folder_id )
        tc.fv( "1", "show_deleted", show_deleted )
        tc.fv( "1", "ldda_message", ldda_message )
        tc.fv( "1", "file_type", file_type )
        tc.fv( "1", "dbkey", dbkey )
        if space_to_tab:
            tc.fv( "1", "space_to_tab", space_to_tab )
        if link_data_only:
            tc.fv( "1", "link_data_only", link_data_only )
        if dont_preserve_dirs:
            tc.fv( "1", "dont_preserve_dirs", dont_preserve_dirs )
        for role_id in roles:
            tc.fv( "1", "roles", role_id )
        # Refresh the form by selecting the upload_option - we do this here to ensure
        # all previously entered form contents are retained.
        self.refresh_form( 'upload_option', upload_option )
        if upload_option == 'import_from_history':
            for check_str in strings_displayed:
                self.check_page_for_string( check_str )
            if hda_ids:
                # Twill cannot handle multi-checkboxes, so the form can only have 1 hda_ids checkbox
                tc.fv( "add_history_datasets_to_library", "hda_ids", '1' )
            tc.submit( 'add_history_datasets_to_library_button' )
        else:
            if filename:
                filename = self.get_filename( filename )
                tc.formfile( "1", "files_0|file_data", filename )
            elif server_dir:
                tc.fv( "1", "server_dir", server_dir )
            for check_str in strings_displayed:
                self.check_page_for_string( check_str )
            tc.submit( "runtool_btn" )
        # Give the files some time to finish uploading
        self.library_wait( library_id )
        data = self.last_page()
        file( 'greg1.html', 'wb' ).write( data )
        self.home()
    def ldda_permissions( self, cntrller, library_id, folder_id, id, role_ids_str,
                          permissions_in=[], permissions_out=[], strings_displayed=[], ldda_name='' ):
        # role_ids_str must be a comma-separated string of role ids
        url = "%s/library_common/ldda_permissions?cntrller=%s&library_id=%s&folder_id=%s&id=%s" % \
            ( self.url, cntrller, library_id, folder_id, id )
        for po in permissions_out:
            key = '%s_out' % po
            url ="%s&%s=%s" % ( url, key, role_ids_str )
        for pi in permissions_in:
            key = '%s_in' % pi
            url ="%s&%s=%s" % ( url, key, role_ids_str )
        if permissions_in or permissions_out:
            url += "&update_roles_button=Save"
            self.visit_url( url )
        if not strings_displayed:
            strings_displayed = [ "Permissions updated for dataset '%s'." % ldda_name ]
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        self.home()
    def ldda_edit_info( self, cntrller, library_id, folder_id, ldda_id, ldda_name, new_ldda_name='',
                        template_refresh_field_contents='', template_fields=[], strings_displayed=[], strings_not_displayed=[] ):
        """Edit library_dataset_dataset_association information, optionally template element information"""
        self.visit_url( "%s/library_common/ldda_edit_info?cntrller=%s&library_id=%s&folder_id=%s&id=%s" % \
                        ( self.url, cntrller, library_id, folder_id, ldda_id ) )        
        check_str = 'Edit attributes of %s' % ldda_name
        self.check_page_for_string( check_str )
        if new_ldda_name:
            tc.fv( '1', 'name', new_ldda_name )
            tc.submit( 'save' )
            check_str = "Attributes updated for library dataset '%s'." % new_ldda_name
            self.check_page_for_string( check_str )
        if template_refresh_field_contents:
            # A template containing an AddressField is displayed on the upload form, so we need to refresh the form 
            # with the received template_refresh_field_contents.  There are 4 forms on this page, and the template is
            # contained in the 4th form named "edit_info".
            self.refresh_form( "field_0", template_refresh_field_contents, form_no=4 )
        if template_fields:
            # We have an information template associated with the folder, so
            # there are 2 forms on this page and the template is the 2nd form
            for field_name, field_value in template_fields:
                tc.fv( "edit_info", field_name, field_value )
            tc.submit( 'edit_info_button' )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
        for check_str in strings_not_displayed:
            try:
                self.check_page_for_string( check_str )
                raise AssertionError, "String (%s) should not have been displayed on ldda Edit Attributes page." % check_str
            except:
                pass
        self.home()
    def act_on_multiple_datasets( self, cntrller, library_id, do_action, ldda_ids='', strings_displayed=[] ):
        # Can't use the ~/library_admin/libraries form as twill barfs on it so we'll simulate the form submission
        # by going directly to the form action
        self.visit_url( '%s/library_common/act_on_multiple_datasets?cntrller=%s&library_id=%s&ldda_ids=%s&do_action=%s' \
                        % ( self.url, cntrller, library_id, ldda_ids, do_action ) )
        for check_str in strings_displayed:
            self.check_page_for_string( check_str )
    def download_archive_of_library_files( self, cntrller, library_id, ldda_ids, format ):
        self.home()
        # Here it would be ideal to have twill set form values and submit the form, but
        # twill barfs on that due to the recently introduced page wrappers around the contents
        # of the browse_library.mako template which enable panel layout when visiting the
        # page from an external URL.  By "barfs", I mean that twill somehow loses hod on the 
        # cntrller param.  We'll just simulate the form submission by building the URL manually.
        # Here's the old, better approach...
        #self.visit_url( "%s/library_common/browse_library?cntrller=%s&id=%s" % ( self.url, cntrller, library_id ) )
        #for ldda_id in ldda_ids:
        #    tc.fv( "1", "ldda_ids", ldda_id )
        #tc.fv( "1", "do_action", format )
        #tc.submit( "action_on_datasets_button" )
        # Here's the new approach...
        url = "%s/library_common/act_on_multiple_datasets?cntrller=%s&library_id=%s&do_action=%s" % ( self.url, cntrller, library_id, format )
        for ldda_id in ldda_ids:
            url += "&ldda_ids=%s" % ldda_id
        self.visit_url( url )
        tc.code( 200 )
        archive = self.write_temp_file( self.last_page(), suffix='.' + format )
        self.home()
        return archive
    def check_archive_contents( self, archive, lddas ):
        def get_ldda_path( ldda ):
            path = ""
            parent_folder = ldda.library_dataset.folder
            while parent_folder is not None:
                if parent_folder.parent is None:
                    path = os.path.join( parent_folder.library_root[0].name, path )
                    break
                path = os.path.join( parent_folder.name, path )
                parent_folder = parent_folder.parent
            path += ldda.name
            return path
        def mkdir( file ):
            dir = os.path.join( tmpd, os.path.dirname( file ) )
            if not os.path.exists( dir ):
                os.makedirs( dir )
        tmpd = tempfile.mkdtemp()
        if tarfile.is_tarfile( archive ):
            t = tarfile.open( archive )
            for n in t.getnames():
                mkdir( n )
                t.extract( n, tmpd )
            t.close()
        elif zipfile.is_zipfile( archive ):
            z = zipfile.ZipFile( archive, 'r' )
            for n in z.namelist():
                mkdir( n )
                open( os.path.join( tmpd, n ), 'wb' ).write( z.read( n ) )
            z.close()
        else:
            raise Exception( 'Unable to read archive: %s' % archive )
        for ldda in lddas:
            orig_file = self.get_filename( ldda.name )
            downloaded_file = os.path.join( tmpd, get_ldda_path( ldda ) )
            assert os.path.exists( downloaded_file )
            try:
                self.files_diff( orig_file, downloaded_file )
            except AssertionError, err:
                errmsg = 'Library item %s different than expected, difference:\n' % ldda.name
                errmsg += str( err )
                errmsg += 'Unpacked archive remains in: %s\n' % tmpd
                raise AssertionError( errmsg )
        shutil.rmtree( tmpd )
    def delete_library_item( self, cntrller, library_id, item_id, item_name, item_type='library_dataset' ):
        """Mark a library item as deleted"""
        self.home()
        self.visit_url( "%s/library_common/delete_library_item?cntrller=%s&library_id=%s&item_id=%s&item_type=%s" \
                        % ( self.url, cntrller, library_id, item_id, item_type ) )
        if item_type == 'library_dataset':
            item_desc = 'Dataset'
        else:
            item_desc = item_type.capitalize()
        check_str = "%s '%s' has been marked deleted" % ( item_desc, item_name )
        self.check_page_for_string( check_str )
        self.home()
    def undelete_library_item( self, cntrller, library_id, item_id, item_name, item_type='library_dataset' ):
        """Mark a library item as deleted"""
        self.home()
        self.visit_url( "%s/library_common/undelete_library_item?cntrller=%s&library_id=%s&item_id=%s&item_type=%s" \
                        % ( self.url, cntrller, library_id, item_id, item_type ) )
        if item_type == 'library_dataset':
            item_desc = 'Dataset'
        else:
            item_desc = item_type.capitalize()
        check_str = "%s '%s' has been marked undeleted" % ( item_desc, item_name )
        self.check_page_for_string( check_str )
        self.home()
    def purge_library( self, library_id, library_name ):
        """Purge a library"""
        self.home()
        self.visit_url( "%s/library_admin/purge_library?id=%s" % ( self.url, library_id ) )
        check_str = "Library '%s' and all of its contents have been purged" % library_name
        self.check_page_for_string( check_str )
        self.home()
    def library_wait( self, library_id, cntrller='library_admin', maxiter=90 ):
        """Waits for the tools to finish"""
        count = 0
        sleep_amount = 1
        while count < maxiter:
            count += 1
            self.visit_url( "%s/library_common/browse_library?cntrller=%s&id=%s" % ( self.url, cntrller, library_id ) )
            page = tc.browser.get_html()
            if page.find( '<!-- running: do not change this comment, used by TwillTestCase.library_wait -->' ) > -1:
                time.sleep( sleep_amount )
                sleep_amount += 1
            else:
                break
        self.assertNotEqual(count, maxiter)

    # Tests associated with tags
    def add_tag( self, item_id, item_class, context, new_tag ):
        self.visit_url( "%s/tag/add_tag_async?item_id=%s&item_class=%s&context=%s&new_tag=%s" % \
                        ( self.url, item_id, item_class, context, new_tag ) )
