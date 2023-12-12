import hashlib
from flask import Flask, render_template, session, flash, redirect, url_for, request, Markup
import sqlite3 as sql
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = "s3secret"


def connectSQL():
    conn = sql.connect(r"/Users/suhninlwin/Visual Studio Code/G-5 Project OBBMS/db.db")
    conn.row_factory = sql.Row
    return conn


@app.route("/home")
def homeView():
    return render_template("home.html")


@app.route("/backtouserhome")
def backToHome():
    username = session.get("accId")
    with connectSQL() as conn:
        curor = conn.cursor()
        curor.execute("SELECT Account.userId AS 'aid', Account.accRole AS 'urole', Account.accEmail AS 'aemail', User.userId AS 'uid', User.userAge AS 'uage', User.userBloodtype AS 'ubtype', User.userGender AS 'ugender', User.userPhone AS 'uphone' FROM Account, User WHERE Account.userId=User.userId AND Account.accEmail=?", (username,))
        profiledata = curor.fetchone()
        cursor = conn.cursor()
        cursor.execute("SELECT History.donarName, History.recptName, History.bloodAmt, History.histDate, History.histStatus FROM History INNER JOIN User ON History.userId = User.userId WHERE User.userId IN (SELECT Account.userId FROM Account WHERE Account.accEmail=?)", (username,))
        historydata = cursor.fetchall()
        cur = conn.cursor()
        cur.execute("SELECT History.recptName, History.donarName, User.userBloodtype, User.userId, Account.accEmail FROM User, History, Account WHERE User.userId=History.userId AND Account.userId=User.userId AND User.userBloodtype=?", (profiledata[5],))
        donorrecptlist = cur.fetchall()
        donate_cursor = conn.cursor()
        donate_cursor.execute("SELECT History.donarName, History.recptName, History.histDate, History.histStatus, User.userBloodtype, User.userPhone FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.donarName is not '-'",(profiledata[5],))
        donorlist = donate_cursor.fetchall()
        recpt_cursor = conn.cursor()
        recpt_cursor.execute("SELECT History.recptName, History.donarName, History.histDate, History.histStatus, User.userBloodtype, User.userPhone FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.recptName is not '-'",(profiledata[5],))
        recptlist = recpt_cursor.fetchall()
        donate_count = conn.cursor()
        donate_count.execute("SELECT COUNT(History.donarName) AS 'countrows' FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.donarName is not '-'",(profiledata[5],))
        donorcount = donate_count.fetchone()
        recpt_count = conn.cursor()
        recpt_count.execute("SELECT COUNT(History.recptName) AS 'countrows' FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.recptName is not '-'",(profiledata[5],))
        recptcount = recpt_count.fetchone()
        return render_template("userHome.html", username=username, profiledata=profiledata, historydata=historydata, donorrecptlist=donorrecptlist, donorlist=donorlist, donorcount=donorcount, recptlist=recptlist, recptcount=recptcount)


@app.route("/aboutus")
def aboutUsView():
    return render_template("aboutUs.html")


