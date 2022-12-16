from distutils.util import strtobool
import logging
import os
import time
import uuid

minimum_seconds_recheck_time = int(os.getenv('MINIMUM_SECONDS_RECHECK_TIME', 60))
mtable = {'seconds': 1, 'minutes': 60, 'hours': 3600, 'days': 86400, 'weeks': 86400 * 7}

from changedetectionio.notification import (
    default_notification_format_for_watch
)


class model(dict):
    __newest_history_key = None
    __history_n = 0
    __base_config = {
        # 'history': {},  # Dict of timestamp and output stripped filename (removed)
        # 'newest_history_key': 0, (removed, taken from history.txt index)
        'body': None,
        'check_unique_lines': False,  # On change-detected, compare against all history if its something new
        'check_count': 0,
        'consecutive_filter_failures': 0,  # Every time the CSS/xPath filter cannot be located, reset when all is fine.
        'extract_text': [],  # Extract text by regex after filters
        'extract_title_as_title': False,
        'fetch_backend': None,
        'filter_failure_notification_send': strtobool(os.getenv('FILTER_FAILURE_NOTIFICATION_SEND_DEFAULT', 'True')),
        'has_ldjson_price_data': None,
        'track_ldjson_price_data': None,
        'headers': {},  # Extra headers to send
        'ignore_text': [],  # List of text to ignore when calculating the comparison checksum
        'include_filters': [],
        'last_checked': 0,
        'last_error': False,
        'last_viewed': 0,  # history key value of the last viewed via the [diff] link
        'method': 'GET',
        # Custom notification content
        'notification_body': None,
        'notification_format': default_notification_format_for_watch,
        'notification_muted': False,
        'notification_title': None,
        'notification_screenshot': False,  # Include the latest screenshot if available and supported by the apprise URL
        'notification_urls': [],  # List of URLs to add to the notification Queue (Usually AppRise)
        'paused': False,
        'previous_md5': False,
        'previous_md5_before_filters': False,  # Used for skipping changedetection entirely
        'proxy': None,  # Preferred proxy connection
        'subtractive_selectors': [],
        'tag': None,
        'text_should_not_be_present': [],  # Text that should not present
        # Re #110, so then if this is set to None, we know to use the default value instead
        # Requires setting to None on submit if it's the same as the default
        # Should be all None by default, so we use the system default in this case.
        'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None},
        'title': None,
        'trigger_text': [],  # List of text or regex to wait for until a change is detected
        'url': None,
        'uuid': str(uuid.uuid4()),
        'webdriver_delay': None,
        'webdriver_js_execute_code': None,  # Run before change-detection
    }
    jitter_seconds = 0

    def __init__(self, *arg, **kw):

        self.update(self.__base_config)
        self.__datastore_path = kw['datastore_path']

        self['uuid'] = str(uuid.uuid4())

        del kw['datastore_path']

        if kw.get('default'):
            self.update(kw['default'])
            del kw['default']

        # Be sure the cached timestamp is ready
        bump = self.history

        # Goes at the end so we update the default object with the initialiser
        super(model, self).__init__(*arg, **kw)

    @property
    def viewed(self):
        if int(self['last_viewed']) >= int(self.newest_history_key) :
            return True

        return False

    def ensure_data_dir_exists(self):
        if not os.path.isdir(self.watch_data_dir):
            print ("> Creating data dir {}".format(self.watch_data_dir))
            os.mkdir(self.watch_data_dir)

    @property
    def link(self):
        url = self.get('url', '')
        ready_url = url
        if '{%' in url or '{{' in url:
            from jinja2 import Environment
            # Jinja2 available in URLs along with https://pypi.org/project/jinja2-time/
            jinja2_env = Environment(extensions=['jinja2_time.TimeExtension'])
            try:
                ready_url = str(jinja2_env.from_string(url).render())
            except Exception as e:
                from flask import (
                    flash, Markup, url_for
                )
                message = Markup('<a href="{}#general">The URL {} is invalid and cannot be used, click to edit</a>'.format(
                    url_for('edit_page', uuid=self.get('uuid')), self.get('url', '')))
                flash(message, 'error')
                return ''

        return ready_url

    @property
    def label(self):
        # Used for sorting
        if self['title']:
            return self['title']
        return self['url']

    @property
    def last_changed(self):
        # last_changed will be the newest snapshot, but when we have just one snapshot, it should be 0
        if self.__history_n <= 1:
            return 0
        if self.__newest_history_key:
            return int(self.__newest_history_key)
        return 0

    @property
    def history_n(self):
        return self.__history_n

    @property
    def history(self):
        """History index is just a text file as a list
            {watch-uuid}/history.txt

            contains a list like

            {epoch-time},{filename}\n

            We read in this list as the history information

        """
        tmp_history = {}

        # Read the history file as a dict
        fname = os.path.join(self.watch_data_dir, "history.txt")
        if os.path.isfile(fname):
            logging.debug("Reading history index " + str(time.time()))
            with open(fname, "r") as f:
                for i in f.readlines():
                    if ',' in i:
                        k, v = i.strip().split(',', 2)

                        # The index history could contain a relative path, so we need to make the fullpath
                        # so that python can read it
                        if not '/' in v and not '\'' in v:
                            v = os.path.join(self.watch_data_dir, v)
                        else:
                            # It's possible that they moved the datadir on older versions
                            # So the snapshot exists but is in a different path
                            snapshot_fname = v.split('/')[-1]
                            proposed_new_path = os.path.join(self.watch_data_dir, snapshot_fname)
                            if not os.path.exists(v) and os.path.exists(proposed_new_path):
                                v = proposed_new_path

                        tmp_history[k] = v

        if len(tmp_history):
            self.__newest_history_key = list(tmp_history.keys())[-1]

        self.__history_n = len(tmp_history)

        return tmp_history

    @property
    def has_history(self):
        fname = os.path.join(self.watch_data_dir, "history.txt")
        return os.path.isfile(fname)

    # Returns the newest key, but if theres only 1 record, then it's counted as not being new, so return 0.
    @property
    def newest_history_key(self):
        if self.__newest_history_key is not None:
            return self.__newest_history_key

        if len(self.history) <= 1:
            return 0


        bump = self.history
        return self.__newest_history_key

    # Save some text file to the appropriate path and bump the history
    # result_obj from fetch_site_status.run()
    def save_history_text(self, contents, timestamp):

        self.ensure_data_dir_exists()

        # Small hack so that we sleep just enough to allow 1 second  between history snapshots
        # this is because history.txt indexes/keys snapshots by epoch seconds and we dont want dupe keys
        if self.__newest_history_key and int(timestamp) == int(self.__newest_history_key):
            time.sleep(timestamp - self.__newest_history_key)

        snapshot_fname = "{}.txt".format(str(uuid.uuid4()))

        # in /diff/ and /preview/ we are going to assume for now that it's UTF-8 when reading
        # most sites are utf-8 and some are even broken utf-8
        with open(os.path.join(self.watch_data_dir, snapshot_fname), 'wb') as f:
            f.write(contents)
            f.close()

        # Append to index
        # @todo check last char was \n
        index_fname = os.path.join(self.watch_data_dir, "history.txt")
        with open(index_fname, 'a') as f:
            f.write("{},{}\n".format(timestamp, snapshot_fname))
            f.close()

        self.__newest_history_key = timestamp
        self.__history_n += 1

        # @todo bump static cache of the last timestamp so we dont need to examine the file to set a proper ''viewed'' status
        return snapshot_fname

    @property
    def has_empty_checktime(self):
        # using all() + dictionary comprehension
        # Check if all values are 0 in dictionary
        res = all(x == None or x == False or x==0 for x in self.get('time_between_check', {}).values())
        return res

    def threshold_seconds(self):
        seconds = 0
        for m, n in mtable.items():
            x = self.get('time_between_check', {}).get(m, None)
            if x:
                seconds += x * n
        return seconds

    # Iterate over all history texts and see if something new exists
    def lines_contain_something_unique_compared_to_history(self, lines: list):
        local_lines = set([l.decode('utf-8').strip().lower() for l in lines])

        # Compare each lines (set) against each history text file (set) looking for something new..
        existing_history = set({})
        for k, v in self.history.items():
            alist = set([line.decode('utf-8').strip().lower() for line in open(v, 'rb')])
            existing_history = existing_history.union(alist)

        # Check that everything in local_lines(new stuff) already exists in existing_history - it should
        # if not, something new happened
        return not local_lines.issubset(existing_history)

    def get_screenshot(self):
        fname = os.path.join(self.watch_data_dir, "last-screenshot.png")
        if os.path.isfile(fname):
            return fname

        # False is not an option for AppRise, must be type None
        return None

    def get_screenshot_as_jpeg(self):

        # Created by save_screenshot()
        fname = os.path.join(self.watch_data_dir, "last-screenshot.jpg")
        if os.path.isfile(fname):
            return fname

        # False is not an option for AppRise, must be type None
        return None


    def __get_file_ctime(self, filename):
        fname = os.path.join(self.watch_data_dir, filename)
        if os.path.isfile(fname):
            return int(os.path.getmtime(fname))
        return False

    @property
    def error_text_ctime(self):
        return self.__get_file_ctime('last-error.txt')

    @property
    def snapshot_text_ctime(self):
        if self.history_n==0:
            return False

        timestamp = list(self.history.keys())[-1]
        return int(timestamp)

    @property
    def snapshot_screenshot_ctime(self):
        return self.__get_file_ctime('last-screenshot.png')

    @property
    def snapshot_error_screenshot_ctime(self):
        return self.__get_file_ctime('last-error-screenshot.png')

    @property
    def watch_data_dir(self):
        # The base dir of the watch data
        return os.path.join(self.__datastore_path, self['uuid'])
    
    def get_error_text(self):
        """Return the text saved from a previous request that resulted in a non-200 error"""
        fname = os.path.join(self.watch_data_dir, "last-error.txt")
        if os.path.isfile(fname):
            with open(fname, 'r') as f:
                return f.read()
        return False

    def get_error_snapshot(self):
        """Return path to the screenshot that resulted in a non-200 error"""
        fname = os.path.join(self.watch_data_dir, "last-error-screenshot.png")
        if os.path.isfile(fname):
            return fname
        return False

    def extract_regex_from_all_history(self, regex):
        import csv
        import re
        import datetime
        csv_output_filename = False
        csv_writer = False
        f = None

        # self.history will be keyed with the full path
        for k, fname in self.history.items():
            if os.path.isfile(fname):
                with open(fname, "r") as f:
                    contents = f.read()
                    res = re.findall(regex, contents, re.MULTILINE)
                    if res:
                        if not csv_writer:
                            # A file on the disk can be transferred much faster via flask than a string reply
                            csv_output_filename = 'report.csv'
                            f = open(os.path.join(self.watch_data_dir, csv_output_filename), 'w')
                            # @todo some headers in the future
                            #fieldnames = ['Epoch seconds', 'Date']
                            csv_writer = csv.writer(f,
                                                    delimiter=',',
                                                    quotechar='"',
                                                    quoting=csv.QUOTE_MINIMAL,
                                                    #fieldnames=fieldnames
                                                    )
                            csv_writer.writerow(['Epoch seconds', 'Date'])
                            # csv_writer.writeheader()

                        date_str = datetime.datetime.fromtimestamp(int(k)).strftime('%Y-%m-%d %H:%M:%S')
                        for r in res:
                            row = [k, date_str]
                            if isinstance(r, str):
                                row.append(r)
                            else:
                                row+=r
                            csv_writer.writerow(row)

        if f:
            f.close()

        return csv_output_filename
