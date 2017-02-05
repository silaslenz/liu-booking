import requests
import json

with open('liu.json') as data_file:    
    config = json.load(data_file)
username = config["username"]
password = config["password"]


def logmein(username,password):
    session = requests.Session()
    # fake som visits to normal pages
    
    session.get("https://se.timeedit.net/web/liu/db1/timeedit/sso/?ssoserver=liu_stud_cas&entry=wr_stud&back=https%3A%2F%2Fse.timeedit.net%2Fweb%2Fliu%2Fdb1%2Fwr_stud%2F")

    loginpage = session.get("https://login.liu.se/cas/login?service=https%3A%2F%2Fse.timeedit.net%2Fweb%2Fliu%2Fdb1%2Ftimeedit%2FssoResponse")

    # Extract form data
    lt = loginpage.text.split('<input type="hidden" name="lt" value="')[1].split('"')[0] # No idea what this stuff is, but is part of form data
    execution = loginpage.text.split('<input type="hidden" name="execution" value="')[1].split('" />')[0] # Seems to be execution and session number in format e#s#

    print(lt,execution)

    # Aquired some neat session cookies on the way
    print (session.cookies)

    signed_in = session.post("https://login.liu.se/cas/login;jsessionid=B8622F07E9C48D0C40DA58D17D9ECE18?service=https%3A%2F%2Fse.timeedit.net%2Fweb%2Fliu%2Fdb1%2Ftimeedit%2FssoResponse",\
                                data = {'username':username,'password':password, 'lt':lt,'execution':execution, '_eventId':'submit', 'submit':'LOGIN'})

    if "Välkommen till Lokalbokning" in signed_in.text:
        print ("Sign in successful")
    else:
        print ("You fucked up")
    return session


def get_buildings(session):
    bookingpage = session.get("https://se.timeedit.net/web/liu/db1/wr_stud/ri1Q8.html")
    buildings = [i.split('">')[1].split('</option')[0] for i in bookingpage.text.split('data-name="Building"')[1].split('</select>')[0].split('<option value="')[1:]]
    return buildings    


def get_bookable_from_campus(session, campus, date, starttime, endtime, houses):
    #https://se.timeedit.net/web/liu/db1/wr_stud/objects.json?max=50&fr=f&part=t&partajax=t&im=f&step=1&sid=4&l=sv_SE&types=195&subtypes=230,231&fe=23.Valla&dates=20170122-20170122&starttime=8:0&endtime=10:0
    #https://se.timeedit.net/web/liu/db1/wr_stud/objects.json?max=50&fr=f&part=t&partajax=t&im=f&step=1&sid=4&l=sv_SE&types=195&subtypes=230,231&fe=26.A-huset,C-Huset&fe=23.Valla&dates=20170122-20170122&starttime=8:0&endtime=10:0
    return session.get("https://se.timeedit.net/web/liu/db1/wr_stud/objects.json?max=50&fr=f&part=t&partajax=t&im=f&step=1&sid=4&l=en&types=195&subtypes=230,231&fe=26." + houses + "&fe=23."+campus+"&dates="+date+"-"+date+"&starttime="+starttime+":0&endtime="+endtime+":0").json()


def get_bookingpage(session, roomid):
    return session.get("https://se.timeedit.net/web/liu/db1/wr_stud/ri1Q8.html#00"+roomid)


def get_userid(session):
    return session.get("https://se.timeedit.net/web/liu/db1/wr_stud/objects.html?max=10&fr=t&partajax=t&im=f&sid=4&l=en&search_text="+username+"&types=184&subtypes=184&step=1").text.split('data-id="')[1].split('"')[0]


def reserve(session, date, starttime, endtime, roomid, userid):
    """
    Param date: yyyymmdd
    Param starttime: hh:mm
    """
    formdata = {'kind':'reserve', 'nocache':'4','l':'en','o':userid+","+roomid,'aos':'',\
                        'dates':date,'starttime':starttime,'endtime':endtime,\
                        'url':'https://se.timeedit.net/web/liu/db1/wr_stud/ri1Q8.html#00'+roomid.split('.')[0],'fe7':''}
    print(formdata)
    return session.post("https://se.timeedit.net/web/liu/db1/wr_stud/ri1Q8.html#00"+roomid.split('.')[0],data=formdata)



session = logmein(username, password)

# Id from first room in list (AG21)
date = "20170207"
starttime = "10"
endtime = "14"
bookable = get_bookable_from_campus(session, "Valla", date, starttime, endtime, "C-Huset,Key")
print(bookable)
firstItem = bookable["objects"][0]["fields"]["Name (web)"]
print(firstItem)
import slackweb
channel = slackweb.Slack("supersecret")
channel.notify(text = "Booked " + firstItem  + " from " + starttime + " to " + endtime)
# Book first result 
reserve(session, date, starttime, endtime, firstItem, get_userid(session))
