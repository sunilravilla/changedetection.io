
# HORRIBLE HACK BUT WORKS :-) PR anyone?
#
# Why?
# `browsersteps_playwright_browser_interface.chromium.connect_over_cdp()` will only run once without async()
# - this flask app is not async()
# - browserless has a single timeout/keepalive which applies to the session made at .connect_over_cdp()
#
# So it means that we must unfortunately for now just keep a single timer since .connect_over_cdp() was run
# and know when that reaches timeout/keepalive :( when that time is up, restart the connection and tell the user
# that their time is up, insert another coin. (reload)
#
# Bigger picture
# - It's horrible that we have this click+wait deal, some nice socket.io solution using something similar
# to what the browserless debug UI already gives us would be smarter..
#
# OR
# - Some API call that should be hacked into browserless or playwright that we can "/api/bump-keepalive/{session_id}/60"
# So we can tell it that we need more time (run this on each action)
#
# OR
# - use multiprocessing to bump this over to its own process and add some transport layer (queue/pipes)

from distutils.util import strtobool
from flask import Blueprint, request, make_response
import os
import logging
from changedetectionio.store import ChangeDetectionStore
from changedetectionio import login_optionally_required

browsersteps_sessions = {}
io_interface_context = None


def construct_blueprint(datastore: ChangeDetectionStore):
    browser_steps_blueprint = Blueprint('browser_steps', __name__, template_folder="templates")

    def start_browsersteps_session(watch_uuid):
        from . import nonContext
        from . import browser_steps
        import time
        global browsersteps_sessions
        global io_interface_context


        # We keep the playwright session open for many minutes
        seconds_keepalive = int(os.getenv('BROWSERSTEPS_MINUTES_KEEPALIVE', 10)) * 60

        browsersteps_start_session = {'start_time': time.time()}

        # You can only have one of these running
        # This should be very fine to leave running for the life of the application
        # @idea - Make it global so the pool of watch fetchers can use it also
        if not io_interface_context:
            io_interface_context = nonContext.c_sync_playwright()
            # Start the Playwright context, which is actually a nodejs sub-process and communicates over STDIN/STDOUT pipes
            io_interface_context = io_interface_context.start()


        # keep it alive for 10 seconds more than we advertise, sometimes it helps to keep it shutting down cleanly
        keepalive = "&timeout={}".format(((seconds_keepalive + 3) * 1000))
        try:
            browsersteps_start_session['browser'] = io_interface_context.chromium.connect_over_cdp(
                os.getenv('PLAYWRIGHT_DRIVER_URL', '') + keepalive)
        except Exception as e:
            if 'ECONNREFUSED' in str(e):
                return make_response('Unable to start the Playwright Browser session, is it running?', 401)
            else:
                return make_response(str(e), 401)

        proxy_id = datastore.get_preferred_proxy_for_watch(uuid=watch_uuid)
        proxy = None
        if proxy_id:
            proxy_url = datastore.proxy_list.get(proxy_id).get('url')
            if proxy_url:

                # Playwright needs separate username and password values
                from urllib.parse import urlparse
                parsed = urlparse(proxy_url)
                proxy = {'server': proxy_url}

                if parsed.username:
                    proxy['username'] = parsed.username

                if parsed.password:
                    proxy['password'] = parsed.password

                print("Browser Steps: UUID {} selected proxy {}".format(watch_uuid, proxy_url))

        # Tell Playwright to connect to Chrome and setup a new session via our stepper interface
        browsersteps_start_session['browserstepper'] = browser_steps.browsersteps_live_ui(
            playwright_browser=browsersteps_start_session['browser'],
            proxy=proxy)

        # For test
        #browsersteps_start_session['browserstepper'].action_goto_url(value="http://example.com?time="+str(time.time()))

        return browsersteps_start_session


    @login_optionally_required
    @browser_steps_blueprint.route("/browsersteps_start_session", methods=['GET'])
    def browsersteps_start_session():
        # A new session was requested, return sessionID

        import uuid
        global browsersteps_sessions

        browsersteps_session_id = str(uuid.uuid4())
        watch_uuid = request.args.get('uuid')

        if not watch_uuid:
            return make_response('No Watch UUID specified', 500)

        print("Starting connection with playwright")
        logging.debug("browser_steps.py connecting")
        browsersteps_sessions[browsersteps_session_id] = start_browsersteps_session(watch_uuid)
        print("Starting connection with playwright - done")
        return {'browsersteps_session_id': browsersteps_session_id}

    # A request for an action was received
    @login_optionally_required
    @browser_steps_blueprint.route("/browsersteps_update", methods=['POST'])
    def browsersteps_ui_update():
        import base64
        import playwright._impl._api_types
        global browsersteps_sessions
        from changedetectionio.blueprint.browser_steps import browser_steps

        remaining =0
        uuid = request.args.get('uuid')

        browsersteps_session_id = request.args.get('browsersteps_session_id')

        if not browsersteps_session_id:
            return make_response('No browsersteps_session_id specified', 500)

        if not browsersteps_sessions.get(browsersteps_session_id):
            return make_response('No session exists under that ID', 500)


        # Actions - step/apply/etc, do the thing and return state
        if request.method == 'POST':
            # @todo - should always be an existing session
            step_operation = request.form.get('operation')
            step_selector = request.form.get('selector')
            step_optional_value = request.form.get('optional_value')
            step_n = int(request.form.get('step_n'))
            is_last_step = strtobool(request.form.get('is_last_step'))

            if step_operation == 'Goto site':
                step_operation = 'goto_url'
                step_optional_value = datastore.data['watching'][uuid].get('url')
                step_selector = None

            # @todo try.. accept.. nice errors not popups..
            try:

                browsersteps_sessions[browsersteps_session_id]['browserstepper'].call_action(action_name=step_operation,
                                         selector=step_selector,
                                         optional_value=step_optional_value)

            except Exception as e:
                print("Exception when calling step operation", step_operation, str(e))
                # Try to find something of value to give back to the user
                return make_response(str(e).splitlines()[0], 401)

            # Get visual selector ready/update its data (also use the current filter info from the page?)
            # When the last 'apply' button was pressed
            # @todo this adds overhead because the xpath selection is happening twice
            u = browsersteps_sessions[browsersteps_session_id]['browserstepper'].page.url
            if is_last_step and u:
                (screenshot, xpath_data) = browsersteps_sessions[browsersteps_session_id]['browserstepper'].request_visualselector_data()
                datastore.save_screenshot(watch_uuid=uuid, screenshot=screenshot)
                datastore.save_xpath_data(watch_uuid=uuid, data=xpath_data)

