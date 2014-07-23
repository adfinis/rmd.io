\c maildelay;

TRUNCATE auth_user CASCADE;
TRUNCATE mails_identity CASCADE;
TRUNCATE mails_useridentity CASCADE;

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

INSERT INTO mails_identity VALUES (
    1,
    'ru4u26aoew',
    false
);

INSERT INTO mails_useridentity VALUES (
    1,
    1,
    1
);
