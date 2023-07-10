/* script to render a cookie consent iframe based on provided configuration and 
store it in a cookie named cookie_consent for 365 days */

function closeIframe() {
  $('#cookie-consent-iframe').remove();
}

function setCookie(cname, cvalue, exdays) {
  var d = new Date();
  d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
  var expires = 'expires=' + d.toUTCString();
  document.cookie = cname + '=' + cvalue + ';' + expires + ';path=/';
}

function getCookie(cname) {
  var name = cname + '=';
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return '';
}

function handleIframeButton(buttonData) {
  setCookie('cookie_consent', buttonData, 365);
  if (buttonData === 'accept') {
    closeIframe();
  } else {
    window.history.back();
  }
}

function checkConsentCookie() {
  let cookieValue = getCookie('cookie_consent');
  if (cookieValue && cookieValue === 'accept') {
    closeIframe();
  } else {
    setCookie('cookie_consent', 'decline', 365);
  }
}

function renderCookieConsent({
  title,
  cookieDetails,
  acceptButtonText,
  rejectButtonText,
}) {
  // const mockConfig = {
  //   title: 'Test title',
  //   cookieDetails: [
  //     {
  //       type: 'Your Privacy',
  //       content:
  //         'Zelthy Platform follows the policy of having cookies that are strictly necessary for enabling basic functionalities. Below is the description of the cookies in use',
  //       cookies: [],
  //     },
  //     {
  //       type: 'Necessary Cookies',
  //       content:
  //         "Session Cookie: This cookie stores a session ID that uniquely identifies a user's sessions to maintain state persistence. The session ID is expired automatically after 30 minutes of user's inactivity. The session cookiecomes with a secured flag and is also automatically expired when the user closes the browser.CSRF Token Cookie: This cookie contains a token that is issued to the user's browser to prevent against Cross Site Request Forgery(CSRF) attack, a common malicious activity that attempts to send request from third-party site while pretending to be from the origin application. With the CSRF token cookie, the application server verifies if the token from the client is the same as the one issued, blocking unauthorized requests directly.",
  //       cookies: ['session', 'csrf'],
  //     },
  //   ],
  //   acceptButtonText: 'Accept all cookies',
  //   rejectButtonText: 'Reject cookies',
  // };

  const consentBody = `<div class="row align-items-center vh-100 mx-md-0 mx-2">
    <div class="col-md-8 mx-auto">
      <div class="card" style="max-height: 75%;">
        <div class="card-header">
          <h5 class="card-title">${title}</h5>
        </div>
        <div class="card-body overflow-auto">
          <div class="card-text">
            <div id="cookie-consent-body" class="row">
              <div class="col-md-3 mb-md-0 mb-2">
                ${cookieDetails
                  .map(
                    (detail, index) =>
                      `<div>
                        <a
                        class="text-info"
                        data-toggle="collapse" 
                        href="#collapse-data-${index}" 
                        role="button" 
                        aria-expanded="false" 
                        aria-controls="collapse-data-${index}">
                          ${detail.type}
                        </a>
                    </div>
                    ${index !== cookieDetails.length - 1 ? '<hr />' : ''}`
                  )
                  .join('')}
              </div>
              <div class="offset-md-1 col-md-8">
                ${cookieDetails
                  .map(
                    (detail, index) =>
                      `<div
                      class="collapse ${index === 0 ? 'show' : ''}"
                      data-parent="#cookie-consent-body"
                      id="collapse-data-${index}">
                        ${detail.content}
                        ${detail.cookies.length ? '<hr /> ' : ''}
                        ${detail.cookies
                          .map(
                            cookie =>
                              `<li class="text-secondary">
                            ${cookie}
                          </li>`
                          )
                          .join('')}
                      </div>`
                  )
                  .join('')}              
              </div>
            </div>
          </div>
        </div>
        <div class="card-footer text-right">
          <button type="button" data-cookie-status="accept" class="cookie-consent-button btn btn-primary">${acceptButtonText}</button>
          <button type="button" data-cookie-status="decline" class="cookie-consent-button btn btn-secondary" data-dismiss="modal">${rejectButtonText}</button>
        </div>
      </div>
    </div>
  </div>`;

  const bootstrapScript = `<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.min.js" integrity="sha384-w1Q4orYjBQndcko6MimVbzY0tgp4pWB4lZ7lr30WKz0vr/aWKhXdBNmNb5D92v7s" crossorigin="anonymous"><\/script>`;
  const jqueryScript = `<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"><\/script>`;

  const iframeDocument = `<html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">
    </head>
    <body style="background-color: rgba(0,0,0,0.5);">
      ${jqueryScript}
      ${bootstrapScript}
      ${consentBody}
      <script type="text/javascript">
        $('.cookie-consent-button').click(function () {
          const dataCookieStatus = $(this).attr('data-cookie-status');
          parent.handleIframeButton(dataCookieStatus);
        });
        $('[data-toggle=collapse]').click(function (e) {
          const titleId = $(this).attr('href');
          const collapseElement = $(titleId);
          if (collapseElement.attr('class').includes('show')) {
            e.stopPropagation();
            return false;
          }
        });
      <\/script>
    </body>
  </html>`;

  $('body').append(
    `<iframe id="cookie-consent-iframe" allowfullscreen="true"></iframe>`
  );
  $('#cookie-consent-iframe').css({
    position: 'fixed',
    top: '0',
    left: '0',
    bottom: '0',
    right: '0',
    width: '100%',
    height: '100%',
    border: '0',
  });

  document
    .querySelector('#cookie-consent-iframe')
    .contentDocument.write(iframeDocument);

  checkConsentCookie();
}
