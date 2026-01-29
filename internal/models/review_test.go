package models

import (
	"encoding/json"
	"testing"
	"time"
)

func TestReviewJSON(t *testing.T) {
	reviewText := "Great course!"
	authorName := "John Smith"
	review := Review{
		ID:                 "123e4567-e89b-12d3-a456-426614174000",
		CourseCode:         "EECS2030",
		Email:              "student@yorku.ca",
		AuthorName:         &authorName,
		Liked:              true,
		Difficulty:         3,
		RealWorldRelevance: 5,
		ReviewText:         &reviewText,
		CreatedAt:          time.Now(),
		UpdatedAt:          time.Now(),
	}

	data, err := json.Marshal(review)
	if err != nil {
		t.Fatalf("Failed to marshal review: %v", err)
	}

	var decoded Review
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Failed to unmarshal review: %v", err)
	}

	if decoded.ID != review.ID {
		t.Errorf("Expected ID %s, got %s", review.ID, decoded.ID)
	}
	if decoded.CourseCode != review.CourseCode {
		t.Errorf("Expected CourseCode %s, got %s", review.CourseCode, decoded.CourseCode)
	}
	// Email should not be in JSON
	if decoded.Email != "" {
		t.Errorf("Expected Email to be empty (not serialized), got %s", decoded.Email)
	}
	if decoded.Liked != review.Liked {
		t.Errorf("Expected Liked %v, got %v", review.Liked, decoded.Liked)
	}
	if decoded.Difficulty != review.Difficulty {
		t.Errorf("Expected Difficulty %d, got %d", review.Difficulty, decoded.Difficulty)
	}
	if decoded.RealWorldRelevance != review.RealWorldRelevance {
		t.Errorf("Expected RealWorldRelevance %d, got %d", review.RealWorldRelevance, decoded.RealWorldRelevance)
	}
}

func TestReviewAnonymous(t *testing.T) {
	reviewText := "Great course!"
	review := Review{
		ID:                 "123e4567-e89b-12d3-a456-426614174000",
		CourseCode:         "EECS2030",
		Email:              "student@yorku.ca",
		AuthorName:         nil, // Anonymous
		Liked:              true,
		Difficulty:         3,
		RealWorldRelevance: 5,
		ReviewText:         &reviewText,
		CreatedAt:          time.Now(),
		UpdatedAt:          time.Now(),
	}

	data, err := json.Marshal(review)
	if err != nil {
		t.Fatalf("Failed to marshal review: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Failed to unmarshal review: %v", err)
	}

	// AuthorName should be null in JSON
	if decoded["author_name"] != nil {
		t.Errorf("Expected author_name to be null for anonymous review, got %v", decoded["author_name"])
	}
}

func TestCreateReviewRequest(t *testing.T) {
	reviewText := "Great course!"
	authorName := "John Smith"
	req := CreateReviewRequest{
		Email:              "student@yorku.ca",
		AuthorName:         &authorName,
		Liked:              true,
		Difficulty:         3,
		RealWorldRelevance: 5,
		ReviewText:         &reviewText,
	}

	data, err := json.Marshal(req)
	if err != nil {
		t.Fatalf("Failed to marshal create review request: %v", err)
	}

	var decoded CreateReviewRequest
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Failed to unmarshal create review request: %v", err)
	}

	if decoded.Email != req.Email {
		t.Errorf("Expected Email %s, got %s", req.Email, decoded.Email)
	}
	if *decoded.AuthorName != *req.AuthorName {
		t.Errorf("Expected AuthorName %s, got %s", *req.AuthorName, *decoded.AuthorName)
	}
	if decoded.Liked != req.Liked {
		t.Errorf("Expected Liked %v, got %v", req.Liked, decoded.Liked)
	}
	if decoded.Difficulty != req.Difficulty {
		t.Errorf("Expected Difficulty %d, got %d", req.Difficulty, decoded.Difficulty)
	}
	if decoded.RealWorldRelevance != req.RealWorldRelevance {
		t.Errorf("Expected RealWorldRelevance %d, got %d", req.RealWorldRelevance, decoded.RealWorldRelevance)
	}
}
