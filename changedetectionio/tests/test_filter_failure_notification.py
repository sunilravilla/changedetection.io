import os
import time
from flask import url_for
from .util import set_original_response, live_server_setup, extract_UUID_from_client, wait_for_all_checks
from changedetectionio.model import App


def set_response_with_filter():
    test_return_data = """<html>
       <body>
     Some initial text<br>
     <p>Which is across multiple lines</p>
     <br>
     So let's see what happens.  <br>
     <div id="nope-doesnt-exist">Some text thats the same</div>     
     </body>
     </html>
    """

    with open("test-datastore/endpoint-content.txt", "w") as f:
        f.write(test_return_data)
    return None

def run_filter_test(client, content_filter):

    # Give the endpoint time to spin up
    time.sleep(1)
    # cleanup for the next
    client.get(
        url_for("form_delete", uuid="all"),
        follow_redirects=True
    )
    if os.path.isfile("test-datastore/notification.txt"):
        os.unlink("test-datastore/notification.txt")

    # Add our URL to the import page
    test_url = url_for('test_endpoint', _external=True)
    res = client.post(
        url_for("form_quick_watch_add"),
        data={"url": test_url, "tags": ''},
        follow_redirects=True
    )

    assert b"Watch added" in res.data

    # Give the thread time to pick up the first version
    wait_for_all_checks(client)

    # Goto the edit page, add our ignore text
    # Add our URL to the import page
    url = url_for('test_notification_endpoint', _external=True)
    notification_url = url.replace('http', 'json')

    print(">>>> Notification URL: " + notification_url)

    # Just a regular notification setting, this will be used by the special 'filter not found' notification
    notification_form_data = {"notification_urls": notification_url,
                              "notification_title": "New ChangeDetection.io Notification - {{watch_url}}",
                              "notification_body": "BASE URL: {{base_url}}\n"
                                                   "Watch URL: {{watch_url}}\n"
                                                   "Watch UUID: {{watch_uuid}}\n"
                                                   "Watch title: {{watch_title}}\n"
                                                   "Watch tag: {{watch_tag}}\n"
                                                   "Preview: {{preview_url}}\n"
                                                   "Diff URL: {{diff_url}}\n"
                                                   "Snapshot: {{current_snapshot}}\n"
                                                   "Diff: {{diff}}\n"
                                                   "Diff Full: {{diff_full}}\n"
                                                   ":-)",
                              "notification_format": "Text"}

    notification_form_data.update({
        "url": test_url,
        "tags": "my tag",
        "title": "my title 123",
        "headers": "",
        "filter_failure_notification_send": 'y',
        "include_filters": content_filter,
        "fetch_backend": "html_requests"})

    res = client.post(
        url_for("edit_page", uuid="first"),
        data=notification_form_data,
        follow_redirects=True
    )

    assert b"Updated watch." in res.data
    wait_for_all_checks(client)

    # Now the notification should not exist, because we didnt reach the threshold
    assert not os.path.isfile("test-datastore/notification.txt")

    # -2 because we would have checked twice above (on adding and on edit)
    for i in range(0, App._FILTER_FAILURE_THRESHOLD_ATTEMPTS_DEFAULT-2):
        res = client.get(url_for("form_watch_checknow"), follow_redirects=True)
        wait_for_all_checks(client)
        assert not os.path.isfile("test-datastore/notification.txt"), f"test-datastore/notification.txt should not exist - Attempt {i}"

    # We should see something in the frontend
    assert b'Warning, no filters were found' in res.data

    # One more check should trigger it (see -2 above)
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    wait_for_all_checks(client)
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    wait_for_all_checks(client)
    # Now it should exist and contain our "filter not found" alert
    assert os.path.isfile("test-datastore/notification.txt")

    with open("test-datastore/notification.txt", 'r') as f:
        notification = f.read()

    assert 'CSS/xPath filter was not present in the page' in notification
    assert content_filter.replace('"', '\\"') in notification

    # Remove it and prove that it doesn't trigger when not expected
    # It should register a change, but no 'filter not found'
    os.unlink("test-datastore/notification.txt")
    set_response_with_filter()

    # Try several times, it should NOT have 'filter not found'
    for i in range(0, App._FILTER_FAILURE_THRESHOLD_ATTEMPTS_DEFAULT):
        client.get(url_for("form_watch_checknow"), follow_redirects=True)
        wait_for_all_checks(client)

    # It should have sent a notification, but..
    assert os.path.isfile("test-datastore/notification.txt")
    # but it should not contain the info about a failed filter (because there was none in this case)
    with open("test-datastore/notification.txt", 'r') as f:
        notification = f.read()
    assert not 'CSS/xPath filter was not present in the page' in notification

    # Re #1247 - All tokens got replaced correctly in the notification
    res = client.get(url_for("index"))
    uuid = extract_UUID_from_client(client)
    # UUID is correct, but notification contains tag uuid as UUIID wtf
    assert uuid in notification

    # cleanup for the next
    client.get(
        url_for("form_delete", uuid="all"),
        follow_redirects=True
    )
    os.unlink("test-datastore/notification.txt")


def test_setup(live_server):
    live_server_setup(live_server)

def test_check_include_filters_failure_notification(client, live_server):
    set_original_response()
    wait_for_all_checks(client)
    run_filter_test(client, '#nope-doesnt-exist')

def test_check_xpath_filter_failure_notification(client, live_server):
    set_original_response()
    time.sleep(1)
    run_filter_test(client, '//*[@id="nope-doesnt-exist"]')

# Test that notification is never sent
