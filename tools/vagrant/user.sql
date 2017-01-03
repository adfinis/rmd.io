\c maildelay;

TRUNCATE auth_user CASCADE;
TRUNCATE mails_userprofile CASCADE;
TRUNCATE mails_account CASCADE;

INSERT INTO auth_user (password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES (
    '!CS8btXLadBKYTLU8xyQHYwfD7M3rSW87hCYprAva',
    '2014-07-23 08:29:15.829938+00',
    true,
    'CxbMocC11-ctpAreo_aBzyZCOg4',
    'Jonas',
    'Metzener',
    'jonasmetzener@gmail.com',
    true,
    true,
    '2014-07-23 08:29:15.800919+00'
);

INSERT INTO mails_account (key, anti_spam) VALUES (
    'ru4u26aoew',
    false
);

INSERT INTO mails_userprofile (user_id, account_id) VALUES (
    (SELECT id FROM auth_user WHERE email = 'jonasmetzener@gmail.com'),
    (SELECT id FROM mails_account WHERE key = 'ru4u26aoew')
);
