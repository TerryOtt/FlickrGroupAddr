import tornado.ioloop
import tornado.web
import os.path
import tornado.tcpserver
import ssl
import logging


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
            self.set_status( 404, "File at path \"{0}\" does not exist" )



class FlickrGroupAddrEndpointHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",      "*")
        self.set_header("Access-Control-Allow-Headers",     "x-requested-with")
        self.set_header('Access-Control-Allow-Methods',     "GET, OPTIONS")

    
    def options(self):
        # no body
        self.set_status(204)
        self.finish()


    def get(self, operation ):
        valid_operations = {
            "ping"          : self._do_ping,
        }

        if operation in valid_operations:
            logging.info( "Valid operation requested: {0}".format(operation) )
            valid_operations[ operation ]()
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
                "result"    : "pong " 
            }
        )


def _make_app():
    return tornado.web.Application(
        [
            (r"^\/api/v1/(.+)\s*$", FlickrGroupAddrEndpointHandler ),
            (r"^\/(.*?)$", StaticFileHandler ),
        ],
        debug=True
    )


def _quiet_other_loggers():
    other_loggers = [
        "asyncio",
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
