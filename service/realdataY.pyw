import requests
import mysql.connector
import datetime
import time
import logging
import wx
import threading
import xml.etree.ElementTree
import ctypes


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon('../web/images/favicon.ico')

    def CreatePopupMenu(self):
        menu = wx.Menu()
        self.create_menu_item(menu, 'Refresh', self.on_refresh)
        self.create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def create_menu_item(self, menu, label, func):
        item = wx.MenuItem(menu, -1, label)
        menu.Bind(wx.EVT_MENU, func, id=item.GetId())
        menu.AppendItem(item)
        return item

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, 'Real Data')

    def on_exit(self, event):
        worker.running = False
        wx.CallAfter(self.Destroy)
        self.frame.Close()

    def on_refresh(self, event):
        worker.refresh = True

class App(wx.App):
    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True

# Link to get stations:
# https://www.wunderground.com/wundermap


class MyThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.running = True

        self.logger = logging.getLogger('realdata')
        self.my_handler = logging.FileHandler("logs.txt")
        formatter = logging.Formatter('%(levelname)s %(message)s')
        self.my_handler.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)

        self.url_to_get = xml.etree.ElementTree.parse('realdata.xml').getroot()
        self.refresh = False

    # "Tue, 21 Mar 2017 06:12:42 +1100" wunderground
    # "Fri, 14 Jul 2017 03:00 AM AEST" yahoo
    @staticmethod
    def parse_date_time(date_and_time):
        dict_months = {
            "Jan": "01",
            "Feb": "02",
            "Mar": "03",
            "Apr": "04",
            "May": "05",
            "Jun": "06",
            "Jul": "07",
            "Aug": "08",
            "Sep": "09",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12"
        }
        my_list = date_and_time.split(" ")
        day = my_list[1]
        month = dict_months[my_list[2]]
        year = my_list[3]
        hour = date_and_time[17:19]
        ampm = date_and_time[23:25]
        if hour == "12":
            if ampm == "AM":
                hour = "00"
        else:
            if ampm == "PM":
                hour = str(int(hour) + 12)
        minute = date_and_time[20:22]
        return [year, month, day, hour, minute]

    def insert_new_date(self, location_id_to_insert, cursor2, db2, date2, date_time2, city2, temp2, feels2,
                        is_raining2, sky2):
        sql_insert = "INSERT INTO temperature (min, minfeels, dateTimeMin, max, maxfeels, dateTimeMax, date," \
                     " fklocation, rain, sky) VALUES (" + str(temp2) + ", " + str(feels2) + ", \"" + date_time2 +\
                     "\", " + str(temp2) + ", " + str(feels2) + ", \"" + date_time2 + "\", \"" + str(date2) + "\", " +\
                     location_id_to_insert + ", " + is_raining2 + ", \"" + sky2 + "\")"
        self.logger.debug(sql_insert)
        try:
            cursor2.execute(sql_insert)
            db2.commit()
            self.logger.info("Added new temp for %s", city2)
        except Exception, ex:
            db2.rollback()
            self.logger.error("Something went wrong adding new temp: %s", str(ex))

    def update_rain(self, db2, cursor2, date2, location_id2, city2, rain2):
        sql_update = "UPDATE temperature SET rain=1 WHERE date=\"" + date2 + \
              "\" AND temperature.fklocation=" + location_id2
        self.logger.debug(sql_update)
        try:
            cursor2.execute(sql_update)
            db2.commit()
            self.logger.info("%s is %s", city2, rain2)
        except Exception, e:
            db2.rollback()
            self.logger.error("Something went wrong while updating rain: %s", str(e))

    def update_sky(self, db2, cursor2, sky2, date2, location_id2, city2):
        sql_update = "UPDATE temperature SET sky=\"" + sky2 + "\" WHERE date=\"" + date2 +\
                     "\" AND temperature.fklocation=" + location_id2
        self.logger.debug(sql_update)
        try:
            cursor2.execute(sql_update)
            db2.commit()
            self.logger.info("%s is %s", city2, sky2)
        except Exception, e:
            db2.rollback()
            self.logger.error("Something went wrong while updating sky: %s", str(e))

    def update_temp(self, db2, cursor2, fieldtemp, temp2, fieldfeels, feels2, fielddatetime, date_time2, date2, location_id2, city2):
        sql_update = "UPDATE temperature SET " + fieldtemp + "=" + str(temp2) + ", " + fieldfeels + "=" + feels2 + \
              ", " + fielddatetime + "=\"" + date_time2 + "\" WHERE date=\"" + \
              date2 + "\" AND temperature.fklocation=" + location_id2
        self.logger.debug(sql_update)
        try:
            cursor2.execute(sql_update)
            db2.commit()
            self.logger.info("%s -> %s temp updated! @ %s -> %s", city2, fieldtemp, date_time2, temp2)
        except Exception, e:
            db2.rollback()
            self.logger.error("Something went wrong while updating %s temp: %s", fieldtemp, str(e))

    def run(self):
        while self.running:
            self.logger.addHandler(self.my_handler)
            places = []
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.logger.info("###### %s ######", today)
            db = None
            for yahoo in self.url_to_get[1]:
                city = yahoo[0].text
                link = yahoo[1].text
                if city not in places:
                    # Gets data from yahoo web service
                    try:
                        r = requests.get(link)
                        data = r.json()
                        data = data["query"]["results"]["channel"]
                        places.append(city)
                        country = data["location"]["country"]
                        temp = data["item"]["condition"]["temp"]
                        sky = data["item"]["condition"]["text"]
                        dateList = self.parse_date_time(data["item"]["condition"]["date"])
                        code = int(data["item"]["condition"]["code"])
                        feels = str(int(round((int(data["wind"]["chill"]) - 32) / 1.8, 0)))
                        rain = False
                        if 0 <= code <= 18 or code == 35 or 37 <= code <= 43 or 45 <= code <= 47:
                            rain = True
                        date = str(dateList[0]) + "-" + str(dateList[1]) + "-" + str(dateList[2])
                        date_time = date + " " + str(dateList[3]) + ":" + str(dateList[4])

                        self.logger.debug("*** Data from yahoo ***")
                        self.logger.debug("city = %s", city)
                        self.logger.debug("country = %s", country)
                        self.logger.debug("temp = %s", temp)
                        self.logger.debug("date = %s-%s-%s", str(dateList[0]), str(dateList[1]), str(dateList[2]))
                        self.logger.debug("time = %s:%s", str(dateList[3]), str(dateList[4]))
                        self.logger.debug("weather = %s", rain)
                    except Exception, e:
                        self.logger.error("Couldn't get data from yahoo: %s", str(e))
                        self.logger.error(r.json())
                        continue
                    if float(temp) < -70.0:
                        self.logger.error("Yahoo reported %s temp. Assuming it's wrong and asking for"
                                          " a new temp", temp)
                        continue
                    if r is not None:  # checks if yahoo responded
                        # Initiates connection with mysql database
                        if db is None:
                            db = mysql.connector.connect(user='root', password='root', host='localhost',
                                                         database='weather')
                            cursor = db.cursor()

                        # Gets locationID from database
                        sql = "SELECT idlocation FROM location WHERE location.city=\"" + city +\
                              "\" AND location.country=\"" + country + "\""
                        self.logger.debug(sql)
                        cursor.execute(sql)
                        locationId = cursor.fetchall()
                        self.logger.debug("locationId = %s", locationId)

                        # Checks if city exists
                        if len(locationId) > 0:
                            # City exists, now gets today's temperature
                            sql = "SELECT temperature.idtemperature, temperature.min, temperature.max," \
                                  " temperature.rain FROM temperature WHERE temperature.date=\"" + date +\
                                  "\" AND temperature.fklocation=" + str(locationId[0][0])
                            self.logger.debug(sql)
                            cursor.execute(sql)
                            tempData = cursor.fetchall()
                            self.logger.debug("tempData = %s", tempData)
                            # checks if there is temp for today
                            if len(tempData) > 0:
                                # update whether or not it's raining today
                                # rain => 1  ****   no rain => 0
                                if tempData[0][3] == 0:
                                    if rain:
                                        self.update_rain(db, cursor, date, str(locationId[0][0]), city, rain)
                                self.update_sky(db, cursor, sky, date, str(locationId[0][0]), city)
                                # update min or max values
                                # checks temp min
                                if float(temp) < tempData[0][1]:
                                    self.update_temp(db, cursor, "min", str(temp), "minfeels", str(feels),
                                                     "dateTimeMin", date_time, date, str(locationId[0][0]), city)
                                else:
                                    if float(temp) > tempData[0][2]:
                                        self.update_temp(db, cursor, "max", str(temp), "maxfeels", str(feels),
                                                         "dateTimeMax", date_time, date, str(locationId[0][0]), city)
                            else:
                                # insert date with min and max values
                                self.insert_new_date(str(locationId[0][0]), cursor, db, date, date_time, city, temp,
                                                     feels, "0", sky)
                        else:  # city does not exist
                            sql = "INSERT INTO location (location.city, location.country) VALUES (\"" + city +\
                                  "\", \"" + country + "\")"
                            self.logger.debug(sql)
                            try:
                                cursor.execute(sql)
                                db.commit()
                                self.logger.info("%s city added!", city)
                            except Exception, e:
                                db.rollback()
                                self.logger.error("Something went wrong adding city %s", city)
                                self.logger.error(str(e))
                            # insert date with min and max values
                            self.insert_new_date(str(cursor.lastrowid), cursor, db, date, date_time, city, temp,
                                                 feels, "0", sky)
            if db is not None:
                db.close()
            # to not have to wait for 15 min for the thread to exit, it breaks down to 15 sec and checks the flag
            # 60 * 15 = 900 seconds which is 15 minutes
            count = 60
            while count > 0:
                if len(self.logger.handlers) > 0:
                    self.logger.handlers[0].close()
                time.sleep(15)
                count -= 1
                if not self.running:
                    ctypes.windll.user32.MessageBoxW(0, u"Real Data has exited completely.", u"Real Data", 0 | 200000)
                    break
                if self.refresh:
                    self.refresh = False
                    ctypes.windll.user32.MessageBoxW(0, u"Temperatures have been updated."
                                                     , u"Real Data", 0 | 200000)
                    break


worker = MyThread(1, "Worker")
worker.start()
app = App(False)
app.MainLoop()
