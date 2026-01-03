DROP INDEX IF EXISTS idx_courses_term;
DROP INDEX IF EXISTS idx_courses_faculty;
ALTER TABLE courses DROP COLUMN IF EXISTS term;
ALTER TABLE courses DROP COLUMN IF EXISTS faculty;
