#!/usr/bin/python3

import time
from flask import url_for
from .util import live_server_setup
from changedetectionio import html_tools


def set_original(excluding=None, add_line=None):
    test_return_data = """<html>
     <body>
     <p>Some initial text</p>
     <p>So let's see what happens.</p>
     <p>and a new line!</p>
     <p>The golden line</p>
     <p>A BREAK TO MAKE THE TOP LINE STAY AS "REMOVED" OR IT WILL GET COUNTED AS "CHANGED INTO"</p>
     <p>Something irrelevant</p>          
     </body>
     </html>
    """

    if add_line:
        c=test_return_data.splitlines()
        c.insert(5, add_line)
        test_return_data = "\n".join(c)

    if excluding:
        output = ""
        for i in test_return_data.splitlines():
            if not excluding in i:
                output += f"{i}\n"

        test_return_data = output

    with open("test-datastore/endpoint-content.txt", "w") as f:
        f.write(test_return_data)

def test_setup(client, live_server):
    live_server_setup(live_server)

def test_check_removed_line_contains_trigger(client, live_server):
    sleep_time_for_fetch_thread = 3

    # Give the endpoint time to spin up
    time.sleep(1)
    set_original()
    # Add our URL to the import page
    test_url = url_for('test_endpoint', _external=True)
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    # Give the thread time to pick it up
    time.sleep(sleep_time_for_fetch_thread)

    # Goto the edit page, add our ignore text
    # Add our URL to the import page
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={"trigger_text": 'The golden line',
              "url": test_url,
              'fetch_backend': "html_requests",
              'filter_text_removed': 'y'},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data
    time.sleep(sleep_time_for_fetch_thread)
    set_original(excluding='Something irrelevant')

    # A line thats not the trigger should not trigger anything
    res = client.get(url_for("form_watch_checknow"), follow_redirects=True)
    assert b'1 watches queued for rechecking.' in res.data
    time.sleep(sleep_time_for_fetch_thread)
    res = client.get(url_for("index"))
    assert b'unviewed' not in res.data

    # The trigger line is REMOVED,  this should trigger
    set_original(excluding='The golden line')
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    time.sleep(sleep_time_for_fetch_thread)
    res = client.get(url_for("index"))
    assert b'unviewed' in res.data


    # Now add it back, and we should not get a trigger
    client.get(url_for("mark_all_viewed"), follow_redirects=True)
    set_original(excluding=None)
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    time.sleep(sleep_time_for_fetch_thread)
    res = client.get(url_for("index"))
    assert b'unviewed' not in res.data

    # Remove it again, and we should get a trigger
    set_original(excluding='The golden line')
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    time.sleep(sleep_time_for_fetch_thread)
    res = client.get(url_for("index"))
    assert b'unviewed' in res.data

    res = client.get(url_for("form_delete", uuid="all"), follow_redirects=True)
    assert b'Deleted' in res.data


def test_check_add_line_contains_trigger(client, live_server):

    sleep_time_for_fetch_thread = 3

    # Give the endpoint time to spin up
    time.sleep(1)
    test_notification_url = url_for('test_notification_endpoint', _external=True).replace('http://', 'post://') + "?xxx={{ watch_url }}"

    res = client.post(
        url_for("settings_page"),
        data={"application-notification_title": "New ChangeDetection.io Notification - {{ watch_url }}",
              "application-notification_body": 'triggered text was -{{triggered_text}}-',
              # https://github.com/caronc/apprise/wiki/Notify_Custom_JSON#get-parameter-manipulation
              "application-notification_urls": test_notification_url,
              "application-minutes_between_check": 180,
              "application-fetch_backend": "html_requests"
              },
        follow_redirects=True
    )
    assert b'Settings updated' in res.data

    set_original()
    # Add our URL to the import page
    test_url = url_for('test_endpoint', _external=True)
    res = client.post(
        url_for("import_page"),
        data={"urls": test_url},
        follow_redirects=True
    )
    assert b"1 Imported" in res.data

    # Give the thread time to pick it up
    time.sleep(sleep_time_for_fetch_thread)

    # Goto the edit page, add our ignore text
    # Add our URL to the import page
    res = client.post(
        url_for("edit_page", uuid="first"),
        data={"trigger_text": 'Oh yes please',
              "url": test_url,
              'fetch_backend': "html_requests",
              'filter_text_removed': '',
              'filter_text_added': 'y'},
        follow_redirects=True
    )
    assert b"Updated watch." in res.data
    time.sleep(sleep_time_for_fetch_thread)
    set_original(excluding='Something irrelevant')

    # A line thats not the trigger should not trigger anything
    res = client.get(url_for("form_watch_checknow"), follow_redirects=True)
    assert b'1 watches queued for rechecking.' in res.data
    time.sleep(sleep_time_for_fetch_thread)
    res = client.get(url_for("index"))
    assert b'unviewed' not in res.data

    # The trigger line is ADDED,  this should trigger
    set_original(add_line='<p>Oh yes please</p>')
    client.get(url_for("form_watch_checknow"), follow_redirects=True)
    time.sleep(sleep_time_for_fetch_thread)
    res = client.get(url_for("index"))
    assert b'unviewed' in res.data

    with open("test-datastore/notification.txt", 'r') as f:
        response= f.read()
        assert '-Oh yes please-' in response


    res = client.get(url_for("form_delete", uuid="all"), follow_redirects=True)
    assert b'Deleted' in res.data
