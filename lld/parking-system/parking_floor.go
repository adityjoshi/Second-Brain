package main

import "github.com/adityjoshi/Second-Brain/lld/parking-system/vehicle"

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
