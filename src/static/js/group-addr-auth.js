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

function checkFlickrAuth()
{
    let needToAuth = true;

    if ( needToAuth === true ) {
        // Tell API endpoint to start auth process
        getRequestTokenAndRedirectClient();
    }

}


function windowLoaded()
{
    console.log( "Inside WindowLoaded" );

    checkFlickrAuth();
}

window.onload = windowLoaded;
