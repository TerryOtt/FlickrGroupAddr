function processRequestTokenResponse( httpResponse )
{
    //console.log("Got response: " + httpResponse );
    tokenResponse = JSON.parse( httpResponse );

    /*
    console.log( "I think the URL we need to bounce the user to now is: \"" + 
        tokenResponse['authorization_url'] + "\"" );
    */

    window.location.replace( tokenResponse['authorization_url'] );
}

function getRequestTokenAndRedirectClient()
{
    let httpRequest = new XMLHttpRequest();
    const url = "https://groupaddrapi.sixbuckssolutions.com/api/v1/auth/start";
    httpRequest.open( "GET", url );
    httpRequest.send();

    console.log("Start auth request sent" );

    httpRequest.onreadystatechange = function() {
        if ( this.readyState == 4 && this.status == 200) {
            console.log("Start auth response received" );

            processRequestTokenResponse( httpRequest.responseText );
        }
    }
}

function getCookie(name) {
    const dc = document.cookie;
    const prefix = name + "=";
    let begin = dc.indexOf("; " + prefix);

    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) {
            return null;
        }
    }
    else {
        begin += 2;
        var end = document.cookie.indexOf(";", begin);
        if (end == -1) {
            end = dc.length;
        }
    }
    // because unescape has been deprecated, replaced with decodeURI
    //return unescape(dc.substring(begin + prefix.length, end));
    return decodeURI(dc.substring(begin + prefix.length, end));
}

function checkFlickrAuth()
{
    // If we have a session ID, don't need to auth
    client_session_id = getCookie( 'client_session_id' ); 

    const needToAuth = (client_session_id === null);

    if ( needToAuth === true ) {
        // Tell API endpoint to start auth process
        getRequestTokenAndRedirectClient();
    }
}

function getClientSessionId()
{
    return client_session_id;
}


/** 
 * Don't wait for window to load, we're intentionally doing a blocking load, so run
 * straight to auth ASAP 
 */
var client_session_id = null;
checkFlickrAuth();
