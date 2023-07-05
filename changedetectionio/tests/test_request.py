import json
import os
import time
from flask import url_for
from . util import set_original_response, set_modified_response, live_server_setup, wait_for_all_checks, extract_UUID_from_client

def test_setup(live_server):
    live_server_setup(live_server)

# Hard to just add more live server URLs when one test is already running (I think)
# So we add our test here (was in a different file)
def test_headers_in_request(client, live_server):
    #live_server_setup(live_server)
    # Add our URL to the import page
    test_url = url_for('test_headers', _external=True)
    if os.getenv('PLAYWRIGHT_DRIVER_URL'):
        # Because its no longer calling back to localhost but from browserless, set in test-only.yml
        test_url = test_url.replace('localhost', 'changedet')

    # Add the test URL twice, we will check
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    wait_for_all_checks(client)

    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    wait_for_all_checks(client)
    cookie_header = '_ga=GA1.2.1022228332; cookie-preferences=analytics:accepted;'


    # Add some headers to a request
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
              "url": test_url,
              "tags": "",
              "fetch_backend": 'html_webdriver' if os.getenv('PLAYWRIGHT_DRIVER_URL') else 'html_requests',
              "headers": "xxx:ooo\ncool:yeah\r\ncookie:"+cookie_header},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data


    # Give the thread time to pick up the first version
    wait_for_all_checks(client)

    # The service should echo back the request headers
    res = client.get(
        url_for("preview_page", uuid="first"),
        follow_redirects=True
    )

    # Flask will convert the header key to uppercase
    assert b"Xxx:ooo" in res.data
    assert b"Cool:yeah" in res.data

    # The test call service will return the headers as the body
    from html import escape
    assert escape(cookie_header).encode('utf-8') in res.data

    wait_for_all_checks(client)

    # Re #137 -  Examine the JSON index file, it should have only one set of headers entered
    watches_with_headers = 0
    with open('test-datastore/url-watches.json') as f:
        app_struct = json.load(f)
        for uuid in app_struct['watching']:
            if (len(app_struct['watching'][uuid]['headers'])):
                watches_with_headers += 1

    # Should be only one with headers set
    assert watches_with_headers==1

def test_body_in_request(client, live_server):
    # Add our URL to the import page
    test_url = url_for('test_body', _external=True)
    if os.getenv('PLAYWRIGHT_DRIVER_URL'):
        # Because its no longer calling back to localhost but from browserless, set in test-only.yml
        test_url = test_url.replace('localhost', 'cdio')

    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    wait_for_all_checks(client)

    # add the first 'version'
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
              "url": test_url,
              "tags": "",
              "method": "POST",
              "fetch_backend": "html_requests",
              "body": "something something"},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data

    wait_for_all_checks(client)

    # Now the change which should trigger a change
    body_value = 'Test Body Value'
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
              "url": test_url,
              "tags": "",
              "method": "POST",
              "fetch_backend": "html_requests",
              "body": body_value},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data

    wait_for_all_checks(client)

    # The service should echo back the body
    res = client.get(
        url_for("preview_page", uuid="first"),
        follow_redirects=True
    )

    # If this gets stuck something is wrong, something should always be there
    assert b"No history found" not in res.data
    # We should see what we sent in the reply
    assert str.encode(body_value) in res.data

    ####### data sanity checks
    # Add the test URL twice, we will check
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    watches_with_body = 0
    with open('test-datastore/url-watches.json') as f:
        app_struct = json.load(f)
        for uuid in app_struct['watching']:
            if app_struct['watching'][uuid]['body']==body_value:
                watches_with_body += 1

    # Should be only one with body set
    assert watches_with_body==1

    # Attempt to add a body with a GET method
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
              "url": test_url,
              "tags": "",
              "method": "GET",
              "fetch_backend": "html_requests",
              "body": "invalid"},
        follow_redirects=True
    )
    assert b"Body must be empty when Request Method is set to GET" in res.data


