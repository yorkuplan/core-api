package repository

import (
	"context"
	"errors"
	"testing"
	"time"
	"yuplan/internal/models"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

type mockActivityRepo struct {
	activities map[string][]models.SectionActivity
}

func (m *mockActivityRepo) GetBySectionID(ctx context.Context, sectionID string) ([]models.SectionActivity, error) {
	if activities, ok := m.activities[sectionID]; ok {
		return activities, nil
	}
	return []models.SectionActivity{}, nil
}

func (m *mockActivityRepo) GetBySectionIDAndType(ctx context.Context, sectionID string, courseType string) ([]models.SectionActivity, error) {
	activities, _ := m.GetBySectionID(ctx, sectionID)
	result := make([]models.SectionActivity, 0)
	for _, a := range activities {
		if a.CourseType == courseType {
			result = append(result, a)
		}
	}
	return result, nil
}

func TestGetSectionsByCourseID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	activityRepo := &mockActivityRepo{
		activities: map[string][]models.SectionActivity{
			"section-1": {
				{ID: "act-1", CourseType: "LECT", SectionID: "section-1", CatalogNumber: "", Times: nil},
			},
			"section-2": {
				{ID: "act-2", CourseType: "LAB", SectionID: "section-2", CatalogNumber: "L01", Times: nil},
			},
		},
	}

	repo := NewSectionRepository(mock, activityRepo)

	now := time.Now()

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}).
			AddRow("section-1", "course-1", "A", now, now).
			AddRow("section-2", "course-1", "B", now, now))

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, sections)
	assert.Len(t, sections, 2)
	assert.Equal(t, "section-1", sections[0].ID)
	assert.Equal(t, "course-1", sections[0].CourseID)
	assert.Equal(t, "A", sections[0].Letter)
	assert.Len(t, sections[0].Activities, 1)
	assert.Equal(t, "LECT", sections[0].Activities[0].CourseType)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	activityRepo := &mockActivityRepo{activities: make(map[string][]models.SectionActivity)}
	repo := NewSectionRepository(mock, activityRepo)

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnError(errors.New("db error"))

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, sections)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	activityRepo := &mockActivityRepo{activities: make(map[string][]models.SectionActivity)}
	repo := NewSectionRepository(mock, activityRepo)

	now := time.Now()
	// Wrong type for course_id to force scan error
	rows := pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}).
		AddRow("section-1", 12345, "A", now, now)

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(rows)

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, sections)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	activityRepo := &mockActivityRepo{activities: make(map[string][]models.SectionActivity)}
	repo := NewSectionRepository(mock, activityRepo)

	now := time.Now()
	rows := pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}).
		AddRow("section-1", "course-1", "A", now, now).
		AddRow("section-2", "course-1", "B", now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(rows)

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, sections)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_EmptyResult(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	activityRepo := &mockActivityRepo{activities: make(map[string][]models.SectionActivity)}
	repo := NewSectionRepository(mock, activityRepo)

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}))

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, sections)
	assert.Len(t, sections, 0)
	assert.NoError(t, mock.ExpectationsWereMet())
}

