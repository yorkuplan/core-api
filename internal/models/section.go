package models

import "time"

type Section struct {
	ID        string           `json:"id"`
	CourseID  string           `json:"course_id"`
	Letter    string           `json:"letter"`
	Activities []SectionActivity `json:"activities,omitempty"`
	CreatedAt time.Time        `json:"created_at"`
	UpdatedAt time.Time        `json:"updated_at"`
}
