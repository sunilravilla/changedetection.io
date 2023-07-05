#!/usr/bin/python3

import os
import time
import re
from random import randint

# Two flags, tell the JS which of the "Selector" or "Value" field should be enabled in the front end
# 0- off, 1- on
browser_step_ui_config = {'Choose one': '0 0',
                          #                 'Check checkbox': '1 0',
                          #                 'Click button containing text': '0 1',
                          #                 'Scroll to bottom': '0 0',
                          #                 'Scroll to element': '1 0',
                          #                 'Scroll to top': '0 0',
                          #                 'Switch to iFrame by index number': '0 1'
                          #                 'Uncheck checkbox': '1 0',
                          # @todo
                          'Check checkbox': '1 0',
                          'Click X,Y': '0 1',
                          'Click element if exists': '1 0',
                          'Click element': '1 0',
                          'Click element containing text': '0 1',
                          'Enter text in field': '1 1',
                          'Execute JS': '0 1',
#                          'Extract text and use as filter': '1 0',
                          'Goto site': '0 0',
                          'Goto URL': '0 1',
                          'Press Enter': '0 0',
                          'Select by label': '1 1',
                          'Scroll down': '0 0',
                          'Uncheck checkbox': '1 0',
                          'Wait for seconds': '0 1',
                          'Wait for text': '0 1',
                          'Wait for text in element': '1 1',
                          #                          'Press Page Down': '0 0',
                          #                          'Press Page Up': '0 0',
                          # weird bug, come back to it later
                          }


# Good reference - https://playwright.dev/python/docs/input
#                  https://pythonmana.com/2021/12/202112162236307035.html
#
# ONLY Works in Playwright because we need the fullscreen screenshot
class steppable_browser_interface():
    page = None

    # Convert and perform "Click Button" for example
    def call_action(self, action_name, selector=None, optional_value=None):
        now = time.time()
        call_action_name = re.sub('[^0-9a-zA-Z]+', '_', action_name.lower())
        if call_action_name == 'choose_one':
            return

        print("> action calling", call_action_name)
        # https://playwright.dev/python/docs/selectors#xpath-selectors
        if selector and selector.startswith('/') and not selector.startswith('//'):
            selector = "xpath=" + selector

        action_handler = getattr(self, "action_" + call_action_name)

        # Support for Jinja2 variables in the value and selector
        from jinja2 import Environment
        jinja2_env = Environment(extensions=['jinja2_time.TimeExtension'])

        if selector and ('{%' in selector or '{{' in selector):
            selector = str(jinja2_env.from_string(selector).render())

        if optional_value and ('{%' in optional_value or '{{' in optional_value):
            optional_value = str(jinja2_env.from_string(optional_value).render())

        action_handler(selector, optional_value)
        self.page.wait_for_timeout(1.5 * 1000)
        print("Call action done in", time.time() - now)

    def action_goto_url(self, selector=None, value=None):
        # self.page.set_viewport_size({"width": 1280, "height": 5000})
        now = time.time()
        response = self.page.goto(value, timeout=0, wait_until='commit')

        # Wait_until = commit
        # - `'commit'` - consider operation to be finished when network response is received and the document started loading.
        # Better to not use any smarts from Playwright and just wait an arbitrary number of seconds
        # This seemed to solve nearly all 'TimeoutErrors'
        print("Time to goto URL ", time.time() - now)

    def action_click_element_containing_text(self, selector=None, value=''):
        if not len(value.strip()):
            return
        elem = self.page.get_by_text(value)
        if elem.count():
            elem.first.click(delay=randint(200, 500), timeout=3000)

    def action_enter_text_in_field(self, selector, value):
        if not len(selector.strip()):
            return

        self.page.fill(selector, value, timeout=10 * 1000)

    def action_execute_js(self, selector, value):
        self.page.evaluate(value)

    def action_click_element(self, selector, value):
        print("Clicking element")
        if not len(selector.strip()):
            return

        self.page.click(selector=selector, timeout=30 * 1000, delay=randint(200, 500))

    def action_click_element_if_exists(self, selector, value):
        import playwright._impl._api_types as _api_types
        print("Clicking element if exists")
        if not len(selector.strip()):
            return
        try:
            self.page.click(selector, timeout=10 * 1000, delay=randint(200, 500))
        except _api_types.TimeoutError as e:
            return
        except _api_types.Error as e:
            # Element was there, but page redrew and now its long long gone
            return

    def action_click_x_y(self, selector, value):
        x, y = value.strip().split(',')
        x = int(float(x.strip()))
        y = int(float(y.strip()))
        self.page.mouse.click(x=x, y=y, delay=randint(200, 500))

    def action_scroll_down(self, selector, value):
        # Some sites this doesnt work on for some reason
        self.page.mouse.wheel(0, 600)
        self.page.wait_for_timeout(1000)

    def action_wait_for_seconds(self, selector, value):
        self.page.wait_for_timeout(float(value.strip()) * 1000)

    def action_wait_for_text(self, selector, value):
        import json
        v = json.dumps(value)
        self.page.wait_for_function(f'document.querySelector("body").innerText.includes({v});', timeout=90000)

    def action_wait_for_text_in_element(self, selector, value):
        import json
        s = json.dumps(selector)
        v = json.dumps(value)
        self.page.wait_for_function(f'document.querySelector({s}).innerText.includes({v});', timeout=90000)

    # @todo - in the future make some popout interface to capture what needs to be set
    # https://playwright.dev/python/docs/api/class-keyboard
    def action_press_enter(self, selector, value):
        self.page.keyboard.press("Enter", delay=randint(200, 500))

    def action_press_page_up(self, selector, value):
        self.page.keyboard.press("PageUp", delay=randint(200, 500))

    def action_press_page_down(self, selector, value):
        self.page.keyboard.press("PageDown", delay=randint(200, 500))

    def action_check_checkbox(self, selector, value):
        self.page.locator(selector).check(timeout=1000)

    def action_uncheck_checkbox(self, selector, value):
        self.page.locator(selector, timeout=1000).uncheck(timeout=1000)


