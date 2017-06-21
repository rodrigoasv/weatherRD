import mysql.connector
import sys
import json


cnx = mysql.connector.connect(user='root', password='root',
                              host='localhost',
                              database='weather', charset="utf8", use_unicode=True)


def get_cities():
    cursor = cnx.cursor()
    cursor.execute("select idlocation, city from location")
    available_cities = cursor.fetchall()

    ret_cities = []
    for city in available_cities:
        if city[0] == 1:
            global json_ret
            json_ret['text'] = city[1]

        ret_cities.append({'id': str(city[0]), 'name': city[1]})
    return ret_cities


json_ret = {}
json_ret['cities'] = get_cities()

city_id = json_ret['cities'][0]['id']
if len(sys.argv) == 2:
    if len(sys.argv[1]) <= 2:
        city_id = str(sys.argv[1])
        for city in json_ret['cities']:
            if city['id'] == city_id:
                json_ret['text'] = city['name']

cursor = cnx.cursor()
cursor.execute("select temperature.date from temperature, location where rain=1 and location.idlocation=" + city_id +
               " and temperature.fklocation=location.idlocation order by temperature.date")
rain_days = cursor.fetchall()
days = []
for each in rain_days:
    split = str(each[0]).split("-")
    year = int(split[0])
    month = int(split[1]) - 1
    day = int(split[2])
    days.append({'year': year, 'month': month, 'day': day})

print "Content-type: text/html\n\n"


json_ret['days'] = days

print json.dumps(json_ret)
