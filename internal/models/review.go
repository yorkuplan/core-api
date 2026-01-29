package models

import "time"

type Review struct {
	ID                  string    `json:"id"`
	CourseCode          string    `json:"course_code"`
	Email               string    `json:"-"` // Never expose email in API responses
	AuthorName          *string   `json:"author_name"` // Nullable: null = anonymous, value = display name
	Liked               bool      `json:"liked"`
	Difficulty          int       `json:"difficulty"`
	RealWorldRelevance  int       `json:"real_world_relevance"`
	ReviewText          *string   `json:"review_text"`
	CreatedAt           time.Time `json:"created_at"`
	UpdatedAt           time.Time `json:"updated_at"`
}

type CreateReviewRequest struct {
	Email              string  `json:"email" binding:"required,email"`
	AuthorName         *string `json:"author_name"` // Optional: provide name or leave null for "Anonymous"
	Liked              bool    `json:"liked"`
	Difficulty         int     `json:"difficulty" binding:"required,min=1,max=5"`
	RealWorldRelevance int     `json:"real_world_relevance" binding:"required,min=1,max=5"`
	ReviewText         *string `json:"review_text"`
}
