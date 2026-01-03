ALTER TABLE courses ADD COLUMN faculty VARCHAR(10);
ALTER TABLE courses ADD COLUMN term VARCHAR(10);

CREATE INDEX idx_courses_faculty ON courses(faculty);
CREATE INDEX idx_courses_term ON courses(term);
