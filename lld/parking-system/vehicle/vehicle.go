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

func (v *Vehicle) GetLicenseNumber() string {
	return v.LicenseNumber
}

func (v *Vehicle) GetVehicleType() string {
	return string(v.VehicleType)
}

func (v *Vehicle) GetHourlyRate() float64 {
	return v.Cost
}

func NewVehicle(licenseNumber string, vehicleType VehicleType) *Vehicle {
	cost := vehicleCost[vehicleType]
	return &Vehicle{LicenseNumber: licenseNumber, VehicleType: vehicleType, Cost: cost}
}

type Car struct {
	Vehicle
}

func NewCar(license string) *Car {
	return &Car{*NewVehicle(license, CarType)}
}

type Van struct {
	Vehicle
}

func NewVan(license string) *Van {
	return &Van{*NewVehicle(license, VanType)}
}

type Truck struct {
	Vehicle
}

func NewTruck(license string) *Truck {
	return &Truck{*NewVehicle(license, TruckType)}
}
