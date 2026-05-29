package main

import (
	"fmt"

	"github.com/adityjoshi/Second-Brain/lld/parking-system/vehicle"
)

const (
	CarCount   = 5
	VanCount   = 10
	TruckCount = 8
	MotorCycle = 5
)

type ParkingFloor struct {
	FloorId      int
	ParkingSpots map[vehicle.VehicleType]map[int]*ParkingSpot
}

func NewParkingFloor(floorId int) *ParkingFloor {
	parkingSpot := make(map[vehicle.VehicleType]map[int]*ParkingSpot)
	parkingSpot[vehicle.CarType] = createParkingSpots(CarCount, vehicle.CarType)
	parkingSpot[vehicle.VanType] = createParkingSpots(VanCount, vehicle.VanType)
	parkingSpot[vehicle.TruckType] = createParkingSpots(TruckCount, vehicle.TruckType)
	parkingSpot[vehicle.MotorCycleType] = createParkingSpots(MotorCycle, vehicle.MotorCycleType)

	return &ParkingFloor{FloorId: floorId, ParkingSpots: parkingSpot}
}

func createParkingSpots(count int, vehicleType vehicle.VehicleType) map[int]*ParkingSpot {
	spots := make(map[int]*ParkingSpot)
	for i := 1; i <= count; i++ {
		spots[i] = NewParkingSpot(i, vehicleType)
	}
	return spots
}

func (p *ParkingFloor) FindAvailableSlots(vehicleType vehicle.VehicleType) *ParkingSpot {
	for _, spot := range p.ParkingSpots[vehicleType] {
		if spot.IsParkingSpotFree() {
			return spot
		}
	}
	return nil
}

func (p *ParkingFloor) DisplayStatus(parkingFloor *ParkingFloor) {

	fmt.Println("FloorID: %d\n", p.FloorId)

	for vehicleType, spotMap := range parkingFloor.ParkingSpots {
		fmt.Printf("\n %s spots:\n", vehicleType)
		count := 0

		for _, spot := range spotMap {
			if spot.IsParkingSpotFree() {
				count++
			}
		}
		fmt.Printf("\n%s Free spot for: %s are %d", vehicleType, count)
	}
}
