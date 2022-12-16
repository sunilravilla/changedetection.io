import yagmail
import json
import time
import schedule
import os
import pandas as pd
from pretty_html_table import build_table
from datetime import datetime
from datetime import timedelta


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
        # clear console output
        os.system('cls' if os.name == 'nt' else 'clear')

        print("send daily overview mail")
        with open(self.json_store_path+"url-watches.json") as json_file:
            from_disk = json.load(json_file)
            # pretty_print console from disk
            print(json.dumps(from_disk, indent=4, sort_keys=True))
            null = None
            false = False
            true = True
            # from_disk take watching
            # from_disk take settings
            new_array = []
            failed_count = 0
            for key in from_disk['watching']:
                # read value for each key and add value new array
                temp = from_disk['watching'][key]
                # open key folder and read history.txt
                if temp['last_error'] == False:
                    read_file = open(
                        self.json_store_path + key + "\\history.txt", "r")
                    # read file
                    read_file = read_file.read()
                    # split file
                    data = read_file.split(",")
                    temp['last_changed'] = data[0]

                    new_array.append(temp)
                else:
                    temp['last_changed'] = 0
                    new_array.append(temp)
                    failed_count += 1
            # print new array
            print(new_array)
            main_array = new_array
            # filter new array last_changed is less than 24 hours
            new_array = list(
                filter(lambda x: int(x['last_changed']) > int(time.time() - 86400), new_array))
            # count no of items of each tag
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
            # send mail as table with headers as country and updates found with border and table hader background color as #f2f2f2 and font size as 12 and font color as #000000 and font family as Arial and font weight as bold and font style as italic
            self.body += "<table border='1' style='border-collapse: collapse;'><tr style='background-color: #f2f2f2;'><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Country</th><th style='font-size: 12px; color: #000000; font-family: Arial; font-weight: bold; font-style: italic;'>Updates Found</th></tr>"
            # for evn index differentiate with background color
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

            # read main_array in data frames
            df = pd.DataFrame(main_array)
            # find last_changed is less than 24 hours

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
