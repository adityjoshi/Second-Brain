package cache

import (
	"container/list"
	"sync"
)

type Cache[T comparable, U any] struct {
	mtx        sync.RWMutex
	capacity   int
	storage    map[T]*list.Element
	ep         EvictionPolicy
	expireTime int
}
