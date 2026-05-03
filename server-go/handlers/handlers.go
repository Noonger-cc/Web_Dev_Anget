package handlers

import (
	"net/http"
	"langgraph-ops-server/models"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"time"
	"sync"
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
)

var upgrader = websocket.Upgrader{}
var wsClients = make(map[*websocket.Conn]bool)
var wsMutex sync.RWMutex

var agentClient *http.Client

func InitAgentClient() {
	agentClient = &http.Client{
		Timeout: 30 * time.Second,
	}
}

func Login(c *gin.Context) {
	var req struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var user models.User
	if err := models.DB.Where("username = ? AND password = ?", req.Username, req.Password).First(&user).Error; err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token":    "mock-jwt-token-" + user.Username,
		"username": user.Username,
	})
}

func GetHosts(c *gin.Context) {
	var hosts []models.Host
	models.DB.Find(&hosts)
	c.JSON(http.StatusOK, gin.H{"data": hosts})
}

func AddHost(c *gin.Context) {
	var host models.Host
	if err := c.ShouldBindJSON(&host); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	host.Status = "offline"
	models.DB.Create(&host)
	c.JSON(http.StatusOK, gin.H{"data": host})
}

func UpdateHost(c *gin.Context) {
	id := c.Param("id")
	var host models.Host
	if err := models.DB.First(&host, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "host not found"})
		return
	}

	var req struct {
		Name       string `json:"name"`
		Host       string `json:"host"`
		Port       int    `json:"port"`
		Username   string `json:"username"`
		AuthType   string `json:"auth_type"`
		Credential string `json:"credential"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	host.Name = req.Name
	host.Host = req.Host
	host.Port = req.Port
	host.Username = req.Username
	host.AuthType = req.AuthType
	if req.Credential != "" {
		host.Credential = req.Credential
	}
	models.DB.Save(&host)
	c.JSON(http.StatusOK, gin.H{"data": host})
}

func DeleteHost(c *gin.Context) {
	id := c.Param("id")
	if err := models.DB.Delete(&models.Host{}, id).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "delete failed"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "deleted"})
}

func GetTasks(c *gin.Context) {
	var tasks []models.Task
	models.DB.Order("id desc").Find(&tasks)
	c.JSON(http.StatusOK, gin.H{"data": tasks})
}

func CreateTask(c *gin.Context) {
	var req struct {
		Name      string   `json:"name"`
		ExecType  string   `json:"exec_type"`
		Command   string   `json:"command"`
		HostIDs   []uint   `json:"host_ids"`
		ClientIDs []uint   `json:"client_ids"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task := models.Task{
		Name:     req.Name,
		ExecType: req.ExecType,
		Command:  req.Command,
		Status:   "pending",
	}
	models.DB.Create(&task)

	go func() {
		models.DB.Model(&task).Update("status", "running")

		ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
		defer cancel()

		reqBody, _ := json.Marshal(map[string]interface{}{
			"task_id":    task.ID,
			"exec_type":  req.ExecType,
			"command":    req.Command,
			"host_ids":   req.HostIDs,
			"client_ids": req.ClientIDs,
		})

		resp, err := agentClient.Post("http://agent-py:8000/execute", "application/json", bytes.NewBuffer(reqBody))
		if err != nil {
			models.DB.Model(&task).Updates(map[string]interface{}{"status": "failed", "result": err.Error()})
			return
		}
		defer resp.Body.Close()

		result, _ := io.ReadAll(resp.Body)
		models.DB.Model(&task).Updates(map[string]interface{}{"status": "success", "result": string(result)})
	}()

	c.JSON(http.StatusOK, gin.H{"data": task})
}

func GetClients(c *gin.Context) {
	var clients []models.Client
	models.DB.Find(&clients)
	c.JSON(http.StatusOK, gin.H{"data": clients})
}

func ClientHeartbeat(c *gin.Context) {
	var req struct {
		ClientID uint   `json:"client_id"`
		Status   string `json:"status"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var client models.Client
	if err := models.DB.First(&client, req.ClientID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "client not found"})
		return
	}

	client.Status = "online"
	client.LastHeart = time.Now().Format("2006-01-02 15:04:05")
	models.DB.Save(&client)

	c.JSON(http.StatusOK, gin.H{"message": "ok"})
}

func SendClientCmd(c *gin.Context) {
	var req struct {
		ClientID uint   `json:"client_id"`
		Command  string `json:"command"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "command sent", "client_id": req.ClientID})
}

func WSLog(c *gin.Context) {
	upgrader.CheckOrigin = func(r *http.Request) bool { return true }
	ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		return
	}
	defer ws.Close()

	wsMutex.Lock()
	wsClients[ws] = true
	wsMutex.Unlock()

	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			wsMutex.RLock()
			if !wsClients[ws] {
				wsMutex.RUnlock()
				return
			}
			wsMutex.RUnlock()
			ws.WriteMessage(websocket.PingMessage, nil)
		}
	}()

	for {
		_, _, err := ws.ReadMessage()
		if err != nil {
			break
		}
	}

	wsMutex.Lock()
	delete(wsClients, ws)
	wsMutex.Unlock()
}

func BroadcastLog(message string) {
	wsMutex.RLock()
	defer wsMutex.RUnlock()

	for ws := range wsClients {
		ws.WriteJSON(map[string]interface{}{
			"time":    time.Now().Format("15:04:05"),
			"level":   "info",
			"message": message,
		})
	}
}
