package main

import (
	"log"
	"os"
	"os/exec"
	"time"
	"net/http"
	"io"
	"encoding/json"
	"github.com/gorilla/websocket"
)

var (
	serverAddr = "server-go:8080"
	clientID   = uint(1)
	clientName = "ops-client-1"
)

func main() {
	if addr := os.Getenv("SERVER_ADDR"); addr != "" {
		serverAddr = addr
	}

	log.Println("Starting LangGraph Ops Client...")
	log.Printf("Server: %s", serverAddr)

	go heartbeatLoop()
	go wsConnectLoop()

	select {}
}

func heartbeatLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		sendHeartbeat()
	}
}

func sendHeartbeat() {
	data := map[string]interface{}{
		"client_id": clientID,
		"status":    "online",
	}
	jsonData, _ := json.Marshal(data)

	resp, err := http.Post("http://"+serverAddr+"/api/client/heartbeat", "application/json", nil)
	if err != nil {
		log.Printf("Heartbeat failed: %v", err)
		return
	}
	defer resp.Body.Close()
	log.Println("Heartbeat sent")
}

func wsConnectLoop() {
	for {
		time.Sleep(5 * time.Second)
		connectWS()
	}
}

func connectWS() {
	url := "ws://" + serverAddr + "/ws/cmd"

	header := http.Header{}
	header.Set("X-Client-ID", string(rune(clientID)))

	ws, _, err := websocket.DefaultDialer.Dial(url, header)
	if err != nil {
		log.Printf("WS connection failed: %v", err)
		return
	}
	defer ws.Close()

	log.Println("WebSocket connected")

	for {
		messageType, message, err := ws.ReadMessage()
		if err != nil {
			log.Printf("WS read error: %v", err)
			break
		}

		if messageType == websocket.TextMessage {
			handleCommand(ws, message)
		}
	}
}

func handleCommand(ws *websocket.Conn, message []byte) {
	var req struct {
		Command string `json:"command"`
	}
	if err := json.Unmarshal(message, &req); err != nil {
		log.Printf("Parse command failed: %v", err)
		return
	}

	log.Printf("Executing command: %s", req.Command)

	cmd := exec.Command("sh", "-c", req.Command)
	output, err := cmd.CombinedOutput()

	result := string(output)
	if err != nil {
		result += "\nError: " + err.Error()
	}

	sendLog(ws, result)
}

func sendLog(ws *websocket.Conn, message string) {
	data := map[string]interface{}{
		"client_id": clientID,
		"log":       message,
		"timestamp": time.Now().Format(time.RFC3339),
	}
	jsonData, _ := json.Marshal(data)
	ws.WriteMessage(websocket.TextMessage, jsonData)
}
