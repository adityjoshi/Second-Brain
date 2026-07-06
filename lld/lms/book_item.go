package main

type Status string

const (
	Borrowed  Status = "Borrowed"
	Available Status = "Available"
)

type BookItem struct {
	ID     int
	BookId int
	Status string
}

func NewBookItem(id, bookID int) *BookItem {
	return &BookItem{ID: id, BookId: bookID, Status: string(Available)}
}

func (bi *BookItem) BorrowBack() {
	bi.Status = string(Borrowed)
}

func (bi *BookItem) ReturnBook() {
	bi.Status = string(Available)
}
