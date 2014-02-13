% Process Wardriving Results for Whitespace Towers
% Wardrive performed on Tuesday, Feb 7, 2012
% Ryan E. Guerra (me@ryaneguerra.com)
%
% Rate: 1 Mbps DSSS
% Antennas: 6 dBi 60 deg log-periodic on tower, 0 dBi fractal hat on car
% Tx Pwr: ~28 dBm into feeder at base of tower
% Velocity: around 

 clear all;
 close all;
format compact;

client_file = 'tower_10_simple.csv';
tower_file = 'tower_1_simple.csv';

% the location of the TFA tower, client
tow_loc = [-95.278976, 29.707332];
cli_loc = [-95.291951, 29.704480];

% Import the file
newData1 = importdata(client_file);
vars = fieldnames(newData1);
for i = 1:length(vars)
    assignin('base', vars{i}, newData1.(vars{i}));
end

cli_data = data;

% Import the file
newData1 = importdata(tower_file);
vars = fieldnames(newData1);
for i = 1:length(vars)
    assignin('base', vars{i}, newData1.(vars{i}));
end

tow_data = data;

% put the gps/rssi data into nice vectors
tow_lnlt = tow_data(:,1:2);
tow_rssi = tow_data(:,3);
tow_num = length(tow_rssi);
cli_lnlt = cli_data(:,1:2);
cli_rssi = cli_data(:,3);
cli_num = length(cli_rssi);

% the distance calculation package requires comparisons of equal vectors.
tow_loc = repmat(tow_loc, tow_num, 1);
tow_dist = DistGPS(tow_lnlt, tow_loc);
cli_loc = repmat(cli_loc, cli_num, 1);
cli_dist = DistGPS(cli_lnlt, cli_loc);

%% Fitting Functions
if (0)
    % SSE Fitting using myfit.m
    Starting=[1, 1, 1];
    options=optimset('Display','iter');
    
    tow_coeff=fminsearch(@myfit,Starting,options,tow_dist,tow_rssi)
    tow_fit = @(d) tow_coeff(1)+tow_coeff(2)*exp(-tow_coeff(3)*d);

    Starting=[1, 1, 1];
    
    cli_coeff=fminsearch(@myfit,Starting,options,cli_dist,cli_rssi)
    cli_fit = @(d) cli_coeff(1)+cli_coeff(2)*exp(-cli_coeff(3)*d);
end

if (0)
    % LSQNONLIN using cal_diff.m
    Init = [1 1 1];
    options = optimset('Largescale','off');
    
    tow_coeff = lsqnonlin(@calc_diff, Init, [], [], options, tow_dist, tow_rssi)
    tow_fit = @(d) tow_coeff(1)+tow_coeff(2)*exp(-tow_coeff(3)*d);
    
    Init = [1 1 1];
    
    cli_coeff = lsqnonlin(@calc_diff, Init, [], [], options, cli_dist, cli_rssi)
    cli_fit = @(d) cli_coeff(1) + cli_coeff(2)*exp(-cli_coeff(3)*d);
end

%% Plotting!
d_min = 0;
d_max = 2000;
rssi_min = -90;
rssi_max = -20;

d = d_min:1:d_max;
% Estimation base on MATLAB optimization program
% tow_est = tow_fit(d);
%cli_est = cli_fit(d);

% Estimation based on cheap Excel curve-fitting
% RSSI = -12.38*ln(x) + 1.6995
tow_est = @(d) (-12.38*log(d) + 1.6995)
cli_est = @(d) -12.84*log(d) - 5.9409

%Curve Fit
a =      -70.61;
b =   7.814e-05;
c =       52.38;
d =    -0.00781;
x=tow_dist;
yaxf=a*exp(b*x)+c*exp(d*x);


% line_marker='--r';

% Atheros Qualcomm AR5008 Typical Values
% CCK_1Mbps_line = @(d) -98
% CCK_11Mbps_line = @(d) -92
% OFDM_6Mbps_line = @(d) -95
% OFDM_54Mbps_line = @(d) -81

% Atheros Qualcomm AR5008 Minumum Values
% OFDM_54Mbps_line = @(d) -65
% CCK_11Mbps_line = @(d) -76
% CCK_1Mbps_line = @(d) -80
% OFDM_6Mbps_line = @(d) -82

% F-20 Pro DBii rated values
% CCK_1Mbps_line = @(d) -97
% CCK_11Mbps_line = @(d) rssi_min
% OFDM_6Mbps_line = @(d) -94
% OFDM_36Mbps_line = @(d) -83
% OFDM_48Mbps_line = @(d) -77
% OFDM_54Mbps_line = @(d) -74

