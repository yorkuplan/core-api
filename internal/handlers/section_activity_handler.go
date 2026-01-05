package handlers

import (
	"net/http"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type SectionActivityHandler struct {
	repo repository.SectionActivityRepositoryInterface
}

func NewSectionActivityHandler(repo repository.SectionActivityRepositoryInterface) *SectionActivityHandler {
	return &SectionActivityHandler{repo: repo}
}

func (h *SectionActivityHandler) GetActivitiesBySectionID(c *gin.Context) {
	sectionID := c.Param("section_id")

	activities, err := h.repo.GetBySectionID(c.Request.Context(), sectionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch section activities"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  activities,
		"count": len(activities),
	})
}

func (h *SectionActivityHandler) GetActivitiesBySectionIDAndType(c *gin.Context) {
	sectionID := c.Param("section_id")
	courseType := c.Query("type")

	if courseType == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Query parameter 'type' is required"})
		return
	}

	activities, err := h.repo.GetBySectionIDAndType(c.Request.Context(), sectionID, courseType)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch section activities"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  activities,
		"count": len(activities),
	})
}
