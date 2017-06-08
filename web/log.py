import sys

print "Content-type: text/html\n\n"
if len(sys.argv) == 2:
    if sys.argv[1] == "True":
        f = open('..\service\logs.txt', 'w')
        f.write("")
        f.close()
        print "The log has been cleared."

f = open('..\service\logs.txt')
for line in f:
    print line + "<br>"
f.close()
