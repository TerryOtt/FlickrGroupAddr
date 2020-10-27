import tornado.ioloop
import tornado.web
import os
import os.path
import tornado.tcpserver
import ssl
import logging
import flickr_api
import pprint
import uuid
import json


flickr_auth_info = {
    "api_key"   : "80aa90492203094f9fad6b8032f5948b",
    "secret"    : "69003acec0548150"
}

flickr_api.set_keys(
    api_key     = flickr_auth_info['api_key'],
    api_secret  = flickr_auth_info['secret']
)


class StaticFileHandler(tornado.web.RequestHandler):
    def get(self, requested_path):
        static_file_root_dir = "static"
        #self.write( "asked for static file with path \"{0}\"".format(requested_path) )

        # If asked for root, convert that into an index.html call
        if len(requested_path) == 0 or requested_path == "/":
            search_path = os.path.join( static_file_root_dir, "index.html" )
        else:
            search_path = os.path.join( static_file_root_dir, requested_path )

        #self.write( "File search path: {0}".format(search_path) ) 

        if os.path.isfile( search_path ) is True:
            with open( search_path, "r") as static_file_handle:
                file_contents = static_file_handle.read()
                
            self.write( file_contents )
        else:
            self.set_status( 404, "File at path \"{0}\" does not exist".format(search_path) )



class FlickrGroupAddrEndpointHandler(tornado.web.RequestHandler):

    # Don't override __init__ in a handler, per Tornado docs
    def initialize(self):
        self.flickr_auth = {
            "api_key"   : "80aa90492203094f9fad6b8032f5948b",
            "secret"    : "69003acec0548150"
        }

        flickr_api.set_keys( 
            api_key     = self.flickr_auth['api_key'], 
            api_secret  = self.flickr_auth['secret']
        )

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",      "*")
        self.set_header("Access-Control-Allow-Headers",     "x-requested-with")
        self.set_header('Access-Control-Allow-Methods',     "GET, OPTIONS")

    
    def options(self):
        # no body
        self.set_status(204)
        self.finish()


    def get(self, operation, session_id ):
        valid_operations = {
            "ping"              : self._do_ping,
            "auth-start"        : self._auth_create_request_token,
            "auth-callback"     : self._auth_callback,
            "user-info"         : self._get_user_info,
        }

        if operation in valid_operations:
            logging.info( "Valid operation requested: {0}".format(operation) )
            valid_operations[ operation ]( session_id )
        else:
            error_string = "Invalid operation requested: \"{0}\"".format(operation)
            self.set_status( 404, error_string )
            self.write( 
                { 
                    "status"        : "error",
                    "error_info"    : error_string
                }
            )


    def _do_ping(self):
        self.write( 
            { 
                "result"    : "success",
                "data"      : "pong",
            }
        )

    def _auth_create_request_token(self, session_id=None):
        auth_handler = flickr_api.auth.AuthHandler(
            callback="https://groupaddrapi.sixbuckssolutions.com/api/v1/auth-callback"
        )
        perms = "read"
        authorization_url = auth_handler.get_authorization_url( perms )

        # Store the auth handler context so we can recreate it when we get our callback
        auth_handler_dict = auth_handler.todict() 
        with open( "request_token_{0}.json".format(auth_handler_dict['request_token_key']), "w" ) as file_handle:
            json.dump( auth_handler_dict, file_handle, indent=4, sort_keys=True )

        self.write( 
            {

                "result"            : "success",
                "authorization_url" : authorization_url
            }
        )



    def _auth_callback( self, session_id=None ):
        try:
            oauth_token     = self.get_argument( 'oauth_token' )
            oauth_verifier  = self.get_argument( 'oauth_verifier' )

            logging.debug( "   Token : {0}".format(oauth_token) )
            logging.debug( "Verifier : {0}".format(oauth_verifier) )
        except e as MissingArgumentException:
            self.set_status( 400, "oauth_token and/or oauth_verifier argument missing" )
            return

        # If we have a matching outstanding request, re-create the AuthHandler for that object
        state_file =  "request_token_{0}.json".format(oauth_token)
        if os.path.isfile( state_file ) is True:
            with open( state_file, 'r' ) as request_token_file_handle:
                request_token_dict = json.load( request_token_file_handle )

            # Reconstitute auth handler from JSON
            auth_handler = flickr_api.auth.AuthHandler.fromdict( request_token_dict )

            # Unlink request token state file, loop is closed
            os.remove( state_file )

            # Add the verifier to the request token, will change internal state of auth handler from 
            #       a request token to an access token
            auth_handler.set_verifier( oauth_verifier )

            # Create GUID which is all the client will ever see
            client_session_id = uuid.uuid4()

            # Persist the access token 
            access_token_dict = auth_handler.todict()
            with open( "access_token_{0}.json".format(str(client_session_id)), "w" ) as access_token_file_handle:
                json.dump( access_token_dict, access_token_file_handle, indent=4, sort_keys=True )

            # Redirect to page where client will save their session ID as a cookie
            self.redirect( "https://groupaddr.sixbuckssolutions.com/store_client_session_id.html?client_session_id={0}".format(
                client_session_id) )

        else:
            self.set_status( 403, "No outstanding requests for request token key {0}".format(oauth_token) )


    def _get_flickr_user(self):
        return flickr_api.test.login()


    def _get_flickr_photo_ids(self, flickr_user):
        curr_results_page = 1 

        # Flickr API defaults to 100 results per page, with max of 500. Let's do 500 to reduce amount of work
        photos_per_results_page = 500

        photo_ids = []

        done_reading = False

        while done_reading is False:
            logging.debug("Reading photos results page {0}".format(curr_results_page) )
            curr_results = flickr_user.getPhotos(page = curr_results_page, per_page = photos_per_results_page)

            # If this is the first read, find out total number of photos and pages
            if curr_results_page == 1:
                total_number_photos = curr_results.info.total
                total_number_pages = curr_results.info.pages
                logging.debug("Total number of pages: {0}".format(
                    curr_results.info.pages) )

            # Add the photo ID's in this results set to our master list 
            for curr_photo in curr_results:
                photo_ids.append( int(curr_photo.id) )

            # Did we just read the last page of photos?
            if curr_results_page == total_number_pages:
                break
            else:
                curr_results_page += 1

        photo_ids.sort()

        return photo_ids


    def _get_groups( self ):
        group_info = []
        logging.debug("Getting groups this user can add photos to")
        #flickr_groups = flickr_api.Group.getGroups()
        group_walker = flickr_api.Walker(flickr_api.Group.getGroups)
        for curr_group in group_walker:
            group_info.append( 
                {
                    "id"            : curr_group.id,
                    "name"          : curr_group.name
                }
            )
        logging.debug("Group listing complete")

        return group_info


    def _get_user_info(self, session_id ):
        logging.debug( "Session ID: {0}".format(session_id) )

        # Do we know anything about this session ID?
        access_token_file =  "access_token_{0}.json".format( session_id )

        if os.path.isfile( access_token_file ) is True:
            logging.info( "Session ID {0} is known and has an access token".format(session_id) )
            with open( access_token_file, "r" ) as access_token_file_handle:
                access_token_info = json.load( access_token_file_handle )

            #logging.debug( "Access token info:\n{0}".format( json.dumps(access_token_info, indent=4, sort_keys=True)))
        else:
            self.set_status( 400, "Unknown session ID {0}".format(session_id) )
            return

        auth_handler = flickr_api.auth.AuthHandler.fromdict( access_token_info )

        flickr_api.set_auth_handler( auth_handler )

        # Now fully authorized

        # Get currently logged-in user
        flickr_user = self._get_flickr_user()

        # Get all relevant info for the page
        user_info = {
            'id'        : flickr_user.id,
            'username'  : flickr_user.username 
        }
        #flickr_photo_ids    = self._get_flickr_photo_ids( flickr_user )
        flickr_groups = self._get_groups()

        self.write( 
            {
                "user_info"         : user_info,
                "public_groups"     : flickr_groups,
            }
        )





