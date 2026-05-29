package main

import "sync"

var (
	parkingLotInstance *ParkingLot
	once               sync.Once
)

type ParkingLot struct {
	Name   string
	floors []*ParkingFloor
}

func GetParkingLot() *ParkingLot {
	once.Do(func() {
		parkingLotInstance = &ParkingLot{}
	})
	return parkingLotInstance
}

func (p *ParkingLot) AddFloor(floorId int) {
	p.floors = append(p.floors, NewParkingFloor(floorId))
}
