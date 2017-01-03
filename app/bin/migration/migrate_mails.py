# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import psycopg2

try:
    conn1 = psycopg2.connect("dbname='maildelay_old' user='maildelay' host='localhost' password='vagrant'")
    conn2 = psycopg2.connect("dbname='maildelay' user='maildelay' host='localhost' password='vagrant'")
except:
    print "I am unable to connect to the database"

# <codecell>

cur1 = conn1.cursor()
cur2 = conn2.cursor()
cur3 = conn1.cursor()

# <codecell>

cur1.execute("SELECT * FROM mails_mail")

# <codecell>

results = cur1.fetchall()
for res in results:
    mail = {}
    mail['id'] = res[0]
    mail['subject'] = res[1]
    mail['sent'] = res[2]
    mail['due'] = res[3]
    mail['sender'] = res[4]
    recipients_raw = res[5].split(',')
    recipients = []
    for rec in recipients_raw:
        recipient = {}
        if not '@' in rec:
            raw = rec.replace('"', '').lstrip(' ')
            lst = [i.capitalize() for i in raw.split(' ')]
            recipient['name'] = ' '.join(lst)
            recipient['email'] = ''
        else:
            recipient['email'] = rec.lower()
            recipient['name'] = ''
        recipients.append(recipient)
    mail['recipients'] = recipients
    cur3.execute("""SELECT id FROM auth_user WHERE email = '%s'""" % mail['sender'])
    mail['user_id'] = cur3.fetchone()[0]
    cur2.execute("INSERT INTO mails_mail (id, subject, sent, due, user_id) VALUES (%s, %s, %s, %s, %s)", (mail['id'], mail['subject'], mail['sent'], mail['due'], mail['user_id']))
    for r in recipients:
        cur2.execute("INSERT INTO mails_recipient (mail_id, name, email) VALUES (%s, %s, %s)", (mail['id'], r['name'], r['email']))

# <codecell>

conn2.commit()
conn1.close()
conn2.close()

# <codecell>


