package repository

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

const courseSearchQueryPattern = "SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses\\s+WHERE name ILIKE \\$1 OR code ILIKE \\$1 OR REPLACE\\(code, ' ', ''\\) ILIKE \\$2\\s+ORDER BY code\\s+LIMIT \\$3 OFFSET \\$4"

func TestGetAllCourses(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	mock.ExpectQuery("SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses TABLESAMPLE SYSTEM \\(10\\) ORDER BY RANDOM\\(\\) LIMIT \\$1").
		WithArgs(10).
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}))

	courses, err := repo.GetRandomCourses(context.Background(), 10)
	assert.NoError(t, err)
	assert.NotNil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetCourseByID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	mock.ExpectQuery("SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses\\s+WHERE id = \\$1").
		WithArgs("test-id").
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
			AddRow("test-id", "Test Course", "TC101", 3.0, &desc, "SC", "Fall", now, now))

	course, err := repo.GetByID(context.Background(), "test-id")
	assert.NoError(t, err)
	assert.NotNil(t, course)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetAllCourses_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	mock.ExpectQuery("SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses TABLESAMPLE SYSTEM \\(10\\) ORDER BY RANDOM\\(\\) LIMIT \\$1").
		WithArgs(10).
		WillReturnError(errors.New("boom"))

	courses, err := repo.GetRandomCourses(context.Background(), 10)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetAllCourses_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	// credits is intentionally the wrong type to force the scan to fail (expects float64).
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
		AddRow("test-id", "Test Course", "TC101", "NOT_A_FLOAT", &desc, "SC", "Fall", now, now)

	mock.ExpectQuery("SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses TABLESAMPLE SYSTEM \\(10\\) ORDER BY RANDOM\\(\\) LIMIT \\$1").
		WithArgs(10).
		WillReturnRows(rows)

	courses, err := repo.GetRandomCourses(context.Background(), 10)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetAllCourses_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	// Trigger rows.Err() by injecting an error on the second row iteration.
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
		AddRow("id-1", "Course 1", "C1", 3.0, &desc, "SC", "Fall", now, now).
		AddRow("id-2", "Course 2", "C2", 3.0, &desc, "LA", "Winter", now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses TABLESAMPLE SYSTEM \\(10\\) ORDER BY RANDOM\\(\\) LIMIT \\$1").
		WithArgs(10).
		WillReturnRows(rows)

	courses, err := repo.GetRandomCourses(context.Background(), 10)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetCourseByID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	// credits wrong type forces a scan error.
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
		AddRow("test-id", "Test Course", "TC101", "NOT_A_FLOAT", &desc, "SC", "Fall", now, now)

	mock.ExpectQuery("SELECT id, name, code, credits, description, faculty, term, created_at, updated_at FROM courses\\s+WHERE id = \\$1").
		WithArgs("test-id").
		WillReturnRows(rows)

	course, err := repo.GetByID(context.Background(), "test-id")
	assert.Error(t, err)
	assert.Nil(t, course)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Software engineering course"
	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%EECS%", "%EECS%", 50, 0).
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
			AddRow("id-1", "Software Design", "EECS3311", 3.0, &desc, "SC", "Fall", now, now).
			AddRow("id-2", "Software Engineering", "EECS4313", 3.0, &desc, "SC", "Winter", now, now))

	courses, err := repo.Search(context.Background(), "EECS", 50, 0)
	assert.NoError(t, err)
	assert.NotNil(t, courses)
	assert.Equal(t, 2, len(courses))
	assert.Equal(t, "EECS3311", courses[0].Code)
	assert.Equal(t, "EECS4313", courses[1].Code)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses_ByCodeWithSpaces(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Software development"
	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%EECS 2030%", "%EECS2030%", 50, 0).
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
			AddRow("id-3", "Software Tools", "EECS2030", 3.0, &desc, "SC", "Fall", now, now))

	courses, err := repo.Search(context.Background(), "EECS 2030", 50, 0)
	assert.NoError(t, err)
	assert.NotNil(t, courses)
	assert.Equal(t, 1, len(courses))
	assert.Equal(t, "EECS2030", courses[0].Code)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses_ByName(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Software design course"
	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%Software%", "%Software%", 50, 0).
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
			AddRow("id-1", "Software Design", "EECS3311", 3.0, &desc, "SC", "Fall", now, now))

	courses, err := repo.Search(context.Background(), "Software", 50, 0)
	assert.NoError(t, err)
	assert.NotNil(t, courses)
	assert.Equal(t, 1, len(courses))
	assert.Equal(t, "Software Design", courses[0].Name)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses_NoResults(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%NONEXISTENT%", "%NONEXISTENT%", 50, 0).
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}))

	courses, err := repo.Search(context.Background(), "NONEXISTENT", 50, 0)
	assert.NoError(t, err)
	assert.NotNil(t, courses)
	assert.Equal(t, 0, len(courses))
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%EECS%", "%EECS%", 50, 0).
		WillReturnError(errors.New("db error"))

	courses, err := repo.Search(context.Background(), "EECS", 50, 0)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
		AddRow("id-1", "Course 1", "C1", "INVALID_FLOAT", &desc, "SC", "Fall", now, now)

	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%EECS%", "%EECS%", 50, 0).
		WillReturnRows(rows)

	courses, err := repo.Search(context.Background(), "EECS", 50, 0)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestSearchCourses_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "faculty", "term", "created_at", "updated_at"}).
		AddRow("id-1", "Course 1", "C1", 3.0, &desc, "SC", "Fall", now, now).
		RowError(0, errors.New("rows error"))

	mock.ExpectQuery(courseSearchQueryPattern).
		WithArgs("%EECS%", "%EECS%", 50, 0).
		WillReturnRows(rows)

	courses, err := repo.Search(context.Background(), "EECS", 50, 0)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}
