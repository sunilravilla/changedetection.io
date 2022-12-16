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
import threading as threading


class DailyOverview:
    def __init__(self, datastore_path):
        self.email = os.environ.get('EMAIL') or 'aimlops@ramco.com'
        self.password = os.environ.get('EMAIL_PASSWORD') or 'kJ@Rv34*xV3'
        self.recipient = os.environ.get('RECIPIENTS') or '14607@ramco.com'
        self.developer = os.environ.get('DEVELOPER_MAIL') or '14607@ramco.com'
        self.triggerTime = os.environ.get('TRIGGERTIME') or '08:00'
        self.yag = yagmail.SMTP(self.email, self.password, host='smtp.office365.com',
                                port=587, smtp_starttls=True, smtp_ssl=False)
        self.subject = 'RaiSE Daily Overview' + \
            str(datetime.now().strftime('%Y-%m-%d'))
        self.body = 'This is the RaiSE statistics overview in the last 24 hours.'
        self.html = ''
        self.json_store_path = datastore_path or 'C:/Users/Gunasekhar/AppData/Roaming/changedetection.io'
        self.changes = []
        # self.getData()
        # self.SendEmail()
        # create the thread to run the schedule
        self.thread = threading.Thread(target=self.Schedule)
        self.thread.start()
        # self.Schedule()

    def getData(self):
        self.changes = []
        self.data = {}
        with open(self.json_store_path+"/url-watches.json") as json_file:
            self.data = json.load(json_file)
            # print(json.dumps(self.data, indent=4, sort_keys=True))
            self.processData()

    def processData(self):
        for key, value in self.data['watching'].items():
            # convert last_checked to timeago
            timea = timeago.format(value['last_checked'], datetime.now())
            self.data['watching'][key]['last_checked'] = timea
            # read last_changed from history.txt file in uuid folder if folder exists
            if os.path.exists(self.json_store_path+'/'+key + "/history.txt"):
                with open(self.json_store_path+'/'+key+"/history.txt") as history_file:
                    history = history_file.readlines()
                    last_changed = history[-1].split(',')[0]
                    # convert timestamp to date
                    last_changed = datetime.fromtimestamp(
                        int(last_changed)).strftime('%Y-%m-%d %H:%M:%S')
                    # convert datetime to timeago
                    last_changedago = timeago.format(
                        last_changed, datetime.now())
                    # print(last_changed)
                    self.data['watching'][key]['last_changed'] = last_changedago
                    # if last changed is less than 24 hours ago, add to changes
                    # filter changes by last_changed when last_changed is less than 24 hours ago

                    if last_changed > str(datetime.now() - timedelta(days=1)):
                        self.changes.append(self.data['watching'][key])
        self.SendEmail()

    def Schedule(self):
        print('Scheduling')
        schedule.every().day.at(self.triggerTime).do(self.getData)
        # schedule.every(1).minutes.do(self.getData)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def SendEmail(self):
        self.GetHtml()
        try:
            sent = self.yag.send(self.recipient, self.subject,
                                 contents=self.body+self.html)
            print('Email sent')

        except Exception as e:
            self.yag.send(self.developer, self.subject,
                          contents='RaiSE Error in sending Overview email'+str(e))
        # after sending email, clear self.changes

    def GetHtml(self):
        self.html = ''
        self.html += self.GetOverview()
        # add br
        self.html += '<br><br>'
        self.html += self.GetTotalCounts()
        # add br
        self.html += '<br><br>'
        self.html += self.GetCountrywise()
        # add br
        self.html += '<br><br>'
        self.html += self.GetFailedUrls()
        self.html += "<p>Thanks & Regards,<br>Team <b>RaiSE</b></p>"
        self.html += "<p>Powered by <b>ILAB</b>.</p>"
        self.html += "<p><a href='https://www.ramco.com'>Ramco Systems</a></p>"
        self.html += "<p> contact: <a href = 'mailto:aimlops@ramco.com' >Contact</a></p>"
        self.html += "</body></html>"

    def GetOverview(self):
        # if self.changes len is 0, return no changes
        if len(self.changes) == 0:
            return "<h2>No Changes in the last 24 hours</h2>"
        print('Getting overview')
        # load self.changes into dataframe
        #
        df = pd.DataFrame(self.changes)
        # df = df.transpose()
        print(df)
        # fill '' cells in tag columns with 'No Tag'
        df['tag'] = df['tag'].replace('', '--No Tag--')
        # group by tags and count the number of changes in each tag
        df = df.groupby('tag').count()
        # create new df with only the tag and check_count columns
        df = df[['check_count']]
        # rename check_count to count
        df = df.rename(columns={'check_count': 'Update_Found'})

        # remove tag as index
        df = df.reset_index()
        # rename tag as country
        df = df.rename(columns={'tag': 'country'})
        # build table
        table = build_table(df, 'blue_light')
        # replace \n in table
        table = table.replace('\n', '')
        # return table
        # print(df)
        return table

    def GetTotalCounts(self):
        # laod self.data into dataframe
        df = pd.DataFrame(self.data['watching'])
        print(df)
        df = df.transpose()
        # filter last_error is not equal to False
        failed_count = len(df[df['last_error'] != False])
        # filter last_error is not equal to False
        website = len(self.data['watching'])
        unique_countries = len(df['tag'].unique())
        df1 = pd.DataFrame({'Total_Countries': unique_countries, 'Total_Websites': [website], 'Total_Failed': [
                           failed_count], 'Total_Success': [website-failed_count]})
        print(df)
        print(df1)
        return build_table(df1, 'blue_light').replace('\n', '')

    def GetCountrywise(self):
        # laod self.data into dataframe
        df = pd.DataFrame(self.data['watching'])
        # country as tag no of websites in with same tag as Total_Websites_Count
        # create new_df with tag as index
        df = df.transpose()
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
        # rename tag "" to No Tag
        new_df['tag'] = new_df['tag'].replace('', '--No Tag--')

        # rename tag as country
        new_df.rename(columns={'tag': 'country'}, inplace=True)
        # set country as index
        # new_df.set_index('country', inplace=True)
        # print(new_df)
        # tohtml with table style black and white background
        text1 = build_table(new_df, 'grey_dark')
        return text1.replace('\n', '')

    def GetFailedUrls(self):
        # laod self.data into dataframe
        df = pd.DataFrame(self.data['watching'])
        # country as tag no of websites in with same tag as Total_Websites_Count
        # create new_df with tag as index
        df = df.transpose()
        # filter last_error is not equal to False
        df = df[df['last_error'] != False][
            ['tag', 'url', 'title', 'last_error', 'last_checked']]
        # print(df)
        # tohtml with table style black and white background
        text1 = build_table(df, 'grey_dark')
        return text1.replace('\n', '')


if __name__ == '__main__':
    dailyOverview = DailyOverview()
    # dailyOverview.getData()
