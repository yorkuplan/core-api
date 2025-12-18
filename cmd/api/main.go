package main

import (
	"context"
	"log"
	"yuplan/internal/config"
	"yuplan/internal/database"
	"yuplan/internal/handlers"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
)

func main() {
	ctx := context.Background()
	cfg := config.Load()

	// Setup dependencies
	pool := initDatabase(ctx, cfg.DatabaseURL)
	defer pool.Close()

	router := setupRouter(pool)

	startServer(router, cfg.Port)
}

func initDatabase(ctx context.Context, databaseURL string) *pgxpool.Pool {
	pool, err := database.NewPool(ctx, databaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	return pool
}

func setupRouter(pool *pgxpool.Pool) *gin.Engine {
	courseRepo := repository.NewCourseRepository(pool)
	courseHandler := handlers.NewCourseHandler(courseRepo)

	router := gin.Default()
	api := router.Group("/api/v1")
	{
		api.GET("/courses", courseHandler.GetCourses)
		api.GET("/courses/:course_id", courseHandler.GetCourseByID)
	}
	return router
}

func startServer(router *gin.Engine, port string) {
	log.Printf("Starting server on port %s", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
