package cache

import (
	"container/list"
	"sync"
)

type Cache[T comparable, U any] struct {
	mtx        sync.RWMutex
	capacity   int
	storage    map[T]*list.Element
	ep         eviction.EvictionPolicy
	expireTime int
}

func NewCache[T comparable, U any](capacity, expireTime int, ep eviction.EvictionPolicy) *Cache[T, U] {
	cache := &Cache[T, U]{
		capacity:   capacity,
		expireTime: expireTime,
		ep:         ep,
		storage:    make(map[T]*list.Element),
	}
	go cache.expire()
	return cache

}
