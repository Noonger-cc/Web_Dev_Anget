package routes

import (
	"langgraph-ops-server/handlers"

	"github.com/gin-gonic/gin"
)

func SetupRouter() *gin.Engine {
	r := gin.Default()

	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	api := r.Group("/api")
	{
		api.POST("/login", handlers.Login)

		hosts := api.Group("/host")
		{
			hosts.GET("", handlers.GetHosts)
			hosts.POST("", handlers.AddHost)
			hosts.PUT("/:id", handlers.UpdateHost)
			hosts.DELETE("/:id", handlers.DeleteHost)
		}

		task := api.Group("/task")
		{
			task.GET("/list", handlers.GetTasks)
			task.POST("/create", handlers.CreateTask)
		}

		client := api.Group("/client")
		{
			client.GET("/list", handlers.GetClients)
			client.POST("", handlers.AddClient)
			client.PUT("/:id", handlers.UpdateClient)
			client.DELETE("/:id", handlers.DeleteClient)
			client.POST("/heartbeat", handlers.ClientHeartbeat)
			client.POST("/send", handlers.SendClientCmd)
		}

		ssh := api.Group("/ssh")
		{
			ssh.POST("/connect", handlers.SshConnect)
			ssh.POST("/execute", handlers.SshExecute)
		}
	}

	r.GET("/ws/log", handlers.WSLog)
	r.GET("/ws/client", handlers.ClientWS)
	r.GET("/ws/cmd", handlers.ClientWS)

	return r
}
