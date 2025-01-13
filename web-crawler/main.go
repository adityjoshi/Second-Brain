package main

import "fmt"

func serialCrawler(url string, fetcher Fetcher, fetched map[string]bool) {
	if fetched[url] {
		return
	}
	fetched[url] = true
}

func main() {
	fmt.Print("hey this is a ")
}
