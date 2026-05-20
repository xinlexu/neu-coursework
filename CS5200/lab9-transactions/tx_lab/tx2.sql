USE sanjose;
SET AUTOCOMMIT = 0;
-- After tx1 updates but before tx1 commits:
SELECT * FROM ACCT;
COMMIT;
SELECT * FROM ACCT;
