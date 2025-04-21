package main

import (
	"fmt"
	"sort"
)

type Process struct {
	ID             int
	ArrivalTime    int
	BurstTime      int
	RemainingTime  int
	CompletionTime int
	TurnaroundTime int
	WaitingTime    int
}

type Execution struct {
	ProcessID int
	StartTime int
	EndTime   int
}

func processInputData() []Process {
	var n int
	fmt.Print("Enter the number of processes: ")
	fmt.Scan(&n)

	processes := make([]Process, n)
	for i := 0; i < n; i++ {
		fmt.Printf("Enter arrival and burst time for process P%d: ", i+1)
		fmt.Scan(&processes[i].ArrivalTime, &processes[i].BurstTime)
		processes[i].ID = i + 1
		processes[i].RemainingTime = processes[i].BurstTime
	}
	return processes
}

func printProcessData(processes []Process) {
	fmt.Println("PID\tAT\tBT\tCT\tTAT\tWT")
	for _, p := range processes {
		fmt.Printf(
			"P%d\t%d\t%d\t%d\t%d\t%d\n",
			p.ID,
			p.ArrivalTime,
			p.BurstTime,
			p.CompletionTime,
			p.TurnaroundTime,
			p.WaitingTime,
		)
	}
}

func ganttChart(exec []Execution) {
	fmt.Println("\nGantt Chart:")
	for _, e := range exec {
		fmt.Printf("|  P%d  ", e.ProcessID)
	}
	fmt.Println("|")

	fmt.Print(exec[0].StartTime)
	for _, e := range exec {
		fmt.Printf("     %d", e.EndTime)
	}
	fmt.Println("\n")
}

func FCFS(orig []Process) {
	fmt.Println("=== FCFS ===")
	processes := clone(orig)
	sort.Slice(processes, func(i, j int) bool {
		return processes[i].ArrivalTime < processes[j].ArrivalTime
	})

	time := 0
	exec := []Execution{}
	for i := range processes {
		if time < processes[i].ArrivalTime {
			time = processes[i].ArrivalTime
		}
		start := time
		time += processes[i].BurstTime
		processes[i].CompletionTime = time
		processes[i].TurnaroundTime = time - processes[i].ArrivalTime
		processes[i].WaitingTime = processes[i].TurnaroundTime - processes[i].BurstTime
		exec = append(exec, Execution{ProcessID: processes[i].ID, StartTime: start, EndTime: time})
	}
	printProcessData(processes)
	ganttChart(exec)
}

func SJF(orig []Process) {
	fmt.Println("=== SJF (Non-Preemptive) ===")
	processes := clone(orig)
	n := len(processes)
	done := 0
	time := 0
	visited := make([]bool, n)
	exec := []Execution{}

	for done < n {
		idx := -1
		for i := range processes {
			if !visited[i] && processes[i].ArrivalTime <= time {
				if idx == -1 || processes[i].BurstTime < processes[idx].BurstTime {
					idx = i
				}
			}
		}
		if idx == -1 {
			time++
			continue
		}
		start := time
		time += processes[idx].BurstTime
		processes[idx].CompletionTime = time
		processes[idx].TurnaroundTime = time - processes[idx].ArrivalTime
		processes[idx].WaitingTime = processes[idx].TurnaroundTime - processes[idx].BurstTime
		visited[idx] = true
		done++
		exec = append(
			exec,
			Execution{ProcessID: processes[idx].ID, StartTime: start, EndTime: time},
		)
	}
	printProcessData(processes)
	ganttChart(exec)
}

// SRTF Preemptive
func SRTF(orig []Process) {
	fmt.Println("=== SRTF (Preemptive SJF) ===")
	processes := clone(orig)
	n := len(processes)
	time := 0
	completed := 0
	exec := []Execution{}
	lastID := -1
	startTime := 0

	for completed < n {
		idx := -1
		for i := 0; i < n; i++ {
			if processes[i].ArrivalTime <= time && processes[i].RemainingTime > 0 {
				if idx == -1 || processes[i].RemainingTime < processes[idx].RemainingTime {
					idx = i
				}
			}
		}
		if idx == -1 {
			time++
			continue
		}

		if lastID != processes[idx].ID {
			if lastID != -1 {
				exec = append(
					exec,
					Execution{ProcessID: lastID, StartTime: startTime, EndTime: time},
				)
			}
			startTime = time
			lastID = processes[idx].ID
		}

		processes[idx].RemainingTime--
		time++

		if processes[idx].RemainingTime == 0 {
			completed++
			processes[idx].CompletionTime = time
			processes[idx].TurnaroundTime = time - processes[idx].ArrivalTime
			processes[idx].WaitingTime = processes[idx].TurnaroundTime - processes[idx].BurstTime
		}
	}
	exec = append(exec, Execution{ProcessID: lastID, StartTime: startTime, EndTime: time})

	printProcessData(processes)
	ganttChart(exec)
}

// Round Robin
func RR(orig []Process, quantum int) {
	fmt.Println("=== Round Robin ===")
	processes := clone(orig)
	n := len(processes)
	queue := []int{}
	inQueue := make([]bool, n)
	time := 0
	exec := []Execution{}
	completed := 0

	for {
		for i := 0; i < n; i++ {
			if processes[i].ArrivalTime <= time && !inQueue[i] && processes[i].RemainingTime > 0 {
				queue = append(queue, i)
				inQueue[i] = true
			}
		}

		if len(queue) == 0 {
			if completed == n {
				break
			}
			time++
			continue
		}

		i := queue[0]
		queue = queue[1:]

		start := time
		d := min(quantum, processes[i].RemainingTime)
		time += d
		processes[i].RemainingTime -= d

		exec = append(exec, Execution{ProcessID: processes[i].ID, StartTime: start, EndTime: time})

		for j := 0; j < n; j++ {
			if processes[j].ArrivalTime <= time && !inQueue[j] && processes[j].RemainingTime > 0 {
				queue = append(queue, j)
				inQueue[j] = true
			}
		}

		if processes[i].RemainingTime > 0 {
			queue = append(queue, i)
		} else {
			completed++
			processes[i].CompletionTime = time
			processes[i].TurnaroundTime = time - processes[i].ArrivalTime
			processes[i].WaitingTime = processes[i].TurnaroundTime - processes[i].BurstTime
		}
	}
	printProcessData(processes)
	ganttChart(exec)
}

// Helpers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func clone(orig []Process) []Process {
	dup := make([]Process, len(orig))
	for i, p := range orig {
		dup[i] = p
		dup[i].RemainingTime = p.BurstTime
	}
	return dup
}

func main() {
	processes := processInputData()

	FCFS(processes)
	SJF(processes)
	SRTF(processes)

	var quantum int
	fmt.Print("Enter time quantum for Round Robin: ")
	fmt.Scan(&quantum)
	RR(processes, quantum)
}
