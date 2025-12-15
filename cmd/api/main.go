package main

import (
	"context"
	"log"
	"yuplan/internal/config"
	"yuplan/internal/database"
	"yuplan/internal/handlers"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

func main() {
	ctx := context.Background()

	cfg := config.Load()

	// Setup db connection
	pool, err := database.NewPool(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer pool.Close()

	courseRepo := repository.NewCourseRepository(pool)

	courseHandler := handlers.NewCourseHandler(courseRepo)

	// Setup router
	r := gin.Default()

	api := r.Group("/api/v1")
	{
		api.GET("/courses", courseHandler.GetCourses)
		api.GET("/courses/:course_id", courseHandler.GetCourseByID)
	}

	log.Printf("Starting server on port %s", cfg.Port)
	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
