# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import psycopg2

try:
    conn1 = psycopg2.connect("dbname='maildelay_old' user='maildelay' host='localhost' password='vagrant'")
    conn2 = psycopg2.connect("dbname='maildelay' user='maildelay' host='localhost' password='vagrant'")
except:
    print("I am unable to connect to the database")

# <codecell>

cur1 = conn1.cursor()
cur2 = conn2.cursor()

# <codecell>

cur1.execute("SELECT * FROM mails_identity")
identities = cur1.fetchall()

# <codecell>

for i in identities:
    cur2.execute("""INSERT INTO mails_account (id, key, anti_spam) VALUES (%s, %s, %s);""", (i[0], i[1], i[2]))

# <codecell>

cur1.execute("SELECT user_id, identity_id FROM mails_useridentity")

# <codecell>

results = cur1.fetchall()

# <codecell>

for res in results:
    cur2.execute("INSERT INTO mails_userprofile (user_id, account_id) VALUES (%s, %s)" % (res[0], res[1]))

# <codecell>

conn2.commit()
conn1.close()
conn2.close()

# <codecell>
