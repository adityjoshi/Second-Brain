package main

import (
	"fmt"
	"math"
	"sync"
)

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

func (e *Elevator) AddDestination(floor int) {
	e.Lock.Lock()
	// todo : add destination floor
	e.Destination = append(e.Destination, floor)
	fmt.Printf("Elevator %d received destination floor with the floor id %d\n", e.ID, floor)
	e.Lock.Unlock()
}

func (e *Elevator) RemoveDestination(floor int) {
	e.Lock.Lock()
	for i, f := range e.Destination {
		if f == floor {
			e.Destination = append(e.Destination[:i], e.Destination[i+1:]...)
			// todo: remove destination floor
		}
		break
	}
	e.Lock.Unlock()
}

func (e *Elevator) UpdateCurrentFloor(floor int) {
	e.Lock.Lock()
	e.CurrentFloor = floor
	e.Lock.Unlock()
}

func (e *Elevator) UpdateCurrentDirection(dir Directions) {
	e.Lock.Lock()
	e.CurrentDirection = dir
	e.Lock.Unlock()
}

func (e *Elevator) FarthesetDirection() int {
	mf := 0

	for _, floor := range e.Destination {
		if floor > mf {
			mf = floor
		}
	}
	return mf
}

func (e *Elevator) NearestDirection() int {
	nf := math.MaxInt
	for _, floor := range e.Destination {
		if nf > floor {
			nf = floor
		}
	}
	return nf
}
