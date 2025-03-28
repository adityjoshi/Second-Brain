# Define an array 
- from array import *
arr = array('i',[12,13,14,15])

/* print an array */

for i in range(0,len(arr)):
   print(arr[i])

/* reverse an array */

for i in range(len(arr)-1,-1,-1):
  print(arr[i])

/* sort an array */

print(sorted(arr))

/* delete an element from an array */

arr.remove(3)
print(arr)


/* search in an array*/

print(arr.index(40))


/* reverse an array list */

print(arr[::-1]) or arr.reverse()


### reversing a numpy arr
 

```
import numpy as np 


# /* flipping an array*/
arr = np.array([1,2,3,4,5])
print(np.flip(arr))

# same as the flip one 
print(np.flipud(arr))

# simple slicing 
print(arr[::-1])


# count the elements in an array 
arr = [20,30,40,2,4,5,6,6,1,22,2,20,20,20,30,30]
print(max(arr))
print(arr.count(20))



def find_max(arr):
  return max(arr)
arr = set([30,20,10,22,44,69])
print("find max in a set \n")
print(find_max(arr))



arr = [20,30,40,2,4,5,6,6,1,22,2,20,20,20,30,30]
max = arr[0]
for i in range(0,len(arr)):
  if (arr[i] > max):
    max = arr[i]

print("max in an arr",max)

res = []
for i in range(0,len(arr)):
  if i not in res:
    res.append(i)

print("result arr", res)
```

```
import numpy as np

# array split is nothing but in how many steps u want to split the array and print the array
arr = np.array([1, 2, 3, 4, 5, 6])

newarr = np.array_split(arr, 1)

print(newarr)


```

```python

prime number 

def num(n):
  if n<2:
    return False
  for i in range(2,n):
    if n % i == 0:
      return False
  return True 

def primes(m,n):
  primeList = []
  for i in range(m,n+1):
    if num(i):
      primeList.append(i) 
  return primeList

print(primes(5,500))


```
