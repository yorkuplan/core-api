-- Create reviews table
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_code VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    author_name VARCHAR(100), -- Optional: user can provide name or stay anonymous
    liked BOOLEAN NOT NULL,
    difficulty INTEGER NOT NULL CHECK (difficulty >= 1 AND difficulty <= 5),
    real_world_relevance INTEGER NOT NULL CHECK (real_world_relevance >= 1 AND real_world_relevance <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate reviews: one review per email per course
    UNIQUE(course_code, email)
);

-- Create indexes for performance
CREATE INDEX idx_reviews_course_code ON reviews(course_code);
CREATE INDEX idx_reviews_created_at ON reviews(created_at DESC);
CREATE INDEX idx_reviews_email ON reviews(email);
