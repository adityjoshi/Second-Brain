package main

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

type User struct {
	id   int
	Name string
	age  int
}

var users = []User{
	{id: 1, Name: "aditya", age: 30},
	{id: 2, Name: "aditi", age: 31},
}

func main() {
	r := gin.Default()

	r.GET("/allUsers", GetAllUsers)
	r.GET("/user/:id", GetUserByID)
	r.POST("/createUser", CreateUser)
	r.PUT("/update/:id", UpdateUser)
	r.PATCH("/patch/:id", patchUser)

	r.Run(":8080")
}

func GetAllUsers(c *gin.Context) {
	c.JSON(http.StatusOK, users)
}

func GetUserByID(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "invalid request "})
	}
	for _, user := range users {
		if user.id == id {
			c.JSON(http.StatusOK, user)
			return
		}
	}
	c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
}

func CreateUser(c *gin.Context) {
	var user User

	if err := c.ShouldBindJSON(&user); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "inavlid request"})
		return
	}
	users = append(users, user)

	c.JSON(http.StatusOK, gin.H{"message": user})
}

func UpdateUser(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "invalid request"})
		return
	}

	var user User
	if err = c.ShouldBindJSON(&user); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": err.Error()})
		return
	}
	for i, u := range users {
		if u.id == id {
			users[i] = user
			c.JSON(http.StatusOK, user)
			return
		}
	}
	c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
}

func patchUser(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "bad reques id is required"})
		return
	}
	var patchData map[string]interface{}

	if err := c.ShouldBindJSON(&patchData); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"message": err.Error()})
		return
	}

	for i, _ := range users {
		if users[i].id == id {
			if name, ok := patchData["name"].(string); ok {
				users[i].Name = name
			}
			if age, ok := patchData["age"].(int); ok {
				users[i].age = age
			}
			c.JSON(http.StatusOK, gin.H{"updated": users[i]})
		}

	}
	c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})

}

func DeleteUser(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"message": "required id"})
		return
	}

	for i, user := range users {
		if user.id == id {
			users = append(users[:i], users[i+1:]...)
			c.JSON(http.StatusOK, gin.H{"message": "user deleted successfully"})
			return
		}
	}
	c.JSON(http.StatusNotFound, gin.H{"message": "user not found"})
}