def test_method_in_request(client, live_server):
    # Add our URL to the import page
    test_url = url_for('test_method', _external=True)
    if os.getenv('PLAYWRIGHT_DRIVER_URL'):
        # Because its no longer calling back to localhost but from browserless, set in test-only.yml
        test_url = test_url.replace('localhost', 'cdio')

    # Add the test URL twice, we will check
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    wait_for_all_checks(client)
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    wait_for_all_checks(client)

    # Attempt to add a method which is not valid
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
            "url": test_url,
            "tags": "",
            "fetch_backend": "html_requests",
            "method": "invalid"},
        follow_redirects=True
    )
    assert b"Not a valid choice" in res.data

    # Add a properly formatted body
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
            "url": test_url,
            "tags": "",
            "fetch_backend": "html_requests",
            "method": "PATCH"},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data

    # Give the thread time to pick up the first version
    wait_for_all_checks(client)

    # The service should echo back the request verb
    res = client.get(
        url_for("preview_page", uuid="first"),
        follow_redirects=True
    )

    # The test call service will return the verb as the body
    assert b"PATCH" in res.data

    wait_for_all_checks(client)

    watches_with_method = 0
    with open('test-datastore/url-watches.json') as f:
        app_struct = json.load(f)
        for uuid in app_struct['watching']:
            if app_struct['watching'][uuid]['method'] == 'PATCH':
                watches_with_method += 1

    # Should be only one with method set to PATCH
    assert watches_with_method == 1

    res = client.get(url_for("form_delete", uuid="all"), follow_redirects=True)
    assert b'Deleted' in res.data

def test_headers_textfile_in_request(client, live_server):
    #live_server_setup(live_server)
    # Add our URL to the import page
    test_url = url_for('test_headers', _external=True)
    if os.getenv('PLAYWRIGHT_DRIVER_URL'):
        # Because its no longer calling back to localhost but from browserless, set in test-only.yml
        test_url = test_url.replace('localhost', 'cdio')

    print ("TEST URL IS ",test_url)
    # Add the test URL twice, we will check
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    wait_for_all_checks(client)


    # Add some headers to a request
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={
              "url": test_url,
              "tags": "testtag",
              "fetch_backend": 'html_webdriver' if os.getenv('PLAYWRIGHT_DRIVER_URL') else 'html_requests',
              "headers": "xxx:ooo\ncool:yeah\r\n"},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data
    wait_for_all_checks(client)

    with open('test-datastore/headers-testtag.txt', 'w') as f:
        f.write("tag-header: test")

    with open('test-datastore/headers.txt', 'w') as f:
        f.write("global-header: nice\r\nnext-global-header: nice")

    with open('test-datastore/'+extract_UUID_from_client(client)+'/headers.txt', 'w') as f:
        f.write("watch-header: nice")

    client.get(url_for("form_watch_checknow"), follow_redirects=True)

    # Give the thread time to pick it up
    wait_for_all_checks(client)

    res = client.get(url_for("edit_page", uuid="first"))
    assert b"Extra headers file found and will be added to this watch" in res.data

    # Not needed anymore
    os.unlink('test-datastore/headers.txt')
    os.unlink('test-datastore/headers-testtag.txt')
    os.unlink('test-datastore/'+extract_UUID_from_client(client)+'/headers.txt')
    # The service should echo back the request verb
    res = client.get(
        url_for("preview_page", uuid="first"),
        follow_redirects=True
    )

    assert b"Global-Header:nice" in res.data
    assert b"Next-Global-Header:nice" in res.data
    assert b"Xxx:ooo" in res.data
    assert b"Watch-Header:nice" in res.data
    assert b"Tag-Header:test" in res.data


    #unlink headers.txt on start/stop
    res = client.get(url_for("form_delete", uuid="all"), follow_redirects=True)
    assert b'Deleted' in res.data