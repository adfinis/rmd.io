# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import psycopg2

try:
    conn1 = psycopg2.connect(
        "dbname='maildelay_old' user='maildelay' host='localhost' password='vagrant'"
    )
    conn2 = psycopg2.connect(
        "dbname='maildelay' user='maildelay' host='localhost' password='vagrant'"
    )
except:
    print("I am unable to connect to the database")

# <codecell>

userstat = conn1.cursor()
oblstat = conn1.cursor()
sentstat = conn1.cursor()
recstat = conn1.cursor()

new = conn2.cursor()
entries = []

# <codecell>

sentstat.execute("SELECT date FROM mails_sentstatistic")

for sent in sentstat.fetchall():
    statistic = {"type": "SENT", "email": "", "date": sent[0]}
    entries.append(statistic)

# <codecell>

userstat.execute("SELECT email, date FROM mails_userstatistic")

for user in userstat.fetchall():
    statistic = {"type": "USER", "email": user[0], "date": user[1]}
    entries.append(statistic)

# <codecell>

recstat.execute("SELECT email, date FROM mails_receivedstatistic")

for rec in recstat.fetchall():
    statistic = {"type": "REC", "email": rec[0], "date": rec[1]}
    entries.append(statistic)

# <codecell>

oblstat.execute("SELECT email, date FROM mails_obliviousstatistic")

for obl in oblstat.fetchall():
    statistic = {"type": "OBL", "email": obl[0], "date": obl[1]}
    entries.append(statistic)

# <codecell>

for entry in entries:
    new.execute(
        "INSERT INTO mails_statistic (type, email, date) VALUES ('%s', '%s', '%s')"
        % (entry["type"], entry["email"], entry["date"])
    )

# <codecell>

conn1.commit()
conn2.commit()
conn1.close()
conn2.close()

# <codecell>


# <codecell>
