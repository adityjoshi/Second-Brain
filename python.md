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
