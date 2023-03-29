
set UFM=Dayboro_WTP_2009_0p6.ufm
rem set UFM=Dayboro_WTP_2014_0p5.ufm
set local_folder=%~dp0
set PYEXEC=C:\Users\richa\anaconda3\python.exe
set PYFILE=C:\Python_projects\Tree_Hydraulics\Hydraulics.py


:: run the hydraulics
call C:\Users\richa\anaconda3\condabin\conda activate base
%PYEXEC% %PYFILE% %UFM% %local_folder%

pause