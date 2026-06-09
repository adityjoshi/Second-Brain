package main

type Directions string

const (
	UP    Directions = "UP"
	STILL Directions = "STILL"
	DOWN  Directions = "DOWN"
)

type HallPanel struct {
	PanelID              int
	DirectionInstruction Directions
	SourceFloor          int
}

func NewHallPanel(panelID, sourceFloor int) *HallPanel {
	return &HallPanel{PanelID: panelID, DirectionInstruction: STILL, SourceFloor: sourceFloor}
}

func (hp *HallPanel) SetDirectionsInstruction(dir Directions) {
	hp.DirectionInstruction = dir
}
