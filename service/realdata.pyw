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

    # "Tue, 21 Mar 2017 06:12:42 +1100"
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
        hour = date_and_time[16:19]
        minute = date_and_time[20:22]
        return [year, month, day, hour, minute]

    def insert_new_date(self, location_id_to_insert, cursor2, db2, date2, date_time2, city, temp2, is_raining2):
        sql_insert = "INSERT INTO temperature (min, dateTimeMin, max, dateTimeMax, date, fklocation, rain) VALUES (" + \
                     str(temp2) + ", \"" + date_time2 + "\", " + str(temp2) + ", \"" +\
                     date_time2 + "\", \"" + str(date2) + "\", " + location_id_to_insert + ", " + is_raining2 + ")"
        self.logger.debug(sql_insert)
        try:
            cursor2.execute(sql_insert)
            db2.commit()
            self.logger.info("Added new temp for %s", city)
        except Exception, ex:
            db2.rollback()
            self.logger.error("Something went wrong adding new temp: %s", str(ex))

    def run(self):
        while self.running:
            self.logger.addHandler(self.my_handler)
            places = []
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.logger.info("###### %s ######", today)
            db = None
            for wundergound in self.url_to_get[0]:
                city = wundergound[0].text
                link = wundergound[1].text
                if city not in places:
                    # Gets data from wunderground web service
                    r = None
                    try:
                        r = requests.get(link)
                        data = r.json()
                        if "error" in data["response"]:
                            self.logger.error("%s - %s: (will try next pws)", city, data["response"]["error"])
                            self.logger.error(link)
                            continue
                        places.append(city)
                        country = data["current_observation"]["observation_location"]["country_iso3166"]
                        temp = data["current_observation"]["temp_c"]
                        dateList = self.parse_date_time(data["current_observation"]["observation_time_rfc822"])
                        rain = data["current_observation"]["weather"]
                        date = str(dateList[0]) + "-" + str(dateList[1]) + "-" + str(dateList[2])
                        date_time = date + " " + str(dateList[3]) + ":" + str(dateList[4])

                        self.logger.debug("*** Data from wunderground ***")
                        self.logger.debug("city = %s", city)
                        self.logger.debug("country = %s", country)
                        self.logger.debug("temp = %s", temp)
                        self.logger.debug("date = %s-%s-%s", str(dateList[0]), str(dateList[1]), str(dateList[2]))
                        self.logger.debug("time = %s:%s", str(dateList[3]), str(dateList[4]))
                        self.logger.debug("weather = %s", rain)
                    except Exception, e:
                        self.logger.error("Couldn't get data from wunderground: %s", str(e))
                        continue
                    if float(temp) < -70.0:
                        self.logger.error("Wunderground reported %s temp. Assuming it's wrong and asking for"
                                          " a new temp", temp)
                        continue
                    if r is not None:  # checks if wunderground responded
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
                                    if rain == 'Rain' or rain == 'Drizzle':
                                        sql = "UPDATE temperature SET rain=1 WHERE date=\"" + date +\
                                              "\" AND temperature.fklocation=" + str(locationId[0][0])
                                        self.logger.debug(sql)
                                        try:
                                            cursor.execute(sql)
                                            db.commit()
                                            self.logger.info("%s is %s", city, rain)
                                        except Exception, e:
                                            db.rollback()
                                            self.logger.error("Something went wrong while updating min temp: %s", str(e))

                                # update min or max values
                                # checks temp min
                                if temp < tempData[0][1]:
                                    sql = "UPDATE temperature SET min=" + str(temp) + ", dateTimeMin=\"" +\
                                          date_time + "\" WHERE date=\"" + date + "\" AND temperature.fklocation=" +\
                                          str(locationId[0][0])
                                    self.logger.debug(sql)
                                    try:
                                        cursor.execute(sql)
                                        db.commit()
                                        self.logger.info("%s -> min temp updated! @ %s", city, date_time)
                                    except Exception, e:
                                        db.rollback()
                                        self.logger.error("Something went wrong while updating min temp: %s", str(e))
                                else:
                                    if temp > tempData[0][2]:
                                        sql = "UPDATE temperature SET max=" + str(temp) + ", dateTimeMax=\"" +\
                                              date_time + "\" WHERE date=\"" + date +\
                                              "\" AND temperature.fklocation=" + str(locationId[0][0])
                                        self.logger.debug(sql)
                                        try:
                                            cursor.execute(sql)
                                            db.commit()
                                            self.logger.info("%s -> max temp updated! @ %s", city, date_time)
                                        except Exception, e:
                                            db.rollback()
                                            self.logger.error("Something went wrong while updating max temp: %s", str(e))
                            else:
                                # insert date with min and max values
                                self.insert_new_date(str(locationId[0][0]), cursor, db, date, date_time, city, temp, "0")
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
                            self.insert_new_date(str(cursor.lastrowid), cursor, db, date, date_time, city, temp, "0")
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
