package main

type ElevatorPanel struct {
	PanelID      int
	FloorButtons [N]bool
}

func NewElevatorPanel(panelID int) *ElevatorPanel {
	return &ElevatorPanel{PanelID: panelID, FloorButtons: [15]bool{}}
}
