"""
Custom exceptions for Galaxy
"""

from galaxy import eggs
eggs.require( "Paste" )

from paste import httpexceptions
from ..exceptions import error_codes


class MessageException( Exception ):
    """
    Exception to make throwing errors from deep in controllers easier.
    """
    # status code to be set when used with API.
    status_code = 400
    # Error code information embedded into API json responses.
    err_code = error_codes.UNKNOWN

    def __init__( self, err_msg=None, type="info", **extra_error_info ):
        self.err_msg = err_msg or self.err_code.default_error_message
        self.type = type
        self.extra_error_info = extra_error_info

    def __str__( self ):
        return self.err_msg


class ItemDeletionException( MessageException ):
    pass


class ObjectInvalid( Exception ):
    """ Accessed object store ID is invalid """
    pass

# Please keep the exceptions ordered by status code

class ActionInputError( MessageException ):
    status_code = 400
    err_code = error_codes.USER_REQUEST_INVALID_PARAMETER

    def __init__( self, err_msg, type="error" ):
        super( ActionInputError, self ).__init__( err_msg, type )

class DuplicatedSlugException( MessageException ):
    status_code = 400
    err_code = error_codes.USER_SLUG_DUPLICATE

class ObjectAttributeInvalidException( MessageException ):
    status_code = 400
    err_code = error_codes.USER_OBJECT_ATTRIBUTE_INVALID

class ObjectAttributeMissingException( MessageException ):
    status_code = 400
    err_code = error_codes.USER_OBJECT_ATTRIBUTE_MISSING

class MalformedId( MessageException ):
    status_code = 400
    err_code = error_codes.MALFORMED_ID

class RequestParameterMissingException( MessageException ):
    status_code = 400
    err_code = error_codes.USER_REQUEST_MISSING_PARAMETER

class RequestParameterInvalidException( MessageException ):
    status_code = 400
    err_code = error_codes.USER_REQUEST_INVALID_PARAMETER

class ItemAccessibilityException( MessageException ):
    status_code = 403
    err_code = error_codes.USER_CANNOT_ACCESS_ITEM

class ItemOwnershipException( MessageException ):
    status_code = 403
    err_code = error_codes.USER_DOES_NOT_OWN_ITEM

class ObjectNotFound( MessageException ):
    """ Accessed object was not found """
    status_code = 404
    err_code = error_codes.USER_OBJECT_NOT_FOUND

class Conflict( MessageException ):
    status_code = 409
    err_code = error_codes.CONFLICT   

class InconsistentDatabase ( MessageException ):
    status_code = 500
    err_code = error_codes.INCONSISTENT_DATABASE   

class InternalServerError ( MessageException ):
    status_code = 500
    err_code = error_codes.INTERNAL_SERVER_ERROR    

class NotImplemented ( MessageException ):
    status_code = 501
    err_code = error_codes.NOT_IMPLEMENTED    
