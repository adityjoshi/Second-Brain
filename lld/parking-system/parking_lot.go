package main

import (
	"fmt"
	"sync"

	"github.com/adityjoshi/Second-Brain/lld/parking-system/vehicle"
)

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

func (p *ParkingLot) DisplayAvailability() {

	fmt.Printf("parking lot %s\n", p.Name)

	for _, floor := range p.floors {
		floor.DisplayStatus(floor)
	}
}

func (p *ParkingLot) FindParkingSpot(vehicleType vehicle.VehicleType) (*ParkingSpot, error) {
	for _, floors := range p.floors {
		if spot := floors.FindAvailableSlots(vehicleType); spot != nil {
			return spot, nil
		}
	}
	return nil, fmt.Errorf("no available parking spot found for the vehicle %s\n", vehicleType)
}

func (p *ParkingLot) ParkVehicle(vehicle vehicle.VehicleType) (*ParkingTicket, error) {
	parkingSpot, err := p.FindParkingSpot(vehicle)
	if err != nil {
		return nil, err
	}
	if err = parkingSpot.ParkVehicle(vehicle); err != nil {
		return nil, err
	}

	parkingTikcet := NewParkingTicket(vehicle, parkingSpot)
	return parkingTikcet, nil

}
