package main

import "fmt"

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

func NewPaymentSystem(amount float64, ticket *ParkingTicket) *Payment {
	return &Payment{Amount: amount, Ticket: ticket, Status: PaymentPending}
}

func (p *Payment) ProcessPayment() error {
	if p.Ticket == nil {
		return fmt.Errorf("payment failed: no parking ticket found")
	}
	if p.Ticket.TotalCharge < p.Amount {
		p.Status = PaymentFailed
		return fmt.Errorf("insufficient balance")
	}

	p.Status = PaymentCompleted
	return nil

}

func (p *Payment) GetPaymentStatus() PaymentStatus {
	return p.Status
}