% F-20 Pro DBii rated values
%  CCK_1Mbps_line = @(d) -97
%  CCK_11Mbps_line = @(d) rssi_min
% OFDM_6Mbps_line = @(d) -81
%  OFDM_36Mbps_line = @(d) -83
%  OFDM_48Mbps_line = @(d) -77
% OFDM_54Mbps_line = @(d) -65

% RSSI offset to adjust for expected parameters
offset = 6;

hand=figure;
% subplot(2,1,1)
    hold on
%     if (CCK_11Mbps_line(20) > rssi_min)
%         fplot(OFDM_54Mbps_line, [d_min, d_max], '--r')
%         fplot(CCK_11Mbps_line, [d_min, d_max], '--g')
%         fplot(CCK_1Mbps_line, [d_min, d_max], '--m')
%         fplot(OFDM_6Mbps_line, [d_min, d_max], '--b')
%     else
%         fplot(OFDM_54Mbps_line, [d_min, d_max], '--r')
%         fplot(OFDM_48Mbps_line, [d_min, d_max], '--g')
%         fplot(OFDM_36Mbps_line, [d_min, d_max], '--m')
%         fplot(OFDM_6Mbps_line, [d_min, d_max], '--c')
%         fplot(CCK_1Mbps_line, [d_min, d_max], '--b')
%     end
    yax=tow_rssi + offset;
    plot(tow_dist, yax, '.b', 'MarkerSize', 10) %points
    plot(tow_dist,yaxf,'r','LineWidth', 2);
%     plot(d, tow_est(d)+offset, '--r', 'LineWidth', 2) % curve fit
    plot([d_min d_max],[-65 -65],'--k','LineWidth', 2) %54MBps
    plot([d_min d_max],[-81 -81],'--k','LineWidth', 2) %6Mbps
    axis([d_min, d_max, rssi_min, rssi_max])
    title_str = ['RSSI from TFA Tower (ht=20m, hr=2m, Gtx= 6dbi, Grx=' int2str(offset) 'dBi, Ptx= 25dBm = 0.32W)' ]
    title(title_str, 'FontSize', 16,'FontName', 'Helvetica')
    xlabel('Distance from AP (m)')
    ylabel('RSSI (dBm)')
    legend('Wardrive','Curve Fit')
%     if (CCK_11Mbps_line(20) > rssi_min)
%         legend('Location', 'NorthEast', 'OFMD 54 Mbps', 'CCK 11 Mbps', 'OFDM 6 Mbps', 'CCK 1 Mbps')
%     else
%         legend('Location', 'NorthEast', 'OFMD 54 Mbps', 'OFDM 48 Mbps', 'OFDM 36 Mbps', 'OFDM 6 Mbps', 'CCK 1 Mbps')
%     end
    grid on
    
%    mySaveAs(hand,'tfaWardrive',6,5)  

% subplot(2,1,2)
%     hold on
%     if (CCK_11Mbps_line(20) > rssi_min)
%         fplot(OFDM_54Mbps_line, [d_min, d_max], '--r')
%         fplot(CCK_11Mbps_line, [d_min, d_max], '--g')
%         fplot(CCK_1Mbps_line, [d_min, d_max], '--m')
%         fplot(OFDM_6Mbps_line, [d_min, d_max], '--b')
%     else
%         fplot(OFDM_54Mbps_line, [d_min, d_max], '--r')
%         fplot(OFDM_48Mbps_line, [d_min, d_max], '--g')
%         fplot(OFDM_36Mbps_line, [d_min, d_max], '--m')
%         fplot(OFDM_6Mbps_line, [d_min, d_max], '--c')
%         fplot(CCK_1Mbps_line, [d_min, d_max], '--b')
%     end
%     
%     plot(cli_dist, cli_rssi + offset, '.k', 'MarkerSize', 10)
%     plot(d, cli_est(d), '--k', 'LineWidth', 2)
%     axis([d_min, d_max, rssi_min, rssi_max])
%     title_str = ['RSSI from Quince Client (3m, ' int2str(offset) ' dBi, 27 dBm Tx, 10 MPH)' ]
%     title(title_str, 'FontSize', 14)
%     xlabel('Distance (m)')
%     ylabel('RSSI (dBm)')
%     if (CCK_11Mbps_line(20) > rssi_min)
%         legend('Location', 'NorthEast', 'OFMD 54 Mbps', 'CCK 11 Mbps', 'OFDM 6 Mbps', 'CCK 1 Mbps')
%     else
%         legend('Location', 'NorthEast', 'OFMD 54 Mbps', 'OFDM 48 Mbps', 'OFDM 36 Mbps', 'OFDM 6 Mbps', 'CCK 1 Mbps')
%     end
%     grid on