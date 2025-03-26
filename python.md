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

