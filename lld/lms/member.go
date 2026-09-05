package main

type Member struct {
	ID              int
	Name            string
	ContactInfo     string
	CurrentBorrowed []*BookItem
	BorrowHistory   []*BookItem
}

func NewMember(id int, name, contactInfo string) *Member {
	return &Member{ID: id, Name: name, ContactInfo: contactInfo, CurrentBorrowed: make([]*BookItem, 0), BorrowHistory: make([]*BookItem, 0)}
}

func (m *Member) IsQuotaFull() bool {
	return len(m.CurrentBorrowed) >= 3
}

func (m *Member) AddBorrowedBook(bi *BookItem) {
	m.CurrentBorrowed = append(m.CurrentBorrowed, bi)
}
