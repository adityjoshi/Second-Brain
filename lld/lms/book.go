package main

import "sync"

type Book struct {
	ID            int
	BookItem      []BookItem
	Title         string
	Author        string
	PublishedYear string
	mu            sync.RWMutex
}

func NewBook(id int, title, author, publishedYear string) *Book {
	bookCopies := &Book{ID: id, Title: title, Author: author, PublishedYear: publishedYear, BookItem: make([]BookItem, 0)}
	for i := 1; i <= 10; i++ {
		bookCopies.BookItem = append(bookCopies.BookItem, *NewBookItem(i, id))
	}
	return bookCopies
}
