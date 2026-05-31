package main

import (
	"fmt"
	"sync"
	"time"

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

func (p *ParkingLot) ParkVehicle(vehicle vehicle.VehicleInterface) (*ParkingTicket, error) {
	parkingSpot, err := p.FindParkingSpot(vehicle.GetVehicleType())
	if err != nil {
		return nil, err
	}
	if err = parkingSpot.Park(vehicle); err != nil {
		return nil, err
	}

	parkingTikcet := NewParkingTicket(vehicle, parkingSpot)
	return parkingTikcet, nil

}

func (p *ParkingLot) UnparkVehicle(parkingTicket *ParkingTicket) error {
	parkingTicket.SetExitTime(time.Now())
	charge := parkingTicket.CalculateTotalCharge()

	paymentSystem := NewPaymentSystem(charge, parkingTicket)

	if err := paymentSystem.ProcessPayment(); err != nil {
		return fmt.Errorf("unable to process the payment %v", err)
	}

	parkingTicket.Spot.RemoveVehicle()
	return nil

}
