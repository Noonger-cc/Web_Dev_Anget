package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"langgraph-ops-server/models"

	"github.com/gin-gonic/gin"
)

// AgentChatRequest mirrors the Python agent's AgentRequest
type AgentChatRequest struct {
	Message        string `json:"message"`
	ConversationID string `json:"conversation_id"`
	ThreadID       string `json:"thread_id"`
}

// AgentProxyChat proxies the AI chat request to the Python agent and streams SSE to the client
func AgentProxyChat(c *gin.Context) {
	var req AgentChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	threadID := req.ThreadID
	if threadID == "" {
		threadID = fmt.Sprintf("thread-%d", time.Now().UnixNano())
	}

	// Build request to Python agent
	body := strings.NewReader(
		fmt.Sprintf(`{"message":"%s","thread_id":"%s"}`,
			escapeJSON(req.Message), threadID),
	)

	agentReq, err := http.NewRequest("POST", agentBaseURL+"/agent/chat", body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	agentReq.Header.Set("Content-Type", "application/json")

	resp, err := agentClient.Do(agentReq)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Agent unavailable: " + err.Error()})
		return
	}
	defer resp.Body.Close()

	// Stream SSE from Python agent straight to frontend
	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")
	c.Writer.WriteHeader(http.StatusOK)

	buf := make([]byte, 4096)
	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			c.Writer.Write(buf[:n])
			c.Writer.Flush()
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("[agent] SSE read error: %v", err)
			break
		}
	}
}


func escapeJSON(s string) string {
	b, _ := json.Marshal(s)
	return string(b[1 : len(b)-1])
}

// GetDashboardSummary aggregates data for the dashboard overview
func GetDashboardSummary(c *gin.Context) {
	var hostCount, onlineCount, offlineCount, alertCount int64

	models.DB.Model(&models.Host{}).Count(&hostCount)
	models.DB.Model(&models.Host{}).Where("status = ?", "online").Count(&onlineCount)
	offlineCount = hostCount - onlineCount
	models.DB.Model(&models.Alert{}).Where("status = ?", "firing").Count(&alertCount)

	// Get recent alerts (last 5)
	var recentAlerts []models.Alert
	models.DB.Order("id desc").Limit(5).Find(&recentAlerts)

	// Get recent tasks (last 5)
	var recentTasks []models.Task
	models.DB.Order("id desc").Limit(5).Find(&recentTasks)

	// Get average CPU/mem across all hosts with metrics
	type AvgMetrics struct {
		AvgCpu  float64 `json:"avg_cpu"`
		AvgMem  float64 `json:"avg_mem"`
		AvgDisk float64 `json:"avg_disk"`
	}
	var avg AvgMetrics
	models.DB.Raw(`
		SELECT
			COALESCE(AVG(cpu_percent), 0) as avg_cpu,
			COALESCE(AVG(mem_percent), 0) as avg_mem,
			COALESCE(AVG(disk_percent), 0) as avg_disk
		FROM metrics
		WHERE created_at > datetime('now', '-1 hour')
	`).Scan(&avg)

	c.JSON(http.StatusOK, gin.H{
		"hosts": gin.H{
			"total":   hostCount,
			"online":  onlineCount,
			"offline": offlineCount,
		},
		"alerts": gin.H{
			"count":   alertCount,
			"recent":  recentAlerts,
		},
		"tasks": gin.H{
			"recent": recentTasks,
		},
		"metrics": gin.H{
			"avg_cpu":  avg.AvgCpu,
			"avg_mem":  avg.AvgMem,
			"avg_disk": avg.AvgDisk,
		},
	})
}

// UpdateHostIpmi updates IPMI configuration for a host
func UpdateHostIpmi(c *gin.Context) {
	id := c.Param("id")
	var host models.Host
	if err := models.DB.First(&host, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "host not found"})
		return
	}

	var req struct {
		IpmiHost     string `json:"ipmi_host"`
		IpmiUser     string `json:"ipmi_user"`
		IpmiPassword string `json:"ipmi_password"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	host.IpmiHost = req.IpmiHost
	host.IpmiUser = req.IpmiUser
	if req.IpmiPassword != "" {
		host.IpmiPassword = req.IpmiPassword
	}
	host.IpmiStatus = "configured"
	models.DB.Save(&host)

	c.JSON(http.StatusOK, gin.H{"data": host})
}

// CheckIpmiConnectivity tests IPMI connectivity for a host
func CheckIpmiConnectivity(c *gin.Context) {
	id := c.Param("id")
	var host models.Host
	if err := models.DB.First(&host, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "host not found"})
		return
	}

	if host.IpmiHost == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "IPMI not configured for this host"})
		return
	}

	// Call Python agent to check IPMI
	reqBody := fmt.Sprintf(`{"host":"%s","action":"status"}`, host.Name)
	resp, err := agentClient.Post(
		agentBaseURL+"/agent/chat-simple",
		"application/json",
		strings.NewReader(fmt.Sprintf(`{"message":"Check IPMI connectivity for %s using ipmi_sensor tool","thread_id":"ipmi-check-%s"}`, host.Name, id)),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer resp.Body.Close()

	// For now, simple check — in production, call ipmi_sensor directly
	_ = reqBody
	host.IpmiStatus = "checking"
	models.DB.Save(&host)

	c.JSON(http.StatusOK, gin.H{"message": "IPMI check initiated"})
}
