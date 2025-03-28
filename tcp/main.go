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

	conn, err := listener.Accept()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Print(conn)
}
