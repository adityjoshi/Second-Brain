package main

import (
	"log"
	"net"
)

func main() {
	listener, err := net.Listen("tcp", ":1729")
	if err != nil {
		log.Fatal("Error starting server:", err)
	}
	defer listener.Close()

	log.Println("Server is listening on port 1729")

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println("Error accepting connection:", err)
			continue
		}

		log.Println("Client connected from:", conn.RemoteAddr())

		go handleClient(conn)
	}
}

func handleClient(conn net.Conn) {
	defer conn.Close()
	buffer := make([]byte, 1024)

	for {
		n, err := conn.Read(buffer)
		if err != nil {
			log.Println("Client disconnected:", conn.RemoteAddr())
			return
		}

		receivedData := string(buffer[:n])
		log.Printf("Received from client (%s): %s\n", conn.RemoteAddr(), receivedData)

		response := "Hello from the server!\n"
		_, err = conn.Write([]byte(response))
		if err != nil {
			log.Println("Error sending response:", err)
			return
		}
		log.Println("Response sent to client.")
	}
}
