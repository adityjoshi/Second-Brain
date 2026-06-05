package main

type ElevatorManager struct {
	Building *Building
}

func NewElevatorManager(building *Building) *ElevatorManager {
	return &ElevatorManager{Building: building}
}

func (em *ElevatorManager) OperateAllElevators() {

}