@app.route("/donatecamp")
def donateCampView():
    return render_template("donateCamp.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form["username"]
        password = request.form["password"]
        repassword = request.form["repassword"]
        role = "user"
        if password == repassword:
            hashpass = hashlib.md5(password.encode("utf-8")).hexdigest()
            with connectSQL() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Account WHERE accEmail=?", (username,))
                rows = cursor.fetchone() 
                if rows is not None:
                    flash("Email has already registered!")
                    return redirect(url_for("login"))
                else:
                    cursor.execute("INSERT INTO Account (accEmail, accPassword, accRole) VALUES (?,?,?)", (username, hashpass, role))
                    if cursor.rowcount > 0:
                        flash("Your account registeration is successful!")
                return redirect(url_for("login"))
        else:
            flash("You must enter password correctly for two times.")
            return redirect(url_for("register")) 


@app.route("/insertinfo", methods=["GET", "POST"])
def insertInfo():
    accid = session.get("accId")
    age = request.args.get("age")
    gender = request.args.get("gender")
    phone = request.args.get("phone")
    bloodtype = request.args.get("bloodtype")
    session["btype"] = bloodtype
    if gender in ["female", "Female", "FEMALE", "f", "F"]:
        gender = "Female"
    else:
        gender = "Male"
    with connectSQL() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO User (userAge, userGender, userPhone, userBloodType) VALUES (?,?,?,?)", (age, gender, phone, bloodtype))
        cursor.execute("SELECT userId FROM User WHERE userAge=? AND userGender=? AND userPhone=? AND userBloodType=?", (age, gender, phone, bloodtype))
        uid = cursor.fetchone()
        uid = uid[0]
        cusr = conn.cursor()
        cusr.execute("UPDATE Account SET userId=? WHERE accEmail=?", (int(uid), accid))
        return render_template("backToHome.html") 


@app.route("/editprofile", methods=["GET", "POST"])
def editProfile():
    accid = session["accId"]
    modifyage = request.form["modage"]
    modifyphone = request.form["modphone"]
    print(modifyage)
    print(modifyphone)
    with connectSQL() as conn:
        csr = conn.cursor()
        csr.execute("UPDATE User SET userAge=?, userPhone=? WHERE userId IN ( SELECT userId FROM Account WHERE accEmail=?)", (modifyage, modifyphone, accid))
        flash("Your profile has changed! THANK YOU!", "success")
        return render_template("backToHome.html") 


@app.route("/donateblood", methods=["GET", "POST"])
def donateBlood():
    donorname = session.get("accId")
    print(donorname)
    donorbamt = request.args.get("donorbamt")
    donordonatedate = request.args.get("donordonatedate")
    middletime = datetime(int(donordonatedate.split("-")[0]),int(donordonatedate.split("-")[1]),int(donordonatedate.split("-")[-1]))
    middle = middletime.strftime("%Y-%m-%d")
    print("user insert date = "+donordonatedate)
    with connectSQL() as conn:
        qrybtype = conn.cursor()
        qrybtype.execute("SELECT bloodGroup FROM Blood INNER JOIN User ON Blood.bloodGroup = User.userBloodtype WHERE User.userId IN (SELECT userId FROM Account WHERE accEmail=?)", (donorname,))
        donorbtype = qrybtype.fetchone()
        donorbtype = donorbtype[0]
        print(donorbtype)
        csr = conn.cursor()
        csr.execute("SELECT History.histDate FROM History JOIN User ON History.userId = User.userId JOIN Account ON User.userId = Account.userId JOIN Blood ON Blood.bloodId = History.bloodId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.donarName is not '-' AND History.donarName=? ORDER BY History.hisId DESC LIMIT 1",(donorbtype, donorname))
        donatedate = csr.fetchone()
        if donatedate is not None:
            donatedstrdate = donatedate[0]
            print(donatedstrdate)
            starttime = datetime(int(donatedstrdate.split("-")[0]),int(donatedstrdate.split("-")[1]),int(donatedstrdate.split("-")[-1]))
            start = starttime.strftime("%Y-%m-%d")
            endtime = str(date(int(donatedstrdate.split("-")[0]),int(donatedstrdate.split("-")[1]),int(donatedstrdate.split("-")[-1])) + relativedelta(months=+4))
            endtime = datetime(int(endtime.split("-")[0]),int(endtime.split("-")[1]),int(endtime.split("-")[-1]))
            end = endtime.strftime("%Y-%m-%d")
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT bloodId FROM Blood INNER JOIN User ON Blood.bloodGroup = User.userBloodtype WHERE User.userId IN (SELECT userId FROM Account WHERE accEmail=?)", (donorname,))
            btype = cursor.fetchone()
            btype = btype[0]
            cursor = conn.cursor()
            cursor.execute("SELECT bloodAmt FROM Blood WHERE bloodId=?", (btype,))
            bloodamt = cursor.fetchone()
            bloodamt = bloodamt[0]
            totalbloodamt = int(bloodamt)+int(donorbamt)
            cursor = conn.cursor()
            cursor.execute("UPDATE Blood SET bloodAmt=? WHERE bloodId=?", (totalbloodamt,btype))
            csr = conn.cursor()
            csr.execute("SELECT userId from Account WHERE accEmail=?", (donorname,))
            uid = csr.fetchone()
            cursor.execute("INSERT INTO History (bloodId, recptName, donarName, bloodAmt, histDate, histStatus, docId, userId) VALUES (?,?,?,?,?,?,?,?)", (btype, "-", donorname, donorbamt, donordonatedate, "donate", 1, uid[0]))
            cursor.execute("INSERT INTO Notification (notiType, notiStatus, notiCmt, userId) VALUES (?,?,?,?)", ("Donate Blood", "Donate", "None", uid[0]))
            flash("You have successfully handed over blood donation form. THANK YOU!", "success")
            return render_template("backToHome.html") 
    if start<middle:
        print("start "+start)
        print("middle "+middle)
        if middle<end:
            flash("You can't donate within four months! We appreciate your kindness but your health comes first. Please come again after a month. See you, our hero!", "warning")
            return render_template("backToHome.html")
        else:
            with connectSQL() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT bloodId FROM Blood INNER JOIN User ON Blood.bloodGroup = User.userBloodtype WHERE User.userId IN (SELECT userId FROM Account WHERE accEmail=?)", (donorname,))
                btype = cursor.fetchone()
                btype = btype[0]
                cursor = conn.cursor()
                cursor.execute("SELECT bloodAmt FROM Blood WHERE bloodId=?", (btype,))
                bloodamt = cursor.fetchone()
                bloodamt = bloodamt[0]
                totalbloodamt = int(bloodamt)+int(donorbamt)
                print(f"{bloodamt} + {donorbamt} = {totalbloodamt}")
                print(f"Bloodtype is {btype}")
                cursor = conn.cursor()
                cursor.execute("UPDATE Blood SET bloodAmt=?, bloodDesc=? WHERE bloodId=?", (totalbloodamt, "None", btype))
                csr = conn.cursor()
                csr.execute("SELECT userId from Account WHERE accEmail=?", (donorname,))
                uid = csr.fetchone()
                cursor.execute("INSERT INTO History (bloodId, recptName, donarName, bloodAmt, histDate, histStatus, docId, userId) VALUES (?,?,?,?,?,?,?,?)", (btype, "-", donorname, donorbamt, donordonatedate, "donate", 1, uid[0]))
                flash("You have successfully handed over blood donation form. THANK YOU!", "success")
                return render_template("backToHome.html")
    else:
        flash("You can't enter past dates. Please try to submit the form again. Thank You!", "warning")
        return render_template("backToHome.html")


@app.route("/requestblood", methods=["GET", "POST"])
def requestBlood():
    recptname = session.get("accId")
    recptreceivedate = request.args.get("recptreceivedate")
    recptstatus = request.args.get("recptstatus")
    if recptstatus == "urgent":
        receivebamt = 450
    else:
        receivebamt = 350
    with connectSQL() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT bloodId FROM Blood INNER JOIN User ON Blood.bloodGroup = User.userBloodtype WHERE User.userId IN (SELECT userId FROM Account WHERE accEmail=?)", (recptname,))
        btype = cursor.fetchone()
        btype = btype[0]
        cursor.execute("SELECT bloodAmt FROM Blood WHERE bloodId=?", (btype,))
        bloodamt = cursor.fetchone()
        bloodamt = bloodamt[0]
        totalbloodamt = int(bloodamt)-int(receivebamt)
        if totalbloodamt < 0:
            flash("You can't request blood now due to lack of blood amount for your blood type! We're sorry about that.", "warning")
            return render_template("backToHome.html") 
        else:
            with connectSQL() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Blood SET bloodAmt=? WHERE bloodId=?", (totalbloodamt,btype))
                csr = conn.cursor()
                csr.execute("SELECT userId from Account WHERE accEmail=?", (recptname,))
                uid = csr.fetchone()
                cursor.execute("INSERT INTO History (bloodId, recptName, donarName, bloodAmt, histDate, histStatus, docId, userId) VALUES (?,?,?,?,?,?,?,?)", (btype, recptname, "-", receivebamt, recptreceivedate, recptstatus, 2, uid[0]))
                cursor.execute("INSERT INTO Notification (notiType, notiStatus, notiCmt, userId) VALUES (?,?,?,?)", ("Request Blood", recptstatus, "None", uid[0]))
                flash("You have successfully handed over blood request form. THANK YOU!", "success")
                return render_template("backToHome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form["username"]
        password = request.form["password"]
        flag = False
        with connectSQL() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Account WHERE accEmail=?", (username,))
            rows = cursor.fetchone()

            if rows is not None:
                hashpass = hashlib.md5(password.encode("utf-8")).hexdigest()
                if rows[2] == hashpass:
                    accRole = rows[3]
                    flag = True
                    session["accId"] = username
                else:
                    flash("Wrong password. Please try again!", "warning")
            else:
                flash("Email hasn't registered yet. Please register first!", "warning")
                return render_template("register.html")
        if flag:
            if accRole == "admin":
                with connectSQL() as conn:
                    accursor = conn.cursor()
                    accursor.execute("SELECT * FROM Account")
                    accrows = accursor.fetchall()
                    bldcursor = conn.cursor()
                    bldcursor.execute("SELECT * FROM Blood")
                    bldrows = bldcursor.fetchall()
                    doccursor = conn.cursor()
                    doccursor.execute("SELECT * FROM Doctor")
                    docrows = doccursor.fetchall()
                    hiscursor = conn.cursor()
                    hiscursor.execute("SELECT * FROM History")
                    hisrows = hiscursor.fetchall()
                    noticursor = conn.cursor()
                    noticursor.execute("SELECT * FROM Notification")
                    notirows = noticursor.fetchall()
                    usrcursor = conn.cursor()
                    usrcursor.execute("SELECT * FROM User")
                    usrrows = usrcursor.fetchall()
                    coursor = conn.execute("SELECT Account.accEmail AS 'email', Account.accPassword AS 'psw', Account.accRole AS 'role' FROM Account WHERE Account.userId IS NULL AND Account.accRole='user'")
                    noninfo = coursor.fetchall()
                    cur = conn.execute("SELECT Account.accEmail AS 'email', Account.accPassword AS 'psw', Account.accRole AS 'role', User.userGender AS 'genter', User.userAge AS 'age', User.userBloodtype AS 'bt', User.userPhone AS 'phone' FROM Account, User WHERE Account.userId=User.userId")
                    infouser = cur.fetchall()
                    cour = conn.execute("SELECT History.donarName As 'donarName',History.recptName AS 'rename', User.userBloodtype AS 'ubloodtype', History.histDate AS 'hisdate', History.histStatus AS 'hisstatus'FROM History,User WHERE History.userId=User.userId")
                    activeuser = cour.fetchall()
                    cour1 = conn.execute("SELECT Account.accEmail AS 'email', User.userGender AS 'ugenter'FROM User INNER JOIN Account ON User.userId = Account.userId WHERE User.userId NOT IN (SELECT History.userId FROM History)")
                    userwithoutactivity = cour1.fetchall()
                    cour2 = conn.execute("SELECT Blood.bloodGroup AS 'bloodgroup', COUNT(*) AS 'count' FROM Blood INNER JOIN History ON History.bloodId=Blood.bloodId GROUP BY Blood.bloodGroup ORDER BY count DESC")
                    mostlydonatebloodtype = cour2.fetchall()
                flash("[Admin] Login Success!")
                return render_template("adminHome.html", username=username, noninfo=noninfo, infouser=infouser, activeuser=activeuser, userwithoutactivity=userwithoutactivity, mostlydonatebloodtype=mostlydonatebloodtype, acc=accrows , bld=bldrows , doc=docrows , his=hisrows , noti=notirows , usr=usrrows)
            elif accRole == "user":
                with connectSQL() as connect:
                    cursor = connect.cursor()
                    cursor.execute("SELECT Account.userId AS 'aid', Account.accRole AS 'urole', Account.accEmail AS 'aemail', User.userId AS 'uid', User.userAge AS 'uage', User.userBloodtype AS 'ubtype', User.userGender AS 'ugender', User.userPhone AS 'uphone' FROM Account, User WHERE Account.userId=User.userId AND Account.accEmail=?", (username,))
                    profiledata = cursor.fetchone()
                    if profiledata != None:
                        session["aid"] = profiledata[0]
                        session["urole"] = profiledata[1]
                        session["aemail"] = profiledata[2]
                        session["uid"] = profiledata[3]
                        session["uage"] = profiledata[4]
                        session["bloodtype"] = profiledata[5]
                        session["ugender"] = profiledata[6]
                        session["uphone"] = profiledata[7]
                        cusr = connect.cursor()
                        cusr.execute("SELECT History.donarName, History.recptName, History.bloodAmt, History.histDate, History.histStatus FROM History INNER JOIN User ON History.userId = User.userId WHERE User.userId IN (SELECT Account.userId FROM Account WHERE Account.accEmail=?)", (profiledata[2],))
                        historydata = cusr.fetchall()
                        cur = connect.cursor()
                        cur.execute("SELECT History.recptName, History.donarName, User.userBloodtype, User.userId, Account.accEmail FROM User, History, Account WHERE User.userId=History.userId AND Account.userId=User.userId AND User.userBloodtype=?", (profiledata[5],))
                        donorrecptlist = cur.fetchall()
                        donate_cursor = connect.cursor()
                        donate_cursor.execute("SELECT History.donarName, History.recptName, History.histDate, History.histStatus, User.userBloodtype, User.userPhone FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.donarName is not '-'",(profiledata[5],))
                        donorlist = donate_cursor.fetchall()
                        recpt_cursor = connect.cursor()
                        recpt_cursor.execute("SELECT History.recptName, History.donarName, History.histDate, History.histStatus, User.userBloodtype, User.userPhone FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.recptName is not '-'",(profiledata[5],))
                        recptlist = recpt_cursor.fetchall()
                        donate_count = connect.cursor()
                        donate_count.execute("SELECT COUNT(History.donarName) AS 'countrows' FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.donarName is not '-'",(profiledata[5],))
                        donorcount = donate_count.fetchone()
                        recpt_count = connect.cursor()
                        recpt_count.execute("SELECT COUNT(History.recptName) AS 'countrows' FROM History INNER JOIN User ON History.userId = User.userId WHERE History.bloodId IN (SELECT Blood.bloodId FROM Blood WHERE bloodGroup=?) AND History.recptName is not '-'",(profiledata[5],))
                        recptcount = recpt_count.fetchone()
                        flash("[User] Login Success!")
                        return render_template("userHome.html", username=username, profiledata=profiledata, historydata=historydata, donorrecptlist=donorrecptlist, donorlist=donorlist, donorcount=donorcount, recptlist=recptlist, recptcount=recptcount)
                    else:
                        flash("[User] Login Success!")
                        return render_template("userHome.html", username=username, profiledata=profiledata)
            else:
                flash("Unidentified role is occured!", "danger")
        else:
            return redirect(url_for("login"))


@app.route("/adminfun")
def returnAdmin():
    username = session.get("accId")
    with connectSQL() as conn:
        accursor = conn.cursor()
        accursor.execute("SELECT * FROM Account")
        accrows = accursor.fetchall()
        bldcursor = conn.cursor()
        bldcursor.execute("SELECT * FROM Blood")
        bldrows = bldcursor.fetchall()
        doccursor = conn.cursor()
        doccursor.execute("SELECT * FROM Doctor")
        docrows = doccursor.fetchall()
        hiscursor = conn.cursor()
        hiscursor.execute("SELECT * FROM History")
        hisrows = hiscursor.fetchall()
        noticursor = conn.cursor()
        noticursor.execute("SELECT * FROM Notification")
        notirows = noticursor.fetchall()
        usrcursor = conn.cursor()
        usrcursor.execute("SELECT * FROM User")
        usrrows = usrcursor.fetchall()
        coursor = conn.execute("SELECT Account.accEmail AS 'email', Account.accPassword AS 'psw', Account.accRole AS 'role' FROM Account WHERE Account.userId IS NULL AND Account.accRole='user'")
        noninfo = coursor.fetchall()
        cur = conn.execute("SELECT Account.accEmail AS 'email', Account.accPassword AS 'psw', Account.accRole AS 'role', User.userGender AS 'genter', User.userAge AS 'age', User.userBloodtype AS 'bt', User.userPhone AS 'phone' FROM Account, User WHERE Account.userId=User.userId")
        infouser = cur.fetchall()
        cour = conn.execute("SELECT History.donarName As 'donarName',History.recptName AS 'rename', User.userBloodtype AS 'ubloodtype', History.histDate AS 'hisdate', History.histStatus AS 'hisstatus'FROM History,User WHERE History.userId=User.userId")
        activeuser = cour.fetchall()
        cour1 = conn.execute("SELECT Account.accEmail AS 'email', User.userGender AS 'ugenter'FROM User INNER JOIN Account ON User.userId = Account.userId WHERE User.userId NOT IN (SELECT History.userId FROM History)")
        userwithoutactivity = cour1.fetchall()
        cour2 = conn.execute("SELECT Blood.bloodGroup AS 'bloodgroup', COUNT(*) AS 'count' FROM Blood INNER JOIN History ON History.bloodId=Blood.bloodId GROUP BY Blood.bloodGroup ORDER BY count DESC")
        mostlydonatebloodtype = cour2.fetchall()
        return render_template("adminHome.html", username=username, noninfo=noninfo, infouser=infouser, activeuser=activeuser, userwithoutactivity=userwithoutactivity, mostlydonatebloodtype=mostlydonatebloodtype, acc=accrows , bld=bldrows , doc=docrows , his=hisrows , noti=notirows , usr=usrrows)


# start of account modify        

@app.route("/admininsertaccount", methods=["GET", "POST"])
def insertnewaccount():
    acmail = request.form["acemail"]
    acpass = request.form["acpassword"]
    accrole = "admin"
    hashpass = hashlib.md5(acpass.encode("utf-8")).hexdigest()
    with connectSQL() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Account WHERE accEmail=?", (acmail,))
        rows = cursor.fetchone() 
        if rows is not None:
            flash("Email has already registered!")
            return redirect(url_for("returnAdmin"))
        else:
            cursor.execute("INSERT INTO Account (accEmail, accPassword, accRole) VALUES (?,?,?)", (acmail, hashpass, accrole))
            flash("Insertion Success", "success")
            return redirect(url_for("returnAdmin"))

@app.route("/adminacdel", methods=["GET", "POST"])
def adminacdel():
    delaccId = int(request.form["delidname"])
    print(delaccId)
    accidlist = []
    with connectSQL() as conn:
        selcur = conn.cursor()
        selcur.execute("SELECT Account.accId FROM Account")
        acclist = selcur.fetchall()
        for i in acclist:
            accidlist.append(int(i[0]))
        if delaccId in accidlist:
            cursor = conn.cursor()
            cursor.execute("DELETE from Account where accId=?", (delaccId,))
            flash("One Account deleted")
            return redirect(url_for("returnAdmin"))
        else:
            flash("ID does not exist")
            return redirect(url_for("returnAdmin"))

@app.route("/editaccount", methods=["GET", "POST"])
def editaccount():
    toeacid = request.form["tocacid"]
    modifyacemail = request.form["tocacemail"]
    modifyacpass = request.form["tocacpass"]
    modifyacpass = hashlib.md5(modifyacpass.encode("utf-8")).hexdigest()
    modifyacrole = request.form["tocacrole"]
    with connectSQL() as conn:
        csr = conn.cursor()
        csr.execute("UPDATE Account SET accEmail=?, accPassword=?, accRole=? WHERE accId=?", (modifyacemail, modifyacpass, modifyacrole, toeacid))
        flash("Edit Success", "success")
        return redirect(url_for("returnAdmin"))

# end of account modify

# start of blood modify        

@app.route("/editblood", methods=["GET", "POST"])
def editblood():
    toebldid = request.form["tobloodid"]
    modifygrp = request.form["bloodgrp"]
    modifyblddes = request.form["bloodde"]
    modifyamount = request.form["blooda"]
    with connectSQL() as conn:
        csr = conn.cursor()
        csr.execute("UPDATE Blood SET bloodGroup=?, bloodDesc=?, bloodAmt=? WHERE bloodId=?", (modifygrp, modifyblddes, modifyamount, toebldid))
        flash("Edit Success", "success")
        return redirect(url_for("returnAdmin"))

# end of blood modify

# start of doctor modify        

@app.route("/admininsertdoc", methods=["GET", "POST"])
def insertnewdoctor():
    dname = request.form["docname"]
    demail = request.form["docemail"]
    dph = request.form["docph"]
    dhos = request.form["dochos"]
    dtime = request.form["doctime"]
    ddesc = request.form["docdesc"]
    with connectSQL() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Doctor WHERE doctEmail=?", (demail,))
        rows = cursor.fetchone() 
        if rows is not None:
            flash("Email has already registered!")
            return redirect(url_for("returnAdmin"))
        else:
            cursor.execute("INSERT INTO Doctor (doctName, doctEmail, doctPhone, doctHospital, doctTime, doctDesc) VALUES (?,?,?,?,?,?)", (dname,demail,dph,dhos,dtime,ddesc))
            return redirect(url_for("returnAdmin"))

@app.route("/admindocdel", methods=["GET", "POST"])
def admindocdel():
    deldoctorId = int(request.form["deldocidname"])
    docidlist = []
    with connectSQL() as conn:
        selcur = conn.cursor()
        selcur.execute("SELECT Doctor.doctId from Doctor")
        doclist = selcur.fetchall()
        for i in doclist:
            docidlist.append(int(i[0]))
        if deldoctorId in docidlist:
            cursor = conn.cursor()
            cursor.execute("DELETE from Doctor where doctId=?", (deldoctorId,))
            flash("One Entry Deleted")
            return redirect(url_for("returnAdmin"))
        else:
            flash("ID does not exist")
            return redirect(url_for("returnAdmin"))
  
@app.route("/editdoctor", methods=["GET", "POST"])
def editdoctor():
    toedocid = request.form["toedoctorid"]
    modifydocn = request.form["docn"]
    modifydoce = request.form["doce"]
    modifydocp = request.form["docp"]
    modifydoch = request.form["doch"]
    modifydoct = request.form["doct"]
    modifydocdes = request.form["docd"]
    with connectSQL() as conn:
        csr = conn.cursor()
        csr.execute("SELECT * FROM Doctor WHERE doctEmail=?", (modifydoce,))
        rows = csr.fetchone() 
        if rows is not None:
            flash("Email has already registered!")
            return redirect(url_for("returnAdmin"))
        else:
            csr.execute("UPDATE Doctor SET doctName=?, doctEmail=?, doctPhone=?, doctHospital=?, doctTime=?, doctDesc=? WHERE doctId=?", (modifydocn, modifydoce, modifydocp, modifydoch, modifydoct, modifydocdes, toedocid))
            flash("Edit Success", "success")
            return redirect(url_for("returnAdmin"))

# end of doctor modify

# start of user modify        

@app.route("/admininsertuser", methods=["GET", "POST"])
def insertnewuser():
    userage = request.form["age"]
    usergen = request.form["gen"]
    userph = request.form["ph"]
    userblood = request.form["utype"]
    if usergen in ["female", "Female", "FEMALE", "f", "F"]:
        usergen = "Female"
    else:
        usergen = "Male"
    with connectSQL() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO User (userAge, userGender, userPhone, userBloodtype) VALUES (?,?,?,?)", (userage, usergen, userph, userblood))
    return redirect(url_for("returnAdmin"))

@app.route("/adminusrdel", methods=["GET", "POST"])
def adminusrdel():
    deluserId = int(request.form["delusridname"])
    useridlist = []
    with connectSQL() as conn:
        selcur = conn.cursor()
        selcur.execute("SELECT User.userId from User")
        usrlist = selcur.fetchall()
        for i in usrlist:
            useridlist.append(int(i[0]))
        if deluserId in useridlist:
            cursor = conn.cursor()
            cursor.execute("DELETE from User where userId=?", (deluserId,))
            flash("One Entry Deleted")
            return redirect(url_for("returnAdmin"))
        else:
            flash("ID does not exist")
            return redirect(url_for("returnAdmin"))
 

@app.route("/editadminuser", methods=["GET", "POST"])
def editadminuser():
    toeusrid = request.form["tousrid"]
    modifyusera = request.form["usera"]
    modifyuserg = request.form["userg"]
    modifyuserp = request.form["userp"]
    modifyuserb = request.form["userb"]
    if modifyuserg in ["female", "Female", "FEMALE", "f", "F"]:
        modifyuserg = "Female"
    else:
        modifyuserg = "Male"
    with connectSQL() as conn:
        csr = conn.cursor()
        csr.execute("UPDATE User SET userAge=?, userGender=?, userPhone=?, userBloodtype=? WHERE userId=?", (modifyusera, modifyuserg, modifyuserp, modifyuserb, toeusrid))
        flash("Edit Success", "success")
        return redirect(url_for("returnAdmin"))

# end of user modify

@app.route("/adminhisdel", methods=["GET", "POST"])
def adminhisdel():
    delhistoryId = int(request.form["delhisidname"])
    hisidlist = []
    with connectSQL() as conn:
        selcur = conn.cursor()
        selcur.execute("SELECT History.hisId from History")
        hislist = selcur.fetchall()
        for i in hislist:
            hisidlist.append(int(i[0]))
        if delhistoryId in hisidlist:
            cursor = conn.cursor()
            cursor.execute("DELETE from History where hisId=?", (delhistoryId,))
            flash("One Entry Deleted")
            return redirect(url_for("returnAdmin"))
        else:
            flash("ID does not exist")
            return redirect(url_for("returnAdmin"))
    
@app.route("/adminnotidel", methods=["GET", "POST"])
def adminnotidel():
    delnotiId = int(request.form["delnotiidname"])
    notiidlist = []
    with connectSQL() as conn:
        selcur = conn.cursor()
        selcur.execute("SELECT Notification.notiId from Notification")
        notilist = selcur.fetchall()
        for i in notilist:
            notiidlist.append(int(i[0]))
        if delnotiId in notiidlist:
            cursor = conn.cursor()
            cursor.execute("DELETE from Notification where notiId=?", (delnotiId,))
            flash("One Entry Deleted")
            return redirect(url_for("returnAdmin"))
        else:
            flash("ID does not exist")
            return redirect(url_for("returnAdmin"))

#Just in case Insert History

@app.route("/admin/inserthistory", methods=["GET", "POST"])
def inserthistory():
    if request.method == "GET":
        return render_template("inserthistory.html")
    else:
        recname = request.form["rcpname"]
        doname = request.form["dnname"]
        blid = request.form["bldid"]
        blamt = request.form["bldamt"]
        hitime = request.form["hdate"]
        histat = request.form["hstat"]
        doId = request.form["doid"]
        with connectSQL() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO History (recptName, donarName, bloodId, bloodAmt, histDate, histStatus, docId) VALUES (?,?,?,?,?,?,?)", (recname, doname, blid, blamt, hitime, histat, doId))
        return render_template("admin.html")

#Just in case Insert Nootification

@app.route("/admin/insertnoti", methods=["GET", "POST"])
def insertnoti():
    if request.method == "GET":
        return render_template("insertnoti.html")
    else:
        notitype = request.form["ntype"]
        notistat = request.form["nstatus"]
        noticmt = request.form["cmt"]
        notiusid = request.form["usid"]
        with connectSQL() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Notification (notiType, notiStatus, notiCmt, userId) VALUES (?,?,?,?)", (notitype, notistat, noticmt, notiusid))
        return render_template("admin.html") 


if __name__=="__main__":
    app.run(debug=True, port=5558)