def _make_app():
    return tornado.web.Application(
        [
            (r"^/api/v1/([^/]*)/?(.+)?\s*$", FlickrGroupAddrEndpointHandler ),
            (r"^/(.*?)$", StaticFileHandler ),
        ],
        debug=True
    )


def _quiet_other_loggers():
    other_loggers = [
        "asyncio", "urllib3", "flickr_api"
    ]
 
    for curr_logger in other_loggers:
        logging.getLogger( curr_logger ).setLevel( logging.WARN )


def _make_ssl_ctx():
    ssl_ctx = ssl.create_default_context( ssl.Purpose.CLIENT_AUTH )
    crt_file = '/etc/letsencrypt/live/groupaddrapi.sixbuckssolutions.com/fullchain.pem'
    key_file = '/etc/letsencrypt/live/groupaddrapi.sixbuckssolutions.com/privkey.pem'

    logging.info( "TLS certificate and chain: {0}\n     TLS private key file: {1}".format(crt_file, key_file) )

    ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    acceptable_cipher_suites = [
        "ECDHE-ECDSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        #"ECDHE-ECDSA-AES128-SHA",
        #"ECDHE-ECDSA-AES256-SHA",
        #"ECDHE-ECDSA-AES128-SHA256",
        #"ECDHE-ECDSA-AES256-SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-RSA-AES256-GCM-SHA384",
        #"ECDHE-RSA-AES128-SHA",
        #"ECDHE-RSA-AES256-SHA",
        #"ECDHE-RSA-AES128-SHA256",
        #"ECDHE-RSA-AES256-SHA384",
        "DHE-RSA-AES128-GCM-SHA256",
        "DHE-RSA-AES256-GCM-SHA384",
        #"DHE-RSA-AES128-SHA",
        #"DHE-RSA-AES256-SHA",
        #"DHE-RSA-AES128-SHA256",
        #"DHE-RSA-AES256-SHA256",
    ]

    ssl_ctx.set_ciphers( ":".join(acceptable_cipher_suites) )

    ssl_ctx.load_cert_chain( crt_file, key_file ) 

    return ssl_ctx


if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG )
    _quiet_other_loggers()
    application = _make_app()
    ssl_ctx = _make_ssl_ctx()
    
    http_server = tornado.httpserver.HTTPServer( application, ssl_options=ssl_ctx )
    server_port = 443

    http_server.listen( server_port )

    logging.info( "Listening for HTTPS connections on port {0}".format(server_port) )

    tornado.ioloop.IOLoop.current().start()
