package main

import (
	"fmt"
	"sort"
)

type ElevatorManager struct {
	Building *Building
}

func NewElevatorManager(building *Building) *ElevatorManager {
	return &ElevatorManager{Building: building}
}

func (em *ElevatorManager) OperateAllElevators() {
	for _, elevator := range em.Building.Elevators {
		go em.OperateElevator(elevator)
	}
}

func (em *ElevatorManager) OperateElevator(e *Elevator) {
	for {
		e.Lock.Lock()
		if len(e.Destination) == 0 {
			e.CurrentDirection = STILL
			e.Lock.Unlock()
			continue
		}
		sort.Ints(e.Destination)
		fmt.Printf("Elevator %d is starting from %d and going to %s\n", e.ID, e.CurrentFloor, e.CurrentDirection)

		if e.CurrentDirection == UP {
			em.MoveElevatorUp(e)
		} else if e.CurrentDirection == DOWN {
			em.MoveElevatorDown(e)
		} else {
			em.DecideDirection(e)
		}
		e.Lock.Unlock()
	}
}

func (em *ElevatorManager) DecideDirection(e *Elevator) {
	currentFloor := e.CurrentFloor
	if len(e.CurrentDirection) == 0 {
		return
	}

	nearestDestination := e.Destination[0]
	if nearestDestination > currentFloor {
		e.UpdateCurrentDirection(UP)
		em.MoveElevatorUp(e)
	} else {
		e.UpdateCurrentDirection(DOWN)
		em.MoveElevatorDown(e)
	}
}
