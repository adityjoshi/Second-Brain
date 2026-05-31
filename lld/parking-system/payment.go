package main

type PaymentStatus string

const (
	PaymentPending   PaymentStatus = "PaymentPending"
	PaymentCompleted PaymentStatus = "PaymentCompleted"
	PaymentFailed    PaymentStatus = "PaymentFailed"
)

type Payment struct {
	Amount float64
	Ticket *ParkingTicket
	Status PaymentStatus
}
