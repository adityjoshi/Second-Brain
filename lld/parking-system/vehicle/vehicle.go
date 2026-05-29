package vehicle

type VehicleType string

const (
	CarType    VehicleType = "Car"
	VanType    VehicleType = "Van"
	TruckType  VehicleType = "TruckType"
	MotorCycle VehicleType = "MotorCycle"
)

var vehicleCost = map[VehicleType]float64{
	CarType:    120,
	VanType:    100,
	TruckType:  150,
	MotorCycle: 80,
}

type Vehicle struct {
	LicenseNumber string
	VehicleType   VehicleType
	Cost          float64
}

type VehicleInterface interface {
	GetLicenseNumber() string
	GetVehicleType() VehicleType
	GetHourlyRate() float64
}
