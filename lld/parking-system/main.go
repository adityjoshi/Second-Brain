package main

import (
	"fmt"
	"sync"
	"time"

	"github.com/adityjoshi/Second-Brain/lld/parking-system/vehicle"
)

var (
	wg sync.WaitGroup
)

func main() {
	parkingLot := GetParkingLot()

	parkingLot.Name = "Nainital Parking Lot"
	parkingLot.AddFloor(1)
	parkingLot.AddFloor(2)

	parkingLot.DisplayAvailability()

	for i := 1; i <= 10; i++ {
		wg.Add(1)
		go parkCar(i, parkingLot)
	}
	wg.Wait()
	parkingLot.DisplayAvailability()
	ticket, _ := parkingLot.ParkVehicle(vehicle.NewTruck("Truck-1"))

	time.Sleep(10 * time.Second)
	err := parkingLot.UnparkVehicle(ticket)
	if err != nil {
		return
	}

	formattedCharge := fmt.Sprintf("%.2f", ticket.CalculateTotalCharge())

	fmt.Printf("bill for %s = %s\n", ticket.Vehicle.GetLicenseNumber(), formattedCharge)
}

func parkCar(i int, parkingLot *ParkingLot) {
	defer wg.Done()
	car := vehicle.NewCar(fmt.Sprintf("car-%d", i))

	ticket, err := parkingLot.ParkVehicle(car)
	if err != nil {
		fmt.Printf("Failed to park %s: %v\n", car.LicenseNumber, err)
		return
	}
	fmt.Printf("%s parked successfully. Ticket: %s\n", car.LicenseNumber, ticket.EntryTime)
}
