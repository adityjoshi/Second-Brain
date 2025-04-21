package main

import (
	"fmt"
	"math"
	"sort"
)

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func inputInt(message string) int {
	var val int
	fmt.Print(message)
	fmt.Scan(&val)
	return val
}

func DiskFCFS(requests []int, head int) {
	fmt.Println("\n=== FCFS ===")
	total := 0
	cur := head
	for _, req := range requests {
		fmt.Printf("Move from %d to %d\n", cur, req)
		total += abs(req - cur)
		cur = req
	}
	fmt.Printf("Total head movement: %d\n", total)
}

func SSTF(requests []int, head int) {
	fmt.Println("\n=== SSTF ===")
	visited := make([]bool, len(requests))
	total := 0
	cur := head

	for i := 0; i < len(requests); i++ {
		minDist := math.MaxInt32
		index := -1
		for j, r := range requests {
			if !visited[j] && abs(cur-r) < minDist {
				minDist = abs(cur - r)
				index = j
			}
		}
		visited[index] = true
		fmt.Printf("Move from %d to %d\n", cur, requests[index])
		total += abs(cur - requests[index])
		cur = requests[index]
	}
	fmt.Printf("Total head movement: %d\n", total)
}

func SCAN(requests []int, head, diskSize int, direction string) {
	fmt.Println("\n=== SCAN ===")
	reqs := append(requests[:], head)
	sort.Ints(reqs)

	pos := sort.SearchInts(reqs, head)
	total := 0
	cur := head

	if direction == "left" {
		for i := pos; i >= 0; i-- {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
		if cur != 0 {
			fmt.Printf("Move from %d to 0\n", cur)
			total += cur
			cur = 0
		}
		for i := pos + 1; i < len(reqs); i++ {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
	} else {
		for i := pos; i < len(reqs); i++ {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
		if cur != diskSize-1 
			fmt.Printf("Move from %d to %d\n", cur, diskSize-1)
			total += diskSize - 1 - cur
			cur = diskSize - 1
		}
		for i := pos - 1; i >= 0; i-- {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
	}
	fmt.Printf("Total head movement: %d\n", total)
}

func LOOK(requests []int, head int, direction string) {
	fmt.Println("\n=== LOOK ===")
	reqs := append(requests[:], head)
	sort.Ints(reqs)

	pos := sort.SearchInts(reqs, head)
	total := 0
	cur := head

	if direction == "left" {
		for i := pos; i >= 0; i-- {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
		for i := pos + 1; i < len(reqs); i++ {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
	} else {
		for i := pos; i < len(reqs); i++ {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
		for i := pos - 1; i >= 0; i-- {
			fmt.Printf("Move from %d to %d\n", cur, reqs[i])
			total += abs(cur - reqs[i])
			cur = reqs[i]
		}
	}
	fmt.Printf("Total head movement: %d\n", total)
}

func CSCAN(requests []int, head, diskSize int) {
	fmt.Println("\n=== C-SCAN ===")
	reqs := append(requests[:], head)
	sort.Ints(reqs)

	pos := sort.SearchInts(reqs, head)
	total := 0
	cur := head

	for i := pos; i < len(reqs); i++ {
		fmt.Printf("Move from %d to %d\n", cur, reqs[i])
		total += abs(cur - reqs[i])
		cur = reqs[i]
	}
	if cur != diskSize-1 {
		fmt.Printf("Move from %d to %d\n", cur, diskSize-1)
		total += diskSize - 1 - cur
		cur = diskSize - 1
	}
	fmt.Printf("Jump from %d to 0\n", cur)
	total += diskSize - 1
	cur = 0
	for i := 0; i < pos; i++ {
		fmt.Printf("Move from %d to %d\n", cur, reqs[i])
		total += abs(cur - reqs[i])
		cur = reqs[i]
	}
	fmt.Printf("Total head movement: %d\n", total)
}

func main() {
	n := inputInt("Enter number of disk requests: ")
	requests := make([]int, n)
	for i := 0; i < n; i++ {
		requests[i] = inputInt(fmt.Sprintf("Enter request %d: ", i+1))
	}
	head := inputInt("Enter initial head position: ")
	diskSize := inputInt("Enter disk size: ")
	var direction string
	fmt.Print("Enter direction (left/right) for SCAN & LOOK: ")
	fmt.Scan(&direction)

	DiskFCFS(requests, head)
	SSTF(requests, head)
	SCAN(requests, head, diskSize, direction)
	LOOK(requests, head, direction)
	CSCAN(requests, head, diskSize)
}
