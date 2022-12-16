import yagmail
import json
import time
import schedule
import os
import pandas as pd
from pretty_html_table import build_table
from datetime import datetime
from datetime import timedelta
import timeago


class DailyOverviewMail:
    def __init__(self):
        print("DailyOverviewMail init")
        print("=====================================")
        # print(self.datastore)
        self.json_store_path = "C:\\Users\\Gunasekhar\\AppData\\Roaming\\changedetection.io\\"
        # self.wait_for_next_run()
        # self.send()
        self.body = '<html><head><h>Hello <b>Team</b><br/> '
        self.body += '<p>Below are the statistics of RaiSE in the last 24 hours</p>'

    def wait_for_next_run(self):
        print("wait for next run")
        schedule.every(1).minutes.do(self.send)
        while 1:
            schedule.run_pending()
            time.sleep(1)

    def send(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("send daily overview mail")
        with open(self.json_store_path+"url-watches.json") as json_file:
            from_disk = json.load(json_file)
            print(json.dumps(from_disk, indent=4, sort_keys=True))
            null = None
            false = False
            true = True
            new_array = []
            failed_count = 0
            for key in from_disk['watching']:
                temp = from_disk['watching'][key]
                if temp['last_error'] == False:
                    read_file = open(
                        self.json_store_path + key + "\\history.txt", "r")
                    read_file = read_file.read()
                    data = read_file.split(",")
                    temp['last_changed'] = timeago.format(
                        datetime.fromtimestamp(int(data[0])), datetime.now())

                    new_array.append(temp)
                else:
                    temp['last_changed'] = None
                    new_array.append(temp)
                    failed_count += 1
            print(new_array, flush=True)

            tag_count = {}
            for item in new_array:

                if item['tag'] in tag_count:
                    tag_count[item['tag']] += 1
                else:
                    if item['tag'] == "":
                        item['tag'] = "No Tag"
                    else:
                        tag_count[item['tag']] = 1
            print(tag_count)
            self.body += "<table border='1' style='border-collapse: collapse;'><tr style='background-color: #f2f2f2;'><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Country</th><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Updates Found</th></tr>"

            for index, key in enumerate(tag_count):
                # print(key)
                # print(tag_count[key])
                if index % 2 == 0:
                    self.body += "<tr style='background-color: #f2f2f2;'><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td></tr>".format(
                        key, tag_count[key])
                else:
                    self.body += "<tr style='background-color: #ffffff;'><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td></tr>".format(
                        key, tag_count[key])

            # close table

            self.body += "</table><br><br>"
            # form new table with unique tags as Total_Countries 	count of watching as Total_websites	failed_count asFailed_Websites_Count
            self.body += "<table border='1' style='border-collapse: collapse;'><tr style='background-color: #f2f2f2;'><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Total_Countries</th><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Total_websites</th><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Failed_Websites_Count</th></tr>"
            self.body += "<tr style='background-color: #f2f2f2;'><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td><td style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>{}</td></tr>".format(
                len(tag_count), len(from_disk['watching']), failed_count)
            self.body += "</table><br><br>"

            # read main_array into dataframe
            main_array = [{'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166108, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': 'df090a6949667e94066f529a6b3b8942', 'proxy': None, 'subtractive_selectors': [], 'tag': 'China', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Human Resources & Payroll Archives - China Briefing News', 'trigger_text': [], 'url': 'https://www.china-briefing.com/news/category/human-resources-payroll/', 'uuid': 'ba24d4aa-5354-4f90-8170-3d4d4556ea08', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 5.066, 'last_changed': '1671093678'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166108, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': '82f88a7bf7a9ff3570db000f39955551', 'proxy': None, 'subtractive_selectors': [], 'tag': 'China', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'China Tax Alert - 2020 Issues - KPMG China', 'trigger_text': [], 'url': 'https://home.kpmg/cn/en/home/insights/2020/01/china-tax-alert.html', 'uuid': '851b54f2-cdb2-4275-b39b-b790a1ada845', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 8.163, 'last_changed': '1671093677'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166095, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': 'cd41d6f2f4faefc6a3105f1a0ec5e5d0', 'proxy': None, 'subtractive_selectors': [], 'tag': 'China', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Tax & Accounting Archives - China Briefing News', 'trigger_text': [], 'url': 'https://www.china-briefing.com/news/category/tax-accounting/', 'uuid': '52053b32-a331-4e87-ac67-792a5388c784', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 1.45, 'last_changed': '1671093655'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166102, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': 'c9b0dfa92f0491174ff92bac5d27f18b', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Cyprus', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Direct Tax Updates - PwC Cyprus publications', 'trigger_text': [], 'url': 'https://www.pwc.com.cy/en/publications-newsletters/direct-tax-updates.html', 'uuid': '5b1c6478-e078-4f6c-b8b6-cde5aa0e9bc2', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 8.323, 'last_changed': '1671093668'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166113, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': 'dc17c2579e67e6c2ef39221b83d769d2', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Czech_Republic', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Právo – dReport', 'trigger_text': [], 'url': 'https://www.dreport.cz/blog/category/pravo/', 'uuid': 'e405e491-199a-4f44-bc17-36672ec953e8', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 3.498, 'last_changed': '1671093685'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166084, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': '8a6fdbf786ca855cccf40f35d3b1bf94', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Czech_Republic', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Insights - KPMG Global', 'trigger_text': [], 'url': 'https://home.kpmg/xx/en/home/insights.html', 'uuid': '1e4b86f0-d204-43e4-b363-e35227bdeee6', 'webdriver_delay': None, 'webdriver_js_execute_code': None,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 4.592, 'last_changed': '1671093637'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': None, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166095, 'last_error': 'Got HTML content but no text found (With 200 reply code).', 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': False, 'proxy': None, 'subtractive_selectors': [], 'tag': 'East_Timor', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': None, 'trigger_text': [], 'url': 'https://www.taxathand.com/world-news/Timor-Leste', 'uuid': '5abe0a1e-f589-4c98-9837-8ba27db639c2', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'fetch_time': 0.991, 'last_changed': ''}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166108, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': '97f2cc68b4652b03f3bfeabfb1edb704', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Egypt', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Middle East Tax & Legal News', 'trigger_text': [], 'url': 'https://www.pwc.com/m1/en/services/tax/me-tax-legal-news.html?tags32142=%7B%22tags%22%3A%5B%5B%22pwc%3Ageography%2Fmiddle_east%2Fegypt%22%5D%5D%7D', 'uuid': 'b7ba3819-3066-4046-8138-12bb5308c3fe', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 4.807, 'last_changed': '1671093679'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166115, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': '0f8cd704baa3e94abfddbcc62f91b539', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Egypt', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Tax Alerts | EY - Global', 'trigger_text': [], 'url': 'https://www.ey.com/en_gl/tax-alerts', 'uuid': 'cbf83cb8-c7a6-4f79-80f9-25038dfddf50', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 5.449, 'last_changed': '1671093688'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166108, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': '0fcfe28c2eb50762d519b619b2ce9b0a', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Hong_Kong', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'Mandatory Provident Fund Schemes Authority - MPFA', 'trigger_text': [], 'url': 'https://www.mpfa.org.hk/eng/main/index.jsp', 'uuid': 'a530942f-4283-4d87-a25f-fe8e16782d42', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 5.187, 'last_changed': '1671093678'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': False, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166084, 'last_error': False, 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': 'ca8bf1c14a1ef462b327243b9919f6bc', 'proxy': None, 'subtractive_selectors': [], 'tag': 'Indonesia', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': 'PwC Indonesia', 'trigger_text': [], 'url': 'https://www.pwc.com/id/en/', 'uuid': '13802d90-11f9-4d18-8f8e-2d12a7fe7cac', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'last_notification_error': False, 'last_check_status': 200, 'fetch_time': 4.477, 'last_changed': '1671093633'}, {'body': None, 'check_unique_lines': False, 'check_count': 4, 'consecutive_filter_failures': 0, 'extract_text': [], 'extract_title_as_title': False, 'fetch_backend': 'html_requests', 'filter_failure_notification_send': 1, 'has_ldjson_price_data': None, 'track_ldjson_price_data': None, 'headers': {}, 'ignore_text': [], 'include_filters': [], 'last_checked': 1671166110, 'last_error': 'Got HTML content but no text found (With 200 reply code).', 'last_viewed': 0, 'method': 'GET', 'notification_body': None, 'notification_format': 'System default', 'notification_muted': False, 'notification_title': None, 'notification_screenshot': False, 'notification_urls': [], 'paused': False, 'previous_md5': False, 'proxy': None, 'subtractive_selectors': [], 'tag': 'Indonesia', 'text_should_not_be_present': [], 'time_between_check': {'weeks': None, 'days': None, 'hours': None, 'minutes': None, 'seconds': None}, 'title': None, 'trigger_text': [], 'url': 'https://www.taxathand.com/world-news/Indonesia', 'uuid': 'dc71d6b2-97b4-4950-8115-1092cafcebb0', 'webdriver_delay': None, 'webdriver_js_execute_code': None, 'fetch_time': 0.633, 'last_changed': ''}]
            df = pd.DataFrame(main_array)
            # filter last_changed is less than 24 hours in
            df = df.sort_values(by=['last_changed'], ascending=False)
            # print(df)
            # convert df to html
            self.body += build_table(df, 'blue_light')

            # need table with unique tag as country	no of websites in unique Total_Websites_Count	no of ['last_error'] != False as Failed_Websites_Count	no of ['last_error'] == FalseSuccessful_Websites_Count from from_disk['watching']
            # load values from_disk['watching'] dataFrame
            df = pd.DataFrame.from_dict(from_disk['watching'], orient='index')
            # country as tag no of websites in with same tag as Total_Websites_Count
            # create new_df with tag as index
            new_df = df.groupby('tag').size().reset_index(
                name='Total_Websites_Count')
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Total_Websites_Count'] = new_df['Total_Websites_Count'].astype(
                int)
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Failed_Websites_Count'] = new_df['tag'].apply(
                lambda x: len(df[(df['tag'] == x) & (df['last_error'] != False)]))
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Successful_Websites_Count'] = new_df['tag'].apply(
                lambda x: len(df[(df['tag'] == x) & (df['last_error'] == False)]))
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Total_Websites_Count'] = new_df['tag'].apply(
                lambda x: len(df[(df['tag'] == x)]))
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Failed_Websites_Count'] = new_df['Failed_Websites_Count'].astype(
                int)
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Successful_Websites_Count'] = new_df['Successful_Websites_Count'].astype(
                int)
            # add new column with no of websites in with same tag as Total_Websites_Count
            new_df['Total_Websites_Count'] = new_df['Total_Websites_Count'].astype(
                int)

            # rename tag as country
            new_df.rename(columns={'tag': 'country'}, inplace=True)
            # set country as index
            # new_df.set_index('country', inplace=True)
            # print(new_df)
            # tohtml with table style black and white background
            text1 = build_table(new_df, 'grey_dark')
            self.body += text1.replace('\n', '')
            # print(new_df)
            # print(new_df)

            # load new_df2 last_error != False and Title', default='No Title' url as url and tag as country and last_error as error and last_check as last_check and last_changed as status
            new_df2 = df[df['last_error'] != False][
                ['tag', 'url', 'title', 'last_error', 'last_checked']]
            # rename tag as country
            new_df2.rename(columns={'tag': 'country'}, inplace=True)
            # rename last_error as error
            new_df2.rename(columns={'last_error': 'error'}, inplace=True)
            # rename last_check as last_check
            new_df2.rename(
                columns={'last_checked': 'last_check'}, inplace=True)
            # convert last_check to datetime
            new_df2['last_check'] = pd.to_datetime(
                new_df2['last_check'], unit='s')
            # convert last_check to datetime
            new_df2['last_check'] = new_df2['last_check'].dt.strftime(
                '%Y-%m-%d %H:%M:%S')

            print(new_df2)
            # add br to self.body
            self.body += "<br><br>"
            text2 = build_table(new_df2, 'grey_dark')
            self.body += text2.replace('\n', '')
            # thanks and end of mail
            self.body += "<p>Thanks & Regards,<br>Team <b>RaiSE</b></p>"
            self.body += "<p>Powered by <b>ILAB</b>.</p>"
            self.body += "<p><a href='https://www.ramco.com'>Ramco Systems</a></p>"
            self.body += "<p> contact: <a href = 'mailto:aimlops@ramco.com' >Contact</a></p>"
            self.body += "</body></html>"

            yag = yagmail.SMTP('aimlops@ramco.com', "kJ@Rv34*xV3",
                               host='smtp.office365.com', port=587, smtp_starttls=True, smtp_ssl=False)
            # print(">> Process Notification: Yagmail notifying {}".format(n_body))
            subject = "RaiSE -Daily Overview Mail - {}".format(
                datetime.now().strftime("%d-%m-%Y"))
            yag.send(to="14607@ramco.com",
                     subject=subject, contents=self.body)
            print(new_array)
            # filter new


if __name__ == "__main__":
    initiate = DailyOverviewMail()
    initiate.send()
