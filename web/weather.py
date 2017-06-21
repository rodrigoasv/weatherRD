#!c:/Python27/python.exe -u
import mysql.connector
import datetime
import sys
import json

dictMonths = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }
cnx = mysql.connector.connect(user='root', password='root',
                              host='localhost',
                              database='weather', charset="utf8", use_unicode=True)


def add_months_for_filter():
    cursor = cnx.cursor()
    cursor.execute("select distinct EXTRACT(year from date), EXTRACT(month from date) from temperature")
    available_months = cursor.fetchall()
    ret = []
    for e_month in available_months:
        label = dictMonths[e_month[1]] + '-' + str(e_month[0])
        if e_month[1] > 10:
            ret.append({'param': str(e_month[1]), 'label': label})
        else:
            ret.append({'param': str(e_month[0]) + '-0' + str(e_month[1]), 'label': label})
    return ret


def get_table(q):
    cursor = cnx.cursor()
    cursor.execute(q)
    # get header and rows
    header = [i[0] for i in cursor.description]
    rows = [list(i) for i in cursor.fetchall()]
    # append header to rows
    rows.insert(0, header)
    cursor.close()
    cnx.close()

    ret = []
    for row in rows:
        child = []
        for item in row:
            child.append(str(item))
        ret.append(child)

    return ret


current_month = datetime.datetime.now().strftime("%Y-%m")
if len(sys.argv) == 2:
    if len(sys.argv[1]) == 7:
        current_month = sys.argv[1]
query = "SELECT temp.date as 'Date', loc.city as 'City', temp.min as 'Temp Min'," \
        " CAST(temp.dateTimeMin as time) as 'Time', temp.max as 'Temp Max'," \
        " CAST(temp.dateTimeMax as time) as 'Time' FROM weather.temperature" \
        " as temp, weather.location as loc WHERE temp.fklocation=loc.idlocation AND temp.date LIKE '" + current_month +\
        "%' ORDER BY temp.date, loc.city"
dropdown_selected = dictMonths[int(current_month[5:7])] + "-" + current_month[0:4]

print "Content-type: text/html\n\n"

json_ret = {}

# text of the dropdown selected
json_ret['text'] = dropdown_selected

# monthList
json_ret['filter'] = add_months_for_filter()

# tables
json_ret['table'] = get_table(query)

print json.dumps(json_ret)
