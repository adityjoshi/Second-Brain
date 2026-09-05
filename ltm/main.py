
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db

from schemas import (
    DepotCreate,
    DepotOut,
    DepotWithVehicles,
    VehicleCreate,
    VehicleOut,
)

Base.metadata.create_all(bind=engine)


app = FastAPI()


@app.post("/depots", response_model=DepotOut, status_code=201)
def create_depot(depot: DepotCreate, db: Session = Depends(get_db)) -> DepotOut:
    db_depot = models.Depot(
        name=depot.name,
        region=depot.region
    )
    db.add(db_depot)
    db.commit()
    db.refresh(db_depot)

    return db_depot


@app.post("/depots/{depot_id}/vehicles", response_model=VehicleOut, status_code=201)
def add_vehicle(depot_id: int, vehicle: VehicleCreate, db: Session = Depends(get_db)) -> VehicleOut:
    depot = (
        db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    )
    if depot is None:
        raise HTTPException(
            status_code=404,
            detail=f"No depot found with id {depot_id}"
        )

    db_vehicle = models.Vehicle(
        plate_number=vehicle.plate_number,
        vehicle_type=vehicle.vehicle_type,
        mileage=vehicle.mileage,
        depot_id=depot_id,
    )

    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@app.get("/depots/{depot_id}", response_model=DepotWithVehicles, status_code=200)
def get_depot(
    depot_id: int,
    vehicle_type: Optional[str] = None,
    sort: Optional[Literal["plate_number", "mileage"]] = Query(None),
    db: Session = Depends(get_db),
) -> DepotWithVehicles:
    depot = (
        db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    )
    if depot is None:
        raise HTTPException(
            status_code=404,
            detail=f"No depot found with id {depot_id}"
        )
    vehicle_q = (
        db.query(models.Vehicle).filter(models.Vehicle.depot_id == depot_id)
    )

    if vehicle_q is None:
        raise HTTPException(
            status_code=404,
            detail="No depot found with id"
        )

    if vehicle_type is not None:
        vehicle_q = vehicle_q.filter(models.Vehicle.vehicle_type == vehicle_type)
    if sort == "plate_number":
        vehicle_q = vehicle_q.order_by(models.Vehicle.plate_number.asc())
    if sort == "mileage":
        vehicle_q = vehicle_q.order_by(models.Vehicle.mileage.asc())

    vehicles = vehicle_q.all()

   
    return DepotWithVehicles(
        id=depot.id,
        name=depot.name,
        region=depot.region,
        vehicles=vehicles,
    )


@app.put("/depots/{depot_id}/vehicles/{vehicle_id}", response_model=VehicleOut, status_code=200)
def update_vehicle(
    depot_id: int,
    vehicle_id: int,
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
) -> VehicleOut:
    depot = (
        db.query(models.Depot).filter(models.Depot.id == depot_id).first()
    )
    if depot is None:
        raise HTTPException(
            status_code=404,
            detail=f"No depot found with id {depot_id}"
        )

    db_vehicle = (
        db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    )
    if db_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail=f"No vehicle found with id {vehicle_id}"
        )

    if db_vehicle.depot_id != depot_id:
        raise HTTPException(
            status_code=404,
            detail="this vehicle is not associated with the provided depot id"
        )

    db_vehicle.plate_number = vehicle.plate_number
    db_vehicle.vehicle_type = vehicle.vehicle_type
    db_vehicle.mileage = vehicle.mileage

    db.commit()
    db.refresh(db_vehicle)

    return db_vehicle



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        app,

        host="127.0.0.1",

        port=8000,

    )
