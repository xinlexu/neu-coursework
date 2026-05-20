CREATE DATABASE IF NOT EXISTS silicon;
USE silicon;

DROP TRIGGER IF EXISTS trg_student_mast_after_update;
DROP TABLE IF EXISTS stu_log;
DROP TABLE IF EXISTS student_mast;

CREATE TABLE student_mast (
    student_id INT PRIMARY KEY,
    name VARCHAR(100),
    st_class INT
);

INSERT INTO student_mast (student_id, name, st_class) VALUES
(1, 'Steven King', 7),
(2, 'Neena Kochhar', 8),
(3, 'Lex De Haan', 8),
(4, 'Alexander Hunold', 10);

CREATE TABLE stu_log (
    student_id INT,
    description VARCHAR(255)
);

DELIMITER $$

CREATE TRIGGER trg_student_mast_after_update
AFTER UPDATE ON student_mast
FOR EACH ROW
BEGIN
    INSERT INTO stu_log (student_id, description)
    VALUES (
        NEW.student_id,
        CONCAT(
            'Student ',
            NEW.name,
            ' promoted from class ',
            OLD.st_class,
            ' to ',
            NEW.st_class
        )
    );
END$$

DELIMITER ;

UPDATE student_mast
SET st_class = st_class + 1;

SELECT * FROM student_mast;
SELECT * FROM stu_log;
