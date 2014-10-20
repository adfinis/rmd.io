\c maildelay;

TRUNCATE auth_user CASCADE;
TRUNCATE mails_userprofile CASCADE;
TRUNCATE mails_account CASCADE;

INSERT INTO auth_user VALUES (
    1,
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

INSERT INTO mails_account VALUES (
    1,
    'ru4u26aoew',
    false
);

INSERT INTO mails_userprofile VALUES (
    1,
    1,
    1
);
