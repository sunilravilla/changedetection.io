from flask import url_for
from . util import set_original_response, set_modified_response, live_server_setup
import time


def test_bad_access(client, live_server):
    live_server_setup(live_server)
    res = client.post(
        url_for("import_page"),
        data={"urls": 'https://localhost'},
        follow_redirects=True
    )

    assert b"1 Imported" in res.data

    # Attempt to add a body with a GET method
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
              "url": 'javascript:alert(document.domain)',
              "tag": "",
              "method": "GET",
              "fetch_backend": "html_requests",
              "body": ""},
        follow_redirects=True
    )

    assert b'Watch protocol is not permitted by SAFE_PROTOCOL_REGEX' in res.data

    res = client.post(
        url_for("form_quick_watch_add"),
        data={"url": '            javascript:alert(123)', "tag": ''},
        follow_redirects=True
    )

    assert b'Watch protocol is not permitted by SAFE_PROTOCOL_REGEX' in res.data

    res = client.post(
        url_for("form_quick_watch_add"),
        data={"url": '%20%20%20javascript:alert(123)%20%20', "tag": ''},
        follow_redirects=True
    )

    assert b'Watch protocol is not permitted by SAFE_PROTOCOL_REGEX' in res.data


    res = client.post(
        url_for("form_quick_watch_add"),
        data={"url": ' source:javascript:alert(document.domain)', "tag": ''},
        follow_redirects=True
    )

    assert b'Watch protocol is not permitted by SAFE_PROTOCOL_REGEX' in res.data

    # file:// is permitted by default, but it will be caught by ALLOW_FILE_URI

    client.post(
        url_for("form_quick_watch_add"),
        data={"url": 'file:///tasty/disk/drive', "tag": ''},
        follow_redirects=True
    )
    time.sleep(1)
    res = client.get(url_for("index"))

    assert b'file:// type access is denied for security reasons.' in res.data