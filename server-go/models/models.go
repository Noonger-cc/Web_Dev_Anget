package models

import (
	"time"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

var DB *gorm.DB

type User struct {
	ID       uint   `gorm:"primaryKey" json:"id"`
	Username string `gorm:"uniqueIndex" json:"username"`
	Password string `json:"-"`
}

type Host struct {
	ID         uint   `gorm:"primaryKey" json:"id"`
	Name       string `json:"name"`
	Host       string `json:"host"`
	Port       int    `json:"port"`
	Username   string `json:"username"`
	AuthType   string `json:"auth_type"`
	Credential string `json:"-"`
	Status     string `json:"status"`
}

type Task struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Name      string    `json:"name"`
	ExecType  string    `json:"exec_type"`
	Command   string    `json:"command"`
	Status    string    `json:"status"`
	Result    string    `json:"result"`
	Logs      string    `gorm:"type:text" json:"logs"`
	CreatedAt time.Time `json:"created_at"`
}

type Client struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Name      string    `json:"name"`
	Host      string    `json:"host"`
	Status    string    `json:"status"`
	LastHeart time.Time `json:"last_heart"`
}

func InitDB() {
	db, err := gorm.Open(sqlite.Open("ops.db"), &gorm.Config{})
	if err != nil {
		panic(err)
	}
	DB = db

	db.AutoMigrate(&User{}, &Host{}, &Task{}, &Client{})

	var count int64
	db.Model(&User{}).Count(&count)
	if count == 0 {
		db.Create(&User{Username: "admin", Password: "admin123"})
	}
}
