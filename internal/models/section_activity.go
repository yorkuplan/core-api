package models

import "time"

type SectionActivity struct {
	ID            string    `json:"id"`
	CourseType    string    `json:"course_type"`
	SectionID     string    `json:"section_id"`
	CatalogNumber string    `json:"catalog_number"`
	Times         *string   `json:"times,omitempty"` // JSON string of schedule array
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}
