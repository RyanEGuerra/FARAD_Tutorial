%The purpose of this program is to calculate distance between two decimal 
%GPS coordinates matrices. The model used in this calculation utilizes 
%Carlson (1999) model. 
% ======Example======
% Import the sample_data.xls file, creating vectors from each column 
% using column names. 
% or you can enter your own GPS data into lat1,long1,lat2 and long2
% variables
% run this m-file.
% ==============================================================

% The output of this program is 
% 1- Calculated distance between Point1(long1(i),lat1(i)) 
% and point2(long2(i),lat2(i)) shwon as distance_m (metric system) 
% and distance_ft (US system)
% 2- Plot of long1 vs lat1
% 3- Plot of long2 vs. lat2
% 4- Plot of distance_m vs. # points

%++++++++++++++++++++++++++++++++++
%   Nov.11.2008, Ramin Shamshiri  +
%   ramin.sh@ufl.edu              +
%   Dept of Ag & Bio Eng          +
%   University of Florida         +
%   Gainesville, Florida          +
%   www.Raminworld.com            +
%++++++++++++++++++++++++++++++++++

%=======================Program Begin========================== 
clc;  
display('....................Distance Matrix .......................');   
format long         % Switch to long format decimal display


[rows,cols]=size(lat1); % Gets number of data points ans store in rows
[rows2,cols]=size(long2); % Gets number of data points ans store in rows2

% Make sure all the matrices have same number of rows

if (rows==rows2)
    
    % Initialize vectors and set all cells to zeros
    angle1 = zeros(rows,1); 
    angle2 = zeros(rows,1);
    r1 = zeros(rows,1); 
    r2 = zeros(rows,1);
    xy1= zeros(rows,1); 
    xy2= zeros(rows,1);
    xy3= zeros(rows,1); 
    xy4= zeros(rows,1);
    X= zeros(rows,1); 
    Y= zeros(rows,1);
    distance_m=zeros(rows,1); 
    distance_ft=zeros(rows,1);

    maj_const=6378137;          %Major axis constant
    min_const=6356752.3142;     %Minor axis constant
    h=334.9;                    %Elevation
    
    for i=1:rows
        % True angle determination (atan=ArcTan)
        angle1(i,1)=(atan((min_const^2)/(maj_const^2)*tan(lat1(i,1)*pi()/180)))*180/pi();
        angle2(i,1)=(atan((min_const^2)/(maj_const^2)*tan(lat2(i,1)*pi()/180)))*180/pi();
   
        % Radius calculation for the two points
        r1(i,1)=(1/((cos(angle1(i,1)*pi()/180))^2/maj_const^2+(sin(angle1(i,1)*pi()/180))^2/min_const^2))^0.5+h;
        r2(i,1)=(1/((cos(angle2(i,1)*pi()/180))^2/maj_const^2+(sin(angle2(i,1)*pi()/180))^2/min_const^2))^0.5+h;
  
        % X-Y earth coordinates
        xy1(i,1)=r1(i,1)*cos(angle1(i,1)*pi()/180);
        xy2(i,1)=r2(i,1)*cos(angle2(i,1)*pi()/180);
        xy3(i,1)=r1(i,1)*sin(angle1(i,1)*pi()/180);
        xy4(i,1)=r2(i,1)*sin(angle2(i,1)*pi()/180);
   
        X(i,1)=((xy1(i,1)-xy2(i,1))^2+(xy3(i,1)-xy4(i,1))^2)^0.5;         % X coordinate
        Y(i,1)=2*pi()*((((xy1(i,1)+xy2(i,1))/2))/360)*(long1(i,1)-long2(i,1));     % Y coordinate

        format short                             % Switch to short format

        distance_m(i,1)=((X(i,1))^2+(Y(i,1))^2)^0.5;                    % Distance Meter
        distance_ft(i,1)= distance_m(i,1)*3.28084;                    % Distance feet

    end
else
    display('.........Lat1 and Lat2 rows are not equal...........');
end
display('.........Distance (m)...........')
distance_m
display('.........Distance (ft)...........')
distance_ft

 
%% Create plot
% figure
% plot1 = plot(...
%   long1,lat1,...
%   'LineStyle',':',...
%   'Marker','.',...
%   'DisplayName','lat1 vs long1','color','blue',...
%   'XDataSource','long1',...
%   'YDataSource','lat1'),grid;
% xlabel('long1')
% ylabel('lat1')
% 
% 
% figure
% plot2 = plot(...
%   long2,lat2,...
%   'LineStyle',':',...
%   'Marker','.',...
%   'DisplayName','lat2 vs long2','color','green',...
%   'XDataSource','long2',...
%   'YDataSource','lat2'),grid;
% xlabel('long2')
% ylabel('lat2')
% 
% 
% figure
% plot3 = plot(...
%   distance_m,...
%   'LineStyle',':',...
%   'Marker','.','color','red',...
%   'DisplayName','Distance',...
%   'YDataSource','distance_m'), grid;
% xlabel('t')
% ylabel('Distance(m)')