#        if not this_session.page:
#            cleanup_playwright_session()
#            return make_response('Browser session ran out of time :( Please reload this page.', 401)

        # Screenshots and other info only needed on requesting a step (POST)
        try:
            state = browsersteps_sessions[browsersteps_session_id]['browserstepper'].get_current_state()
        except playwright._impl._api_types.Error as e:
            return make_response("Browser session ran out of time :( Please reload this page."+str(e), 401)

        # Use send_file() which is way faster than read/write loop on bytes
        import json
        from tempfile import mkstemp
        from flask import send_file
        tmp_fd, tmp_file = mkstemp(text=True, suffix=".json", prefix="changedetectionio-")

        output = json.dumps({'screenshot': "data:image/jpeg;base64,{}".format(
            base64.b64encode(state[0]).decode('ascii')),
            'xpath_data': state[1],
            'session_age_start': browsersteps_sessions[browsersteps_session_id]['browserstepper'].age_start,
            'browser_time_remaining': round(remaining)
        })

        with os.fdopen(tmp_fd, 'w') as f:
            f.write(output)

        response = make_response(send_file(path_or_file=tmp_file,
                                           mimetype='application/json; charset=UTF-8',
                                           etag=True))
        # No longer needed
        os.unlink(tmp_file)

        return response

    return browser_steps_blueprint


