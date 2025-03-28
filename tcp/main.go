package main

import (
	"fmt"
	"log"
	"net"
)

func main() {

	listener, err := net.Listen("tcp", ":1729")
	if err != nil {
		log.Fatal("error :", err)
	}
	fmt.Print("hello server ", listener)
}