# Responsible for maintaining a live 'context' with browserless
# @todo - how long do contexts live for anyway?
class browsersteps_live_ui(steppable_browser_interface):
    context = None
    page = None
    render_extra_delay = 1
    stale = False
    # bump and kill this if idle after X sec
    age_start = 0

    # use a special driver, maybe locally etc
    command_executor = os.getenv(
        "PLAYWRIGHT_BROWSERSTEPS_DRIVER_URL"
    )
    # if not..
    if not command_executor:
        command_executor = os.getenv(
            "PLAYWRIGHT_DRIVER_URL",
            'ws://playwright-chrome:3000'
        ).strip('"')

    browser_type = os.getenv("PLAYWRIGHT_BROWSER_TYPE", 'chromium').strip('"')

    def __init__(self, playwright_browser, proxy=None):
        self.age_start = time.time()
        self.playwright_browser = playwright_browser
        if self.context is None:
            self.connect(proxy=proxy)

    # Connect and setup a new context
    def connect(self, proxy=None):
        # Should only get called once - test that
        keep_open = 1000 * 60 * 5
        now = time.time()

        # @todo handle multiple contexts, bind a unique id from the browser on each req?
        self.context = self.playwright_browser.new_context(
            # @todo
            #                user_agent=request_headers['User-Agent'] if request_headers.get('User-Agent') else 'Mozilla/5.0',
            #               proxy=self.proxy,
            # This is needed to enable JavaScript execution on GitHub and others
            bypass_csp=True,
            # Should never be needed
            accept_downloads=False,
            proxy=proxy
        )

        self.page = self.context.new_page()

        # self.page.set_default_navigation_timeout(keep_open)
        self.page.set_default_timeout(keep_open)
        # @todo probably this doesnt work
        self.page.on(
            "close",
            self.mark_as_closed,
        )
        # Listen for all console events and handle errors
        self.page.on("console", lambda msg: print(f"Browser steps console - {msg.type}: {msg.text} {msg.args}"))

        print("Time to browser setup", time.time() - now)
        self.page.wait_for_timeout(1 * 1000)

    def mark_as_closed(self):
        print("Page closed, cleaning up..")

    @property
    def has_expired(self):
        if not self.page:
            return True


    def get_current_state(self):
        """Return the screenshot and interactive elements mapping, generally always called after action_()"""
        from pkg_resources import resource_string
        xpath_element_js = resource_string(__name__, "../../res/xpath_element_scraper.js").decode('utf-8')
        now = time.time()
        self.page.wait_for_timeout(1 * 1000)

        # The actual screenshot
        screenshot = self.page.screenshot(type='jpeg', full_page=True, quality=40)

        self.page.evaluate("var include_filters=''")
        # Go find the interactive elements
        # @todo in the future, something smarter that can scan for elements with .click/focus etc event handlers?
        elements = 'a,button,input,select,textarea,i,th,td,p,li,h1,h2,h3,h4,div,span'
        xpath_element_js = xpath_element_js.replace('%ELEMENTS%', elements)
        xpath_data = self.page.evaluate("async () => {" + xpath_element_js + "}")
        # So the JS will find the smallest one first
        xpath_data['size_pos'] = sorted(xpath_data['size_pos'], key=lambda k: k['width'] * k['height'], reverse=True)
        print("Time to complete get_current_state of browser", time.time() - now)
        # except
        # playwright._impl._api_types.Error: Browser closed.
        # @todo show some countdown timer?
        return (screenshot, xpath_data)

    def request_visualselector_data(self):
        """
        Does the same that the playwright operation in content_fetcher does
        This is used to just bump the VisualSelector data so it' ready to go if they click on the tab
        @todo refactor and remove duplicate code, add include_filters
        :param xpath_data:
        :param screenshot:
        :param current_include_filters:
        :return:
        """

        self.page.evaluate("var include_filters=''")
        from pkg_resources import resource_string
        # The code that scrapes elements and makes a list of elements/size/position to click on in the VisualSelector
        xpath_element_js = resource_string(__name__, "../../res/xpath_element_scraper.js").decode('utf-8')
        from changedetectionio.content_fetcher import visualselector_xpath_selectors
        xpath_element_js = xpath_element_js.replace('%ELEMENTS%', visualselector_xpath_selectors)
        xpath_data = self.page.evaluate("async () => {" + xpath_element_js + "}")
        screenshot = self.page.screenshot(type='jpeg', full_page=True, quality=int(os.getenv("PLAYWRIGHT_SCREENSHOT_QUALITY", 72)))

        return (screenshot, xpath_data)
