package main

import "sync"

type Elevator struct {
	ID               int
	Capacity         int
	CurrentFloor     int
	CurrentDirection int
	CurrentLoad      int
	Elevator         *ElevatorPanel
	Destination      []int
	Lock             sync.Mutex
}

func NewElevator(id int) *Elevator {
	return &Elevator{ID: id, Capacity: 10, CurrentFloor: 0, CurrentDirection: Still, CurrentLoad: 0, Elevator: NewElevatorPanel(id)}
}
