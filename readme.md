
# **Weather Real Data**
**Author:** *Rodrigo Victor*


### **Description:**
This project was made as a need that I had to have real historic temperatures. I always had the feeling that the historic data showed on the weather web sites were not correct, so I've created this to satisfy myself. In addition, I wanted to see the differences between min and max temperatures from different cities.

### **Technologies:**
- python
- mysql
- html, javascript, jquery, css
- Bootstrap
- Bootstrap Year Calendar

### **Layers:**
- service
- web page

---

## **Real Data Service**


### **Description:**
The service needs to be running to get the data from Weather Underground API.
Although it's written in Python, it uses Windows DLLs in order to create an icon on the taskbar (next to the clock) with a tiny menu to make simple operations, like Refresh and Exit.

### **Requirements:**
- MySQL configured
- XML with correct urls and keys
- A few imports for Python:
	- mysql.connector
	- wx
- In order to create an exe windows file, you will need py2exe and do appropriate adjusts in `setup.py`

---

## **Web Page**

### **Description:**
This is basically the web page that shows in a table all temperatures for all cities configured in a given month.
It was also written in Python to get the data from MySQL database.
