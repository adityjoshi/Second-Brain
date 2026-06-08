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

func (em *ElevatorManager) MoveElevatorUp(e *Elevator) {
	for i := 0; i < len(e.Destination); i++ {
		destination := e.Destination[i]
		if destination >= e.CurrentFloor {
			fmt.Printf("Elevator %d moving up to floor %d\n", e.ID, destination)
			e.UpdateCurrentFloor(destination)
			e.RemoveDestination(destination)
			i--
		}
	}
	if len(e.Destination) == 0 {
		e.UpdateCurrentDirection(STILL)
	} else {
		e.UpdateCurrentDirection(DOWN)
	}
}

func (em *ElevatorManager) MoveElevatorDown(e *Elevator) {
	for i := len(e.Destination) - 1; i >= 0; i-- {
		destination := e.Destination[i]
		if destination <= e.CurrentFloor {
			fmt.Printf("Elevator %d moving down to floor %d\n", e.ID, destination)
			e.UpdateCurrentFloor(destination)
			e.RemoveDestination(destination)

		}
	}
	if len(e.Destination) == 0 {
		e.UpdateCurrentDirection(STILL)
	} else {
		e.UpdateCurrentDirection(UP)
	}

}

func (em *ElevatorManager) AssignElevator(floor int, dir Directions) *Elevator {
	bestE := em.FindClosestElevator(floor, dir)
	if bestE != nil {
		bestE.AddDestination(floor)
		fmt.Printf("Elevator %d assigned to floor %d with direction %s\n", bestE.ID, floor, dir)

	}
	return bestE
}

func (em *ElevatorManager) FindClosestElevator(floor int, dir Directions) *Elevator {
	var ce *Elevator
	minDistance := int(1e9)

	for _, elevator := range em.Building.Elevators {
		elevator.Lock.Lock()
		distance := em.Distance(elevator, floor, dir)
		if distance < minDistance {
			minDistance = distance
			ce = elevator
		}
		elevator.Lock.Unlock()
	}
	return ce
}

func (em *ElevatorManager) Distance(elevator *Elevator, floor int, dir Directions) int {
	currentFloor := elevator.CurrentFloor
	currentDirection := elevator.CurrentDirection

	if currentDirection == STILL || (currentDirection == dir && ((dir == UP && floor > currentFloor) || (dir == DOWN && floor < currentFloor))) {
		return abs(floor - currentFloor)
	}
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
