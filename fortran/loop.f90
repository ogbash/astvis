program Loop
  implicit none
  
  integer n
  integer r

  n = 5
  r = Sum(n)

  print *, r

contains

  function Sum(n) result(s)
    integer, intent(in) :: n
    integer :: s, i

    s = 0
    do i=1,n
       if (i==1) then
          print *, i
       end if
       s = s+i
    end do

    i=0
    do while(i<n)
       s = s+i
    end do

  end function Sum
end program Loop
