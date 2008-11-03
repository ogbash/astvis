program Fib
  implicit none

  integer :: e1, e2
  integer e3, e4

  e1 = Fibonacci(5)
  e2 = Fibonacci(10)
  e3 = Fibonacci(15)
  e4 = Fibonacci(0)

  print *, e1, e2, e3, e4

contains

  recursive function Fibonacci(n) result(r)
    integer, intent(in) :: n
    integer :: r

    if (n<0) stop "Fibonacci cannot be negative"

    if (n==0 .or. n==1) then
       r = 1
    else
       r = Fibonacci(n-1) + Fibonacci(n-2)
    end if
  end function Fibonacci
end program Fib
