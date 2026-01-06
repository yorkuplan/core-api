package repository

import (
	"context"
	"fmt"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v4"
)

type SectionActivityRepositoryInterface interface {
	GetBySectionID(ctx context.Context, sectionID string) ([]models.SectionActivity, error)
	GetBySectionIDAndType(ctx context.Context, sectionID string, courseType string) ([]models.SectionActivity, error)
}

type sectionActivityDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

type SectionActivityRepository struct {
	db sectionActivityDB
}

func NewSectionActivityRepository(db sectionActivityDB) *SectionActivityRepository {
	return &SectionActivityRepository{db: db}
}

func (r *SectionActivityRepository) GetBySectionID(ctx context.Context, sectionID string) ([]models.SectionActivity, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT id, course_type, section_id, catalog_number, times, created_at, updated_at
		 FROM section_activities
		 WHERE section_id = $1
		 ORDER BY course_type, catalog_number`,
		sectionID,
	)
	if err != nil {
		return nil, fmt.Errorf("query section_activities by section_id: %w", err)
	}
	defer rows.Close()

	activities := make([]models.SectionActivity, 0)
	for rows.Next() {
		var activity models.SectionActivity
		if err := rows.Scan(&activity.ID, &activity.CourseType, &activity.SectionID, &activity.CatalogNumber, &activity.Times, &activity.CreatedAt, &activity.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan section_activity: %w", err)
		}
		activities = append(activities, activity)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate section_activities: %w", err)
	}

	return activities, nil
}

func (r *SectionActivityRepository) GetBySectionIDAndType(ctx context.Context, sectionID string, courseType string) ([]models.SectionActivity, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT id, course_type, section_id, catalog_number, times, created_at, updated_at
		 FROM section_activities
		 WHERE section_id = $1 AND course_type = $2
		 ORDER BY catalog_number`,
		sectionID,
		courseType,
	)
	if err != nil {
		return nil, fmt.Errorf("query section_activities by section_id and type: %w", err)
	}
	defer rows.Close()

	activities := make([]models.SectionActivity, 0)
	for rows.Next() {
		var activity models.SectionActivity
		if err := rows.Scan(&activity.ID, &activity.CourseType, &activity.SectionID, &activity.CatalogNumber, &activity.Times, &activity.CreatedAt, &activity.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan section_activity: %w", err)
		}
		activities = append(activities, activity)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate section_activities: %w", err)
	}

	return activities, nil
}
