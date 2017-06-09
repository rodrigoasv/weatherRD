import sys
import os.path

fname = '../service/logs.txt'
print "Content-type: text/html\n\n"

if os.path.isfile(fname):
    if len(sys.argv) == 2:
        if sys.argv[1] == "True":
            f = open(fname, 'w')
            f.write("")
            f.close()
            print "The log has been cleared."

    f = open(fname)
    for line in f:
        print line + "<br>"
    f.close()
else:
    print "The log is empty."