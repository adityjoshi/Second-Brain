package main

import (
	"time"

	"github.com/adityjoshi/Second-Brain/lld/parking-system/vehicle"
)

const baseChager = 100.00

type ParkingTicket struct {
	EntryTime   time.Time
	ExitTime    time.Time
	Vehicle     vehicle.VehicleInterface
	Spot        *ParkingSpot
	TotalCharge float64
}

func (p *ParkingTicket) SetExitTime(t time.Time) {
	p.ExitTime = t
}
